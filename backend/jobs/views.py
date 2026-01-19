"""
Views for Jobs API
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Min, Max

from jobs.models import JobPosting, JobCategory, JobSkill
from jobs.serializers import (
    JobPostingListSerializer, JobPostingDetailSerializer,
    JobCategorySerializer, JobSearchSerializer,
    JobMatchSerializer, JobStatisticsSerializer
)
from skills.models import UserSkill


class JobCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for job categories
    """
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """Get all jobs in this category"""
        category = self.get_object()
        
        # Get jobs in this category
        job_ids = category.job_posting_categories.values_list('job_posting_id', flat=True)
        jobs = JobPosting.objects.filter(
            id__in=job_ids,
            is_active=True,
            archived=False
        ).order_by('-published_at')
        
        # Paginate
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = JobPostingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = JobPostingListSerializer(jobs, many=True)
        return Response({
            'category': category.name,
            'count': jobs.count(),
            'jobs': serializer.data
        })


class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for job postings
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'company_name', 'description_text', 'location']
    filterset_fields = ['work_type', 'employment_type', 'location', 'is_active', 'premium']
    ordering_fields = ['published_at', 'salary_min', 'title', 'company_name']
    ordering = ['-published_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobPostingDetailSerializer
        return JobPostingListSerializer
    
    def get_queryset(self):
        """Get active, non-archived jobs"""
        queryset = JobPosting.objects.filter(
            is_active=True,
            archived=False
        ).select_related().prefetch_related('job_skills__skill')
        
        # Filter by salary range
        min_salary = self.request.query_params.get('min_salary')
        if min_salary:
            try:
                queryset = queryset.filter(salary_min__gte=float(min_salary))
            except ValueError:
                pass
        
        max_salary = self.request.query_params.get('max_salary')
        if max_salary:
            try:
                queryset = queryset.filter(salary_max__lte=float(max_salary))
            except ValueError:
                pass
        
        # Filter by fresh jobs (last 7 days)
        is_fresh = self.request.query_params.get('is_fresh')
        if is_fresh and is_fresh.lower() == 'true':
            from datetime import timedelta
            from django.utils import timezone
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(published_at__gte=week_ago)
        
        # Filter by skills
        skills = self.request.query_params.get('skills')
        if skills:
            try:
                skill_ids = [int(s) for s in skills.split(',')]
                queryset = queryset.filter(
                    job_skills__skill_id__in=skill_ids
                ).distinct()
            except ValueError:
                pass
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            try:
                queryset = queryset.filter(
                    job_posting_categories__category_id=int(category)
                ).distinct()
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def fresh(self, request):
        """Get fresh jobs (posted in last 7 days)"""
        from datetime import timedelta
        from django.utils import timezone
        
        week_ago = timezone.now() - timedelta(days=7)
        jobs = self.get_queryset().filter(published_at__gte=week_ago)
        
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def remote(self, request):
        """Get remote jobs"""
        jobs = self.get_queryset().filter(work_type='remote')
        
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
        """Get jobs recommended for the user based on their skills"""
        user = request.user
        
        # Get user's skills
        user_skill_ids = set(
            UserSkill.objects.filter(
                user=user,
                status='learned'
            ).values_list('skill_id', flat=True)
        )
        
        if not user_skill_ids:
            return Response({
                'message': 'No skills found in your profile. Please add some skills first.',
                'jobs': []
            })
        
        # Get jobs that require user's skills
        jobs = self.get_queryset().filter(
            job_skills__skill_id__in=user_skill_ids
        ).distinct()
        
        # Calculate match percentage for each job
        job_matches = []
        for job in jobs[:50]:  # Limit to 50 for performance
            required_skill_ids = set(
                job.job_skills.filter(is_required=True).values_list('skill_id', flat=True)
            )
            
            if not required_skill_ids:
                continue
            
            matching_skills = user_skill_ids & required_skill_ids
            match_percentage = (len(matching_skills) / len(required_skill_ids)) * 100
            
            if match_percentage >= 30:  # At least 30% match
                matching_skill_names = list(
                    job.job_skills.filter(
                        skill_id__in=matching_skills
                    ).values_list('skill__name', flat=True)
                )
                
                missing_skill_names = list(
                    job.job_skills.filter(
                        skill_id__in=(required_skill_ids - user_skill_ids)
                    ).values_list('skill__name', flat=True)
                )
                
                job_matches.append({
                    'job': job,
                    'match_percentage': match_percentage,
                    'matching_skills_count': len(matching_skills),
                    'total_required_skills': len(required_skill_ids),
                    'matching_skills': matching_skill_names,
                    'missing_skills': missing_skill_names
                })
        
        # Sort by match percentage
        job_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        serializer = JobMatchSerializer(job_matches[:20], many=True)  # Top 20
        return Response({
            'count': len(job_matches),
            'recommendations': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get job market statistics"""
        # Jobs by work type
        from datetime import timedelta
        from django.utils import timezone
        jobs = JobPosting.objects.filter(is_active=True, archived=False)
        
        # Total counts
        total_jobs = jobs.count()
        fresh_jobs = jobs.filter(
            published_at__gte=timezone.now() - timedelta(days=7)
        ).count() if jobs.exists() else 0
        
        
        jobs_by_work_type = {}
        for work_type, display in JobPosting.WORK_TYPE_CHOICES:
            count = jobs.filter(work_type=work_type).count()
            jobs_by_work_type[display] = count
        
        # Jobs by location (top 10)
        jobs_by_location = dict(
            jobs.values('location').annotate(
                count=Count('id')
            ).order_by('-count')[:10].values_list('location', 'count')
        )
        
        # Salary statistics
        salary_stats = jobs.exclude(salary_min__isnull=True).aggregate(
            avg_salary=Avg('salary_min'),
            min_salary=Min('salary_min'),
            max_salary=Max('salary_min')
        )
        
        jobs_with_salary = jobs.exclude(salary_min__isnull=True).count()
        
        # Top companies
        top_companies = list(
            jobs.values('company_name').annotate(
                job_count=Count('id')
            ).order_by('-job_count')[:10].values_list('company_name', 'job_count')
        )
        
        data = {
            'total_jobs': total_jobs,
            'active_jobs': total_jobs,
            'fresh_jobs': fresh_jobs,
            'jobs_by_work_type': jobs_by_work_type,
            'jobs_by_location': jobs_by_location,
            'average_salary': salary_stats['avg_salary'],
            'salary_range': {
                'min': salary_stats['min_salary'],
                'max': salary_stats['max_salary']
            },
            'top_companies': [
                {'name': name, 'count': count} for name, count in top_companies
            ],
            'jobs_with_salary': jobs_with_salary
        }
        
        serializer = JobStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Get similar jobs based on skills"""
        job = self.get_object()
        
        # Get skills from this job
        job_skill_ids = list(
            job.job_skills.values_list('skill_id', flat=True)
        )
        
        if not job_skill_ids:
            return Response({
                'message': 'No skills found for this job',
                'jobs': []
            })
        
        # Find jobs with similar skills
        similar_jobs = JobPosting.objects.filter(
            is_active=True,
            archived=False,
            job_skills__skill_id__in=job_skill_ids
        ).exclude(id=job.id).annotate(
            skill_match_count=Count('job_skills')
        ).order_by('-skill_match_count')[:10]
        
        serializer = JobPostingListSerializer(similar_jobs, many=True)
        return Response({
            'job_title': job.title,
            'similar_jobs_count': similar_jobs.count(),
            'similar_jobs': serializer.data
        })