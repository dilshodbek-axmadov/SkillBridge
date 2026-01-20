"""
Views for Analytics API - Comprehensive Dashboard for Career Decisions
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db.models import Count, Avg, Min, Max, Q, F, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict

from .models import MarketTrend, SkillCombination
from .serializers import (
    MarketTrendSerializer, SkillTrendHistorySerializer, TrendComparisonSerializer,
    TopSkillSerializer, SkillDemandByCategorySerializer,
    SalaryTrendSerializer, SalaryBySkillSerializer, SalaryByRoleSerializer,
    SalaryByLocationSerializer, SalaryByExperienceSerializer,
    SkillCombinationSerializer, SkillStackSerializer, RelatedSkillSerializer,
    JobMarketOverviewSerializer, JobsByWorkTypeSerializer, JobsByEmploymentTypeSerializer,
    CompanyInsightSerializer, DashboardSummarySerializer,
    CareerComparisonSerializer, SkillValueAnalysisSerializer
)
from skills.models import Skill
from jobs.models import JobPosting, JobSkill, JobCategory
from career.models import Role, RoleRequiredSkill


# ============== Market Trends ViewSet ==============

class MarketTrendViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for market trends analysis

    Endpoints:
    - GET /api/analytics/trends/ - List all market trends
    - GET /api/analytics/trends/{id}/ - Get trend details
    - GET /api/analytics/trends/by-skill/{skill_id}/ - Get trends for a skill
    - GET /api/analytics/trends/compare/ - Compare trends between skills
    - GET /api/analytics/trends/rising/ - Get rising skills
    - GET /api/analytics/trends/declining/ - Get declining skills
    - GET /api/analytics/trends/monthly-summary/ - Get monthly market summary
    """
    serializer_class = MarketTrendSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = MarketTrend.objects.select_related('skill').all()

        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=int(year))

        # Filter by month
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=int(month))

        # Filter by trend direction
        direction = self.request.query_params.get('direction')
        if direction:
            queryset = queryset.filter(trend_direction=direction)

        return queryset.order_by('-year', '-month', '-demand_count')

    @action(detail=False, methods=['get'], url_path='by-skill/(?P<skill_id>[^/.]+)')
    def by_skill(self, request, skill_id=None):
        """
        Get trend history for a specific skill

        GET /api/analytics/trends/by-skill/{skill_id}/
        """
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return Response(
                {'detail': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get last 12 months of trends
        trends = MarketTrend.objects.filter(
            skill=skill
        ).order_by('-year', '-month')[:12]

        # Calculate growth
        if trends.count() >= 2:
            latest = trends.first()
            oldest = trends.last()
            if oldest.demand_count > 0:
                growth = ((latest.demand_count - oldest.demand_count) / oldest.demand_count) * 100
            else:
                growth = 0
        else:
            growth = 0

        latest_trend = trends.first() if trends.exists() else None

        data = {
            'skill_id': skill.id,
            'skill_name': skill.name,
            'skill_category': skill.get_category_display(),
            'current_demand': latest_trend.demand_count if latest_trend else 0,
            'current_salary': latest_trend.average_salary if latest_trend else None,
            'trend_direction': latest_trend.trend_direction if latest_trend else 'stable',
            'growth_percentage': round(growth, 2),
            'history': MarketTrendSerializer(trends, many=True).data
        }

        serializer = SkillTrendHistorySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        Compare trends between multiple skills

        GET /api/analytics/trends/compare/?skills=1,2,3
        """
        skill_ids = request.query_params.get('skills', '')
        if not skill_ids:
            return Response(
                {'detail': 'Please provide skill IDs (e.g., ?skills=1,2,3)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        skill_ids = [int(x) for x in skill_ids.split(',') if x.isdigit()]
        skills = Skill.objects.filter(id__in=skill_ids)

        comparison_data = []
        highest_growth = {'skill_name': None, 'growth': -float('inf')}
        highest_demand = {'skill_name': None, 'demand': 0}

        for skill in skills:
            trends = MarketTrend.objects.filter(skill=skill).order_by('-year', '-month')[:12]
            latest = trends.first() if trends.exists() else None

            # Calculate growth
            if trends.count() >= 2:
                oldest = trends.last()
                if oldest.demand_count > 0:
                    growth = ((latest.demand_count - oldest.demand_count) / oldest.demand_count) * 100
                else:
                    growth = 0
            else:
                growth = 0

            skill_data = {
                'skill_id': skill.id,
                'skill_name': skill.name,
                'current_demand': latest.demand_count if latest else 0,
                'current_salary': str(latest.average_salary) if latest and latest.average_salary else None,
                'trend_direction': latest.trend_direction if latest else 'stable',
                'growth_percentage': round(growth, 2)
            }
            comparison_data.append(skill_data)

            if growth > highest_growth['growth']:
                highest_growth = {'skill_name': skill.name, 'growth': growth}
            if latest and latest.demand_count > highest_demand['demand']:
                highest_demand = {'skill_name': skill.name, 'demand': latest.demand_count}

        return Response({
            'skills': comparison_data,
            'period_start': '12 months ago',
            'period_end': 'Current',
            'highest_growth_skill': highest_growth,
            'highest_demand_skill': highest_demand
        })

    @action(detail=False, methods=['get'])
    def rising(self, request):
        """
        Get skills with rising demand

        GET /api/analytics/trends/rising/
        """
        limit = int(request.query_params.get('limit', 10))

        # Get latest month's rising trends
        latest_trends = MarketTrend.objects.filter(
            trend_direction='rising'
        ).order_by('-year', '-month', '-demand_count')[:limit]

        serializer = MarketTrendSerializer(latest_trends, many=True)
        return Response({
            'count': latest_trends.count(),
            'rising_skills': serializer.data
        })

    @action(detail=False, methods=['get'])
    def declining(self, request):
        """
        Get skills with declining demand

        GET /api/analytics/trends/declining/
        """
        limit = int(request.query_params.get('limit', 10))

        latest_trends = MarketTrend.objects.filter(
            trend_direction='declining'
        ).order_by('-year', '-month', '-demand_count')[:limit]

        serializer = MarketTrendSerializer(latest_trends, many=True)
        return Response({
            'count': latest_trends.count(),
            'declining_skills': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='monthly-summary')
    def monthly_summary(self, request):
        """
        Get monthly market summary

        GET /api/analytics/trends/monthly-summary/?year=2024&month=1
        """
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))

        trends = MarketTrend.objects.filter(year=year, month=month)

        rising_count = trends.filter(trend_direction='rising').count()
        stable_count = trends.filter(trend_direction='stable').count()
        declining_count = trends.filter(trend_direction='declining').count()

        total_demand = trends.aggregate(total=Sum('demand_count'))['total'] or 0
        avg_salary = trends.aggregate(avg=Avg('average_salary'))['avg']

        top_demanded = trends.order_by('-demand_count')[:10]
        top_salary = trends.filter(average_salary__isnull=False).order_by('-average_salary')[:10]

        return Response({
            'period': f'{year}/{month:02d}',
            'year': year,
            'month': month,
            'summary': {
                'total_skills_tracked': trends.count(),
                'rising_skills': rising_count,
                'stable_skills': stable_count,
                'declining_skills': declining_count,
                'total_job_demand': total_demand,
                'average_salary': str(avg_salary) if avg_salary else None
            },
            'top_demanded_skills': MarketTrendSerializer(top_demanded, many=True).data,
            'top_paying_skills': MarketTrendSerializer(top_salary, many=True).data
        })


# ============== Skill Demand ViewSet ==============

class SkillDemandViewSet(viewsets.ViewSet):
    """
    ViewSet for skill demand analysis

    Endpoints:
    - GET /api/analytics/skills/top/ - Get top skills by demand
    - GET /api/analytics/skills/by-category/ - Get skills grouped by category
    - GET /api/analytics/skills/{skill_id}/analysis/ - Get detailed skill analysis
    - GET /api/analytics/skills/emerging/ - Get emerging skills
    - GET /api/analytics/skills/stable-demand/ - Get skills with stable high demand
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def top(self, request):
        """
        Get top skills by job demand

        GET /api/analytics/skills/top/?limit=20&category=framework
        """
        limit = int(request.query_params.get('limit', 20))
        category = request.query_params.get('category')

        # Get skills with job counts
        skill_stats = JobSkill.objects.values(
            'skill_id',
            'skill__name',
            'skill__category',
            'skill__popularity_score'
        ).annotate(
            job_count=Count('job_posting', distinct=True),
            required_count=Count('id', filter=Q(is_required=True)),
            optional_count=Count('id', filter=Q(is_required=False))
        ).order_by('-job_count')

        if category:
            skill_stats = skill_stats.filter(skill__category=category)

        skill_stats = skill_stats[:limit]

        # Enrich with salary and trend data
        result = []
        for stat in skill_stats:
            # Get average salary
            jobs_with_skill = JobSkill.objects.filter(
                skill_id=stat['skill_id']
            ).values_list('job_posting_id', flat=True)

            salary_data = JobPosting.objects.filter(
                id__in=jobs_with_skill,
                salary_min__isnull=False
            ).aggregate(avg_salary=Avg('salary_min'))

            # Get trend direction
            latest_trend = MarketTrend.objects.filter(
                skill_id=stat['skill_id']
            ).order_by('-year', '-month').first()

            result.append({
                'skill_id': stat['skill_id'],
                'skill_name': stat['skill__name'],
                'category': stat['skill__category'],
                'category_display': dict(Skill.CATEGORY_CHOICES).get(stat['skill__category'], stat['skill__category']),
                'job_count': stat['job_count'],
                'required_count': stat['required_count'],
                'optional_count': stat['optional_count'],
                'average_salary': salary_data['avg_salary'],
                'popularity_score': stat['skill__popularity_score'],
                'trend_direction': latest_trend.trend_direction if latest_trend else None
            })

        serializer = TopSkillSerializer(result, many=True)
        return Response({
            'count': len(result),
            'skills': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-category')
    def by_category(self, request):
        """
        Get skill demand grouped by category

        GET /api/analytics/skills/by-category/
        """
        categories = []

        for category_code, category_name in Skill.CATEGORY_CHOICES:
            skills_in_category = Skill.objects.filter(category=category_code)
            skill_ids = skills_in_category.values_list('id', flat=True)

            # Get job stats
            job_stats = JobSkill.objects.filter(
                skill_id__in=skill_ids
            ).aggregate(
                total_jobs=Count('job_posting', distinct=True)
            )

            # Get top skills in category
            top_skills = JobSkill.objects.filter(
                skill_id__in=skill_ids
            ).values(
                'skill_id',
                'skill__name',
                'skill__category',
                'skill__popularity_score'
            ).annotate(
                job_count=Count('job_posting', distinct=True),
                required_count=Count('id', filter=Q(is_required=True)),
                optional_count=Count('id', filter=Q(is_required=False))
            ).order_by('-job_count')[:5]

            # Get average salary for category
            job_ids = JobSkill.objects.filter(
                skill_id__in=skill_ids
            ).values_list('job_posting_id', flat=True)

            salary_data = JobPosting.objects.filter(
                id__in=job_ids,
                salary_min__isnull=False
            ).aggregate(avg_salary=Avg('salary_min'))

            categories.append({
                'category': category_code,
                'category_display': category_name,
                'total_jobs': job_stats['total_jobs'] or 0,
                'skills_count': skills_in_category.count(),
                'top_skills': [
                    {
                        'skill_id': s['skill_id'],
                        'skill_name': s['skill__name'],
                        'category': s['skill__category'],
                        'category_display': category_name,
                        'job_count': s['job_count'],
                        'required_count': s['required_count'],
                        'optional_count': s['optional_count'],
                        'average_salary': None,
                        'popularity_score': s['skill__popularity_score'],
                        'trend_direction': None
                    }
                    for s in top_skills
                ],
                'average_salary': salary_data['avg_salary']
            })

        # Sort by total jobs
        categories.sort(key=lambda x: x['total_jobs'], reverse=True)

        serializer = SkillDemandByCategorySerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='(?P<skill_id>[^/.]+)/analysis')
    def analysis(self, request, skill_id=None):
        """
        Get detailed analysis for a specific skill

        GET /api/analytics/skills/{skill_id}/analysis/
        """
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return Response(
                {'detail': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Job count
        job_count = JobSkill.objects.filter(skill=skill).values('job_posting').distinct().count()

        # Salary impact
        jobs_with_skill = JobSkill.objects.filter(skill=skill).values_list('job_posting_id', flat=True)
        salary_with_skill = JobPosting.objects.filter(
            id__in=jobs_with_skill,
            salary_min__isnull=False
        ).aggregate(avg=Avg('salary_min'))['avg'] or 0

        overall_salary = JobPosting.objects.filter(
            salary_min__isnull=False
        ).aggregate(avg=Avg('salary_min'))['avg'] or 0

        salary_impact = salary_with_skill - overall_salary if overall_salary else 0

        # Trend
        latest_trend = MarketTrend.objects.filter(skill=skill).order_by('-year', '-month').first()
        trends = MarketTrend.objects.filter(skill=skill).order_by('-year', '-month')[:12]

        # Growth calculation
        if trends.count() >= 2:
            oldest = trends.last()
            if oldest.demand_count > 0:
                growth = ((trends.first().demand_count - oldest.demand_count) / oldest.demand_count) * 100
            else:
                growth = 0
        else:
            growth = 0

        # Related roles
        related_roles = Role.objects.filter(
            role_required_skills__skill=skill
        ).distinct()[:5]

        # Commonly paired skills
        combinations = SkillCombination.objects.filter(
            Q(skill_1=skill) | Q(skill_2=skill)
        ).order_by('-co_occurrence_count')[:10]

        paired_skills = []
        for combo in combinations:
            paired_skill = combo.skill_2 if combo.skill_1 == skill else combo.skill_1
            paired_skills.append(paired_skill)

        # Learning priority score (0-100)
        priority_score = (
            (job_count / 100 * 30) +  # Job demand weight
            (skill.popularity_score * 0.3) +  # Popularity weight
            (growth * 0.2 if growth > 0 else 0) +  # Growth weight
            (20 if latest_trend and latest_trend.trend_direction == 'rising' else 0)  # Trend weight
        )
        priority_score = min(priority_score, 100)

        # Recommendation
        if priority_score >= 80:
            recommendation = "Highly recommended - This skill is in high demand and growing rapidly."
        elif priority_score >= 60:
            recommendation = "Recommended - This skill has strong market demand."
        elif priority_score >= 40:
            recommendation = "Consider learning - This skill has moderate market demand."
        else:
            recommendation = "Optional - This skill has lower market demand currently."

        from skills.serializers import SkillSerializer
        from career.serializers import RoleListSerializer

        data = {
            'skill': SkillSerializer(skill).data,
            'current_job_count': job_count,
            'salary_impact': salary_impact,
            'demand_trend': latest_trend.trend_direction if latest_trend else 'stable',
            'growth_percentage': round(growth, 2),
            'related_roles': RoleListSerializer(related_roles, many=True).data,
            'commonly_paired_with': SkillSerializer(paired_skills, many=True).data,
            'learning_priority_score': round(priority_score, 2),
            'recommendation': recommendation
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def emerging(self, request):
        """
        Get emerging skills (new and rising)

        GET /api/analytics/skills/emerging/
        """
        limit = int(request.query_params.get('limit', 10))

        # Get skills with rising trends
        rising_trends = MarketTrend.objects.filter(
            trend_direction='rising'
        ).order_by('-year', '-month').values_list('skill_id', flat=True).distinct()[:limit * 2]

        # Get skill details
        skills = Skill.objects.filter(id__in=rising_trends)

        result = []
        for skill in skills[:limit]:
            job_count = JobSkill.objects.filter(skill=skill).count()
            result.append({
                'skill_id': skill.id,
                'skill_name': skill.name,
                'category': skill.category,
                'category_display': skill.get_category_display(),
                'job_count': job_count,
                'required_count': JobSkill.objects.filter(skill=skill, is_required=True).count(),
                'optional_count': JobSkill.objects.filter(skill=skill, is_required=False).count(),
                'average_salary': None,
                'popularity_score': skill.popularity_score,
                'trend_direction': 'rising'
            })

        return Response({
            'count': len(result),
            'emerging_skills': result
        })

    @action(detail=False, methods=['get'], url_path='stable-demand')
    def stable_demand(self, request):
        """
        Get skills with stable high demand

        GET /api/analytics/skills/stable-demand/
        """
        limit = int(request.query_params.get('limit', 10))

        # Get skills with stable trends and high demand
        stable_skills = MarketTrend.objects.filter(
            trend_direction='stable',
            demand_count__gte=10
        ).order_by('-demand_count').values_list('skill_id', flat=True).distinct()[:limit]

        skills = Skill.objects.filter(id__in=stable_skills)

        result = []
        for skill in skills:
            job_count = JobSkill.objects.filter(skill=skill).count()
            result.append({
                'skill_id': skill.id,
                'skill_name': skill.name,
                'category': skill.category,
                'category_display': skill.get_category_display(),
                'job_count': job_count,
                'required_count': JobSkill.objects.filter(skill=skill, is_required=True).count(),
                'optional_count': JobSkill.objects.filter(skill=skill, is_required=False).count(),
                'average_salary': None,
                'popularity_score': skill.popularity_score,
                'trend_direction': 'stable'
            })

        return Response({
            'count': len(result),
            'stable_skills': result
        })


# ============== Salary Analytics ViewSet ==============

class SalaryAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for salary analytics

    Endpoints:
    - GET /api/analytics/salary/trends/ - Get salary trends over time
    - GET /api/analytics/salary/by-skill/ - Get salary by skill
    - GET /api/analytics/salary/by-role/ - Get salary by role
    - GET /api/analytics/salary/by-location/ - Get salary by location
    - GET /api/analytics/salary/by-experience/ - Get salary by experience level
    - GET /api/analytics/salary/compare/ - Compare salaries between skills/roles
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Get salary trends over time

        GET /api/analytics/salary/trends/?months=12
        """
        months = int(request.query_params.get('months', 12))

        # Get salary trends by month
        salary_by_month = JobPosting.objects.filter(
            salary_min__isnull=False,
            published_at__gte=timezone.now() - timedelta(days=months * 30)
        ).annotate(
            month=TruncMonth('published_at')
        ).values('month').annotate(
            average_salary=Avg('salary_min'),
            min_salary=Min('salary_min'),
            max_salary=Max('salary_max'),
            job_count=Count('id')
        ).order_by('month')

        result = []
        for entry in salary_by_month:
            result.append({
                'period': entry['month'].strftime('%Y-%m') if entry['month'] else 'Unknown',
                'month': entry['month'].month if entry['month'] else 0,
                'year': entry['month'].year if entry['month'] else 0,
                'average_salary': entry['average_salary'],
                'min_salary': entry['min_salary'],
                'max_salary': entry['max_salary'] or entry['min_salary'],
                'job_count': entry['job_count']
            })

        serializer = SalaryTrendSerializer(result, many=True)
        return Response({
            'period_months': months,
            'trends': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-skill')
    def by_skill(self, request):
        """
        Get salary statistics by skill

        GET /api/analytics/salary/by-skill/?limit=20
        """
        limit = int(request.query_params.get('limit', 20))

        skills_salary = []

        # Get top skills
        top_skills = JobSkill.objects.values('skill_id', 'skill__name', 'skill__category').annotate(
            job_count=Count('job_posting', distinct=True)
        ).order_by('-job_count')[:limit]

        for skill_data in top_skills:
            job_ids = JobSkill.objects.filter(
                skill_id=skill_data['skill_id']
            ).values_list('job_posting_id', flat=True)

            salary_stats = JobPosting.objects.filter(
                id__in=job_ids,
                salary_min__isnull=False
            ).aggregate(
                average_salary=Avg('salary_min'),
                min_salary=Min('salary_min'),
                max_salary=Max('salary_max')
            )

            if salary_stats['average_salary']:
                skills_salary.append({
                    'skill_id': skill_data['skill_id'],
                    'skill_name': skill_data['skill__name'],
                    'category': skill_data['skill__category'],
                    'average_salary': salary_stats['average_salary'],
                    'min_salary': salary_stats['min_salary'],
                    'max_salary': salary_stats['max_salary'] or salary_stats['average_salary'],
                    'median_salary': None,
                    'job_count': skill_data['job_count'],
                    'salary_growth_percentage': None
                })

        # Sort by average salary
        skills_salary.sort(key=lambda x: x['average_salary'], reverse=True)

        serializer = SalaryBySkillSerializer(skills_salary, many=True)
        return Response({
            'count': len(skills_salary),
            'skills': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-role')
    def by_role(self, request):
        """
        Get salary statistics by role

        GET /api/analytics/salary/by-role/
        """
        roles_salary = []

        for role in Role.objects.all():
            # Find jobs matching this role
            jobs = JobPosting.objects.filter(
                Q(title__icontains=role.title) |
                Q(description_text__icontains=role.title),
                salary_min__isnull=False
            )

            salary_stats = jobs.aggregate(
                average_salary=Avg('salary_min'),
                min_salary=Min('salary_min'),
                max_salary=Max('salary_max')
            )

            if salary_stats['average_salary']:
                roles_salary.append({
                    'role_id': role.id,
                    'role_title': role.title,
                    'average_salary': salary_stats['average_salary'],
                    'min_salary': salary_stats['min_salary'],
                    'max_salary': salary_stats['max_salary'] or salary_stats['average_salary'],
                    'job_count': jobs.count(),
                    'demand_score': role.demand_score
                })

        roles_salary.sort(key=lambda x: x['average_salary'], reverse=True)

        serializer = SalaryByRoleSerializer(roles_salary, many=True)
        return Response({
            'count': len(roles_salary),
            'roles': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-location')
    def by_location(self, request):
        """
        Get salary statistics by location

        GET /api/analytics/salary/by-location/
        """
        location_salary = JobPosting.objects.filter(
            salary_min__isnull=False
        ).values('location').annotate(
            average_salary=Avg('salary_min'),
            min_salary=Min('salary_min'),
            max_salary=Max('salary_max'),
            job_count=Count('id')
        ).order_by('-average_salary')[:20]

        result = [
            {
                'location': entry['location'],
                'average_salary': entry['average_salary'],
                'min_salary': entry['min_salary'],
                'max_salary': entry['max_salary'] or entry['average_salary'],
                'job_count': entry['job_count']
            }
            for entry in location_salary
        ]

        serializer = SalaryByLocationSerializer(result, many=True)
        return Response({
            'count': len(result),
            'locations': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-experience')
    def by_experience(self, request):
        """
        Get salary statistics by experience level

        GET /api/analytics/salary/by-experience/
        """
        experience_labels = {
            'noExperience': 'No Experience',
            'between1And3': '1-3 Years',
            'between3And6': '3-6 Years',
            'moreThan6': '6+ Years'
        }

        experience_salary = JobPosting.objects.filter(
            salary_min__isnull=False,
            experience_required__isnull=False
        ).values('experience_required').annotate(
            average_salary=Avg('salary_min'),
            min_salary=Min('salary_min'),
            max_salary=Max('salary_max'),
            job_count=Count('id')
        ).order_by('experience_required')

        result = [
            {
                'experience_level': entry['experience_required'],
                'experience_display': experience_labels.get(entry['experience_required'], entry['experience_required']),
                'average_salary': entry['average_salary'],
                'min_salary': entry['min_salary'],
                'max_salary': entry['max_salary'] or entry['average_salary'],
                'job_count': entry['job_count']
            }
            for entry in experience_salary
        ]

        serializer = SalaryByExperienceSerializer(result, many=True)
        return Response({
            'count': len(result),
            'experience_levels': serializer.data
        })

    @action(detail=False, methods=['get'])
    def compare(self, request):
        """
        Compare salaries between skills or roles

        GET /api/analytics/salary/compare/?skills=1,2,3
        GET /api/analytics/salary/compare/?roles=1,2,3
        """
        skill_ids = request.query_params.get('skills')
        role_ids = request.query_params.get('roles')

        if skill_ids:
            skill_ids = [int(x) for x in skill_ids.split(',') if x.isdigit()]
            comparison = []

            for skill_id in skill_ids:
                try:
                    skill = Skill.objects.get(id=skill_id)
                    job_ids = JobSkill.objects.filter(skill=skill).values_list('job_posting_id', flat=True)

                    salary_stats = JobPosting.objects.filter(
                        id__in=job_ids,
                        salary_min__isnull=False
                    ).aggregate(
                        average_salary=Avg('salary_min'),
                        min_salary=Min('salary_min'),
                        max_salary=Max('salary_max'),
                        job_count=Count('id')
                    )

                    comparison.append({
                        'type': 'skill',
                        'id': skill.id,
                        'name': skill.name,
                        'average_salary': salary_stats['average_salary'],
                        'min_salary': salary_stats['min_salary'],
                        'max_salary': salary_stats['max_salary'],
                        'job_count': salary_stats['job_count']
                    })
                except Skill.DoesNotExist:
                    continue

            return Response({'comparison': comparison})

        elif role_ids:
            role_ids = [int(x) for x in role_ids.split(',') if x.isdigit()]
            comparison = []

            for role_id in role_ids:
                try:
                    role = Role.objects.get(id=role_id)
                    jobs = JobPosting.objects.filter(
                        Q(title__icontains=role.title),
                        salary_min__isnull=False
                    )

                    salary_stats = jobs.aggregate(
                        average_salary=Avg('salary_min'),
                        min_salary=Min('salary_min'),
                        max_salary=Max('salary_max'),
                        job_count=Count('id')
                    )

                    comparison.append({
                        'type': 'role',
                        'id': role.id,
                        'name': role.title,
                        'average_salary': salary_stats['average_salary'],
                        'min_salary': salary_stats['min_salary'],
                        'max_salary': salary_stats['max_salary'],
                        'job_count': salary_stats['job_count']
                    })
                except Role.DoesNotExist:
                    continue

            return Response({'comparison': comparison})

        return Response(
            {'detail': 'Please provide skills or roles to compare'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============== Skill Combinations ViewSet ==============

class SkillCombinationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for skill combinations analysis

    Endpoints:
    - GET /api/analytics/combinations/ - List all combinations
    - GET /api/analytics/combinations/{id}/ - Get combination details
    - GET /api/analytics/combinations/for-skill/{skill_id}/ - Get combinations for a skill
    - GET /api/analytics/combinations/tech-stacks/ - Get common tech stacks
    - GET /api/analytics/combinations/strongest/ - Get strongest correlations
    """
    serializer_class = SkillCombinationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SkillCombination.objects.select_related(
            'skill_1', 'skill_2'
        ).order_by('-co_occurrence_count')

    @action(detail=False, methods=['get'], url_path='for-skill/(?P<skill_id>[^/.]+)')
    def for_skill(self, request, skill_id=None):
        """
        Get skill combinations for a specific skill

        GET /api/analytics/combinations/for-skill/{skill_id}/
        """
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return Response(
                {'detail': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        combinations = SkillCombination.objects.filter(
            Q(skill_1=skill) | Q(skill_2=skill)
        ).order_by('-co_occurrence_count')[:20]

        result = []
        for combo in combinations:
            paired_skill = combo.skill_2 if combo.skill_1 == skill else combo.skill_1

            result.append({
                'skill': {
                    'id': paired_skill.id,
                    'name': paired_skill.name,
                    'category': paired_skill.category,
                    'category_display': paired_skill.get_category_display(),
                    'popularity_score': paired_skill.popularity_score
                },
                'co_occurrence_count': combo.co_occurrence_count,
                'correlation_score': combo.correlation_score,
                'combined_job_count': combo.co_occurrence_count
            })

        return Response({
            'skill': {
                'id': skill.id,
                'name': skill.name
            },
            'count': len(result),
            'related_skills': result
        })

    @action(detail=False, methods=['get'], url_path='tech-stacks')
    def tech_stacks(self, request):
        """
        Get common tech stacks based on skill combinations

        GET /api/analytics/combinations/tech-stacks/
        """
        # Define common stack patterns
        stacks = [
            {
                'name': 'MERN Stack',
                'skills': ['MongoDB', 'Express.js', 'React', 'Node.js'],
                'category': 'Full Stack'
            },
            {
                'name': 'MEAN Stack',
                'skills': ['MongoDB', 'Express.js', 'Angular', 'Node.js'],
                'category': 'Full Stack'
            },
            {
                'name': 'Django Stack',
                'skills': ['Python', 'Django', 'PostgreSQL', 'REST API'],
                'category': 'Backend'
            },
            {
                'name': 'Spring Stack',
                'skills': ['Java', 'Spring Boot', 'MySQL', 'REST API'],
                'category': 'Backend'
            },
            {
                'name': 'Data Science Stack',
                'skills': ['Python', 'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow'],
                'category': 'Data Science'
            },
            {
                'name': 'DevOps Stack',
                'skills': ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Terraform'],
                'category': 'DevOps'
            },
            {
                'name': 'Mobile (React Native)',
                'skills': ['React Native', 'JavaScript', 'TypeScript', 'Redux'],
                'category': 'Mobile'
            },
            {
                'name': 'Mobile (Flutter)',
                'skills': ['Flutter', 'Dart', 'Firebase'],
                'category': 'Mobile'
            }
        ]

        result = []
        for stack in stacks:
            # Find skills
            skill_objects = Skill.objects.filter(name__in=stack['skills'])

            if skill_objects.exists():
                # Count jobs that have all skills
                job_count = 0  # Would need complex query

                result.append({
                    'stack_name': stack['name'],
                    'skills': [
                        {
                            'id': s.id,
                            'name': s.name,
                            'category': s.category,
                            'category_display': s.get_category_display(),
                            'popularity_score': s.popularity_score
                        }
                        for s in skill_objects
                    ],
                    'job_count': job_count,
                    'average_salary': None,
                    'growth_trend': 'stable'
                })

        return Response({
            'count': len(result),
            'tech_stacks': result
        })

    @action(detail=False, methods=['get'])
    def strongest(self, request):
        """
        Get skill pairs with strongest correlation

        GET /api/analytics/combinations/strongest/?limit=20
        """
        limit = int(request.query_params.get('limit', 20))

        combinations = self.get_queryset().order_by('-correlation_score')[:limit]
        serializer = self.get_serializer(combinations, many=True)

        return Response({
            'count': combinations.count(),
            'combinations': serializer.data
        })


# ============== Job Market Insights ViewSet ==============

class JobMarketInsightsViewSet(viewsets.ViewSet):
    """
    ViewSet for job market insights

    Endpoints:
    - GET /api/analytics/market/overview/ - Get market overview
    - GET /api/analytics/market/by-work-type/ - Get jobs by work type
    - GET /api/analytics/market/by-employment-type/ - Get jobs by employment type
    - GET /api/analytics/market/top-companies/ - Get top hiring companies
    - GET /api/analytics/market/top-locations/ - Get top job locations
    - GET /api/analytics/market/freshness/ - Get job freshness stats
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get comprehensive job market overview

        GET /api/analytics/market/overview/
        """
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Basic counts
        total_jobs = JobPosting.objects.filter(is_active=True).count()
        jobs_this_month = JobPosting.objects.filter(
            published_at__gte=month_ago
        ).count()
        jobs_this_week = JobPosting.objects.filter(
            published_at__gte=week_ago
        ).count()

        # Average salary
        salary_stats = JobPosting.objects.filter(
            is_active=True,
            salary_min__isnull=False
        ).aggregate(avg_salary=Avg('salary_min'))

        # Work type distribution
        work_type_stats = JobPosting.objects.filter(
            is_active=True
        ).values('work_type').annotate(count=Count('id'))

        total_with_type = sum(w['count'] for w in work_type_stats)
        remote_pct = 0
        hybrid_pct = 0
        onsite_pct = 0

        for wt in work_type_stats:
            pct = (wt['count'] / total_with_type * 100) if total_with_type > 0 else 0
            if wt['work_type'] == 'remote':
                remote_pct = pct
            elif wt['work_type'] == 'hybrid':
                hybrid_pct = pct
            elif wt['work_type'] == 'onsite':
                onsite_pct = pct

        # Top hiring companies
        top_companies = JobPosting.objects.filter(
            is_active=True
        ).values('company_name').annotate(
            job_count=Count('id')
        ).order_by('-job_count')[:10]

        # Top locations
        top_locations = JobPosting.objects.filter(
            is_active=True
        ).values('location').annotate(
            job_count=Count('id')
        ).order_by('-job_count')[:10]

        data = {
            'total_active_jobs': total_jobs,
            'jobs_posted_this_month': jobs_this_month,
            'jobs_posted_this_week': jobs_this_week,
            'average_salary': salary_stats['avg_salary'],
            'remote_jobs_percentage': round(remote_pct, 2),
            'hybrid_jobs_percentage': round(hybrid_pct, 2),
            'onsite_jobs_percentage': round(onsite_pct, 2),
            'top_hiring_companies': [
                {'company_name': c['company_name'], 'job_count': c['job_count']}
                for c in top_companies
            ],
            'top_locations': [
                {'location': l['location'], 'job_count': l['job_count']}
                for l in top_locations
            ]
        }

        serializer = JobMarketOverviewSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-work-type')
    def by_work_type(self, request):
        """
        Get job distribution by work type

        GET /api/analytics/market/by-work-type/
        """
        work_type_labels = {
            'remote': 'Remote',
            'onsite': 'On-site',
            'hybrid': 'Hybrid'
        }

        stats = JobPosting.objects.filter(
            is_active=True
        ).values('work_type').annotate(
            job_count=Count('id'),
            avg_salary=Avg('salary_min')
        )

        total = sum(s['job_count'] for s in stats)

        result = [
            {
                'work_type': s['work_type'],
                'work_type_display': work_type_labels.get(s['work_type'], s['work_type']),
                'job_count': s['job_count'],
                'percentage': round((s['job_count'] / total * 100) if total > 0 else 0, 2),
                'average_salary': s['avg_salary']
            }
            for s in stats
        ]

        serializer = JobsByWorkTypeSerializer(result, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-employment-type')
    def by_employment_type(self, request):
        """
        Get job distribution by employment type

        GET /api/analytics/market/by-employment-type/
        """
        employment_labels = {
            'full_time': 'Full-time',
            'part_time': 'Part-time',
            'contract': 'Contract',
            'internship': 'Internship',
            'freelance': 'Freelance'
        }

        stats = JobPosting.objects.filter(
            is_active=True
        ).values('employment_type').annotate(
            job_count=Count('id'),
            avg_salary=Avg('salary_min')
        )

        total = sum(s['job_count'] for s in stats)

        result = [
            {
                'employment_type': s['employment_type'],
                'employment_type_display': employment_labels.get(s['employment_type'], s['employment_type']),
                'job_count': s['job_count'],
                'percentage': round((s['job_count'] / total * 100) if total > 0 else 0, 2),
                'average_salary': s['avg_salary']
            }
            for s in stats
        ]

        serializer = JobsByEmploymentTypeSerializer(result, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='top-companies')
    def top_companies(self, request):
        """
        Get top hiring companies with insights

        GET /api/analytics/market/top-companies/?limit=20
        """
        limit = int(request.query_params.get('limit', 20))

        companies = JobPosting.objects.filter(
            is_active=True
        ).values('company_name').annotate(
            job_count=Count('id'),
            avg_salary=Avg('salary_min')
        ).order_by('-job_count')[:limit]

        result = []
        for company in companies:
            # Get top skills for company
            company_jobs = JobPosting.objects.filter(
                company_name=company['company_name']
            ).values_list('id', flat=True)

            top_skills = JobSkill.objects.filter(
                job_posting_id__in=company_jobs
            ).values('skill__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]

            # Get locations
            locations = JobPosting.objects.filter(
                company_name=company['company_name']
            ).values_list('location', flat=True).distinct()[:5]

            result.append({
                'company_name': company['company_name'],
                'job_count': company['job_count'],
                'average_salary': company['avg_salary'],
                'top_skills': [s['skill__name'] for s in top_skills],
                'locations': list(locations)
            })

        serializer = CompanyInsightSerializer(result, many=True)
        return Response({
            'count': len(result),
            'companies': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='top-locations')
    def top_locations(self, request):
        """
        Get top job locations

        GET /api/analytics/market/top-locations/?limit=20
        """
        limit = int(request.query_params.get('limit', 20))

        locations = JobPosting.objects.filter(
            is_active=True
        ).values('location').annotate(
            job_count=Count('id'),
            avg_salary=Avg('salary_min')
        ).order_by('-job_count')[:limit]

        return Response({
            'count': len(locations),
            'locations': list(locations)
        })

    @action(detail=False, methods=['get'])
    def freshness(self, request):
        """
        Get job posting freshness statistics

        GET /api/analytics/market/freshness/
        """
        now = timezone.now()

        fresh_24h = JobPosting.objects.filter(
            is_active=True,
            published_at__gte=now - timedelta(hours=24)
        ).count()

        fresh_7d = JobPosting.objects.filter(
            is_active=True,
            published_at__gte=now - timedelta(days=7)
        ).count()

        fresh_30d = JobPosting.objects.filter(
            is_active=True,
            published_at__gte=now - timedelta(days=30)
        ).count()

        older = JobPosting.objects.filter(
            is_active=True,
            published_at__lt=now - timedelta(days=30)
        ).count()

        return Response({
            'last_24_hours': fresh_24h,
            'last_7_days': fresh_7d,
            'last_30_days': fresh_30d,
            'older_than_30_days': older,
            'total_active': fresh_24h + fresh_7d + fresh_30d + older
        })


# ============== Dashboard ViewSet ==============

class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard data

    Endpoints:
    - GET /api/analytics/dashboard/summary/ - Get complete dashboard summary
    - GET /api/analytics/dashboard/career-comparison/ - Compare career paths
    - GET /api/analytics/dashboard/personalized/ - Get personalized insights (auth required)
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get complete dashboard summary for main analytics page

        GET /api/analytics/dashboard/summary/
        """
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # Market Overview
        total_jobs = JobPosting.objects.filter(is_active=True).count()
        total_skills = Skill.objects.count()
        total_companies = JobPosting.objects.filter(is_active=True).values('company_name').distinct().count()
        avg_salary = JobPosting.objects.filter(
            is_active=True, salary_min__isnull=False
        ).aggregate(avg=Avg('salary_min'))['avg']

        # Calculate market growth
        last_month_jobs = JobPosting.objects.filter(
            published_at__gte=now - timedelta(days=60),
            published_at__lt=now - timedelta(days=30)
        ).count()
        this_month_jobs = JobPosting.objects.filter(
            published_at__gte=now - timedelta(days=30)
        ).count()
        growth = ((this_month_jobs - last_month_jobs) / last_month_jobs * 100) if last_month_jobs > 0 else 0

        new_jobs_week = JobPosting.objects.filter(published_at__gte=week_ago).count()

        # Trending skills (rising)
        trending = MarketTrend.objects.filter(
            trend_direction='rising'
        ).order_by('-demand_count')[:5]

        trending_skills = [
            {
                'skill_id': t.skill.id,
                'skill_name': t.skill.name,
                'category': t.skill.category,
                'category_display': t.skill.get_category_display(),
                'job_count': t.demand_count,
                'required_count': 0,
                'optional_count': 0,
                'average_salary': t.average_salary,
                'popularity_score': t.skill.popularity_score,
                'trend_direction': 'rising'
            }
            for t in trending
        ]

        # Top skills by demand
        top_skills_qs = JobSkill.objects.values(
            'skill_id', 'skill__name', 'skill__category', 'skill__popularity_score'
        ).annotate(
            job_count=Count('job_posting', distinct=True)
        ).order_by('-job_count')[:10]

        top_skills = [
            {
                'skill_id': s['skill_id'],
                'skill_name': s['skill__name'],
                'category': s['skill__category'],
                'category_display': dict(Skill.CATEGORY_CHOICES).get(s['skill__category'], ''),
                'job_count': s['job_count'],
                'required_count': 0,
                'optional_count': 0,
                'average_salary': None,
                'popularity_score': s['skill__popularity_score'],
                'trend_direction': None
            }
            for s in top_skills_qs
        ]

        # Top roles
        top_roles = Role.objects.order_by('-demand_score')[:10]
        top_roles_data = [
            {
                'id': r.id,
                'title': r.title,
                'demand_score': r.demand_score,
                'growth_potential': r.growth_potential
            }
            for r in top_roles
        ]

        # Top paying skills
        top_paying = []
        for skill_data in top_skills_qs[:10]:
            job_ids = JobSkill.objects.filter(
                skill_id=skill_data['skill_id']
            ).values_list('job_posting_id', flat=True)

            salary_stats = JobPosting.objects.filter(
                id__in=job_ids, salary_min__isnull=False
            ).aggregate(
                avg=Avg('salary_min'),
                min_s=Min('salary_min'),
                max_s=Max('salary_max')
            )

            if salary_stats['avg']:
                top_paying.append({
                    'skill_id': skill_data['skill_id'],
                    'skill_name': skill_data['skill__name'],
                    'category': skill_data['skill__category'],
                    'average_salary': salary_stats['avg'],
                    'min_salary': salary_stats['min_s'],
                    'max_salary': salary_stats['max_s'] or salary_stats['avg'],
                    'median_salary': None,
                    'job_count': skill_data['job_count'],
                    'salary_growth_percentage': None
                })

        top_paying.sort(key=lambda x: x['average_salary'], reverse=True)

        # Work type distribution
        work_types = JobPosting.objects.filter(is_active=True).values('work_type').annotate(
            job_count=Count('id'),
            avg_salary=Avg('salary_min')
        )
        total_wt = sum(w['job_count'] for w in work_types)

        work_type_dist = [
            {
                'work_type': w['work_type'],
                'work_type_display': dict(JobPosting.WORK_TYPE_CHOICES).get(w['work_type'], w['work_type']),
                'job_count': w['job_count'],
                'percentage': round((w['job_count'] / total_wt * 100) if total_wt > 0 else 0, 2),
                'average_salary': w['avg_salary']
            }
            for w in work_types
        ]

        data = {
            'total_jobs': total_jobs,
            'total_skills': total_skills,
            'total_companies': total_companies,
            'average_market_salary': avg_salary,
            'market_growth_percentage': round(growth, 2),
            'new_jobs_this_week': new_jobs_week,
            'trending_skills': trending_skills,
            'top_skills_by_demand': top_skills,
            'top_roles_by_demand': top_roles_data,
            'top_paying_skills': top_paying[:10],
            'work_type_distribution': work_type_dist
        }

        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='career-comparison')
    def career_comparison(self, request):
        """
        Compare different career paths

        GET /api/analytics/dashboard/career-comparison/?roles=1,2,3
        """
        role_ids = request.query_params.get('roles')

        if role_ids:
            role_ids = [int(x) for x in role_ids.split(',') if x.isdigit()]
            roles = Role.objects.filter(id__in=role_ids)
        else:
            roles = Role.objects.order_by('-demand_score')[:5]

        result = []
        for role in roles:
            # Count jobs
            job_count = JobPosting.objects.filter(
                Q(title__icontains=role.title)
            ).count()

            # Get required skills
            required_skills = RoleRequiredSkill.objects.filter(role=role).select_related('skill')[:5]

            # Determine market trend
            skill_ids = required_skills.values_list('skill_id', flat=True)
            rising = MarketTrend.objects.filter(
                skill_id__in=skill_ids, trend_direction='rising'
            ).count()
            declining = MarketTrend.objects.filter(
                skill_id__in=skill_ids, trend_direction='declining'
            ).count()

            if rising > declining:
                trend = 'rising'
            elif declining > rising:
                trend = 'declining'
            else:
                trend = 'stable'

            result.append({
                'role_id': role.id,
                'role_title': role.title,
                'demand_score': role.demand_score,
                'growth_potential': role.growth_potential,
                'average_salary_min': role.average_salary_min,
                'average_salary_max': role.average_salary_max,
                'job_count': job_count,
                'required_skills_count': required_skills.count(),
                'top_required_skills': [
                    {
                        'id': rs.skill.id,
                        'name': rs.skill.name,
                        'category': rs.skill.category,
                        'category_display': rs.skill.get_category_display(),
                        'popularity_score': rs.skill.popularity_score
                    }
                    for rs in required_skills
                ],
                'market_trend': trend
            })

        serializer = CareerComparisonSerializer(result, many=True)
        return Response({
            'count': len(result),
            'careers': serializer.data
        })

    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """
        Get personalized analytics for authenticated user

        GET /api/analytics/dashboard/personalized/
        """
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        from skills.models import UserSkill

        # Get user's skills
        user_skills = UserSkill.objects.filter(
            user=request.user,
            status='learned'
        ).select_related('skill')

        user_skill_ids = user_skills.values_list('skill_id', flat=True)

        # Skills in demand that user has
        in_demand_user_skills = JobSkill.objects.filter(
            skill_id__in=user_skill_ids
        ).values('skill__name').annotate(
            job_count=Count('job_posting', distinct=True)
        ).order_by('-job_count')[:10]

        # Skills user should learn (high demand, user doesn't have)
        top_demanded = JobSkill.objects.exclude(
            skill_id__in=user_skill_ids
        ).values('skill_id', 'skill__name', 'skill__category').annotate(
            job_count=Count('job_posting', distinct=True)
        ).order_by('-job_count')[:10]

        # Matching jobs
        matching_jobs = JobPosting.objects.filter(
            is_active=True,
            job_skills__skill_id__in=user_skill_ids
        ).distinct().count()

        # Salary potential
        job_ids = JobSkill.objects.filter(
            skill_id__in=user_skill_ids
        ).values_list('job_posting_id', flat=True)

        salary_potential = JobPosting.objects.filter(
            id__in=job_ids,
            salary_min__isnull=False
        ).aggregate(
            avg=Avg('salary_min'),
            max_s=Max('salary_max')
        )

        return Response({
            'user_skills_count': user_skills.count(),
            'matching_jobs_count': matching_jobs,
            'salary_potential': {
                'average': salary_potential['avg'],
                'maximum': salary_potential['max_s']
            },
            'your_in_demand_skills': list(in_demand_user_skills),
            'recommended_skills_to_learn': list(top_demanded)
        })
