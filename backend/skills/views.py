"""
Views for Skills API
"""
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q

from skills.models import Skill, SkillLevel, UserSkill
from skills.serializers import (
    SkillSerializer, SkillDetailSerializer, SkillLevelSerializer,
    UserSkillSerializer, AddUserSkillSerializer, UpdateUserSkillSerializer,
    MarkSkillLearnedSerializer, SkillSearchSerializer, SkillStatisticsSerializer
)


# SKILL VIEWSETS

class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for skills
    Provides list and retrieve actions
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['category']
    ordering_fields = ['name', 'popularity_score', 'created_at']
    ordering = ['-popularity_score']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SkillDetailSerializer
        return SkillSerializer
    
    def get_queryset(self):
        queryset = Skill.objects.all()
        
        # Filter by minimum popularity
        min_popularity = self.request.query_params.get('min_popularity')
        if min_popularity:
            try:
                queryset = queryset.filter(popularity_score__gte=float(min_popularity))
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular skills"""
        limit = int(request.query_params.get('limit', 10))
        skills = Skill.objects.order_by('-popularity_score')[:limit]
        serializer = self.get_serializer(skills, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get skills grouped by category"""
        category = request.query_params.get('category')
        
        if not category:
            return Response(
                {'error': 'category parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        skills = Skill.objects.filter(category=category).order_by('-popularity_score')
        serializer = self.get_serializer(skills, many=True)
        
        return Response({
            'category': category,
            'count': skills.count(),
            'skills': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get skills that commonly appear with this skill"""
        skill = self.get_object()
        
        from analytics.models import SkillCombination
        
        # Get combinations where this skill appears
        combinations = SkillCombination.objects.filter(
            Q(skill_1=skill) | Q(skill_2=skill)
        ).order_by('-co_occurrence_count')[:10]
        
        related_skill_ids = set()
        for combo in combinations:
            if combo.skill_1_id == skill.id:
                related_skill_ids.add(combo.skill_2_id)
            else:
                related_skill_ids.add(combo.skill_1_id)
        
        related_skills = Skill.objects.filter(id__in=related_skill_ids)
        serializer = self.get_serializer(related_skills, many=True)
        
        return Response({
            'skill': skill.name,
            'related_skills': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall skill statistics"""
        total_skills = Skill.objects.count()
        
        # Skills by category
        skills_by_category = {}
        for category_code, category_name in Skill.CATEGORY_CHOICES:
            count = Skill.objects.filter(category=category_code).count()
            skills_by_category[category_name] = count
        
        # Top 10 skills
        top_skills = Skill.objects.order_by('-popularity_score')[:10].values(
            'id', 'name', 'popularity_score'
        )
        
        # Build base data
        data = {
            'total_skills': total_skills,
            'skills_by_category': skills_by_category,
            'top_skills': list(top_skills),
            'user_skill_count': 0,  # Default values
            'user_learned_count': 0,
            'user_in_progress_count': 0,
        }
    
        # User-specific stats (if authenticated)
        if request.user.is_authenticated:
            user_skills = UserSkill.objects.filter(user=request.user)
            data['user_skill_count'] = user_skills.count()
            data['user_learned_count'] = user_skills.filter(status='learned').count()
            data['user_in_progress_count'] = user_skills.filter(status='in_progress').count()
        
        serializer = SkillStatisticsSerializer(data)
        return Response(serializer.data)


class SkillLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for skill levels
    """
    queryset = SkillLevel.objects.all().order_by('level_order')
    serializer_class = SkillLevelSerializer
    permission_classes = [AllowAny]


# USER SKILL VIEWSETS

class UserSkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user's skills
    """
    serializer_class = UserSkillSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get skills for current user"""
        queryset = UserSkill.objects.filter(user=self.request.user).select_related(
            'skill', 'level'
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(skill__category=category)
        
        return queryset.order_by('-date_added')
    
    def create(self, request, *args, **kwargs):
        """Add a skill to user's profile"""
        serializer = AddUserSkillSerializer(data=request.data)
        
        if serializer.is_valid():
            skill_id = serializer.validated_data['skill_id']
            level_id = serializer.validated_data.get('level_id')
            status_value = serializer.validated_data.get('status', 'not_started')
            proof_url = serializer.validated_data.get('proof_url', '')
            
            # Check if user already has this skill
            if UserSkill.objects.filter(user=request.user, skill_id=skill_id).exists():
                return Response(
                    {'error': 'You already have this skill. Use PATCH to update it.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get skill and level
            skill = Skill.objects.get(id=skill_id)
            level = SkillLevel.objects.get(id=level_id) if level_id else None
            
            # Create user skill
            user_skill = UserSkill.objects.create(
                user=request.user,
                skill=skill,
                level=level,
                status=status_value,
                proof_url=proof_url,
                self_assessed=True
            )
            
            # Update user profile completion
            request.user.update_profile_completion()
            
            result_serializer = UserSkillSerializer(user_skill)
            return Response(
                result_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update a user skill"""
        user_skill = self.get_object()
        serializer = UpdateUserSkillSerializer(data=request.data)
        
        if serializer.is_valid():
            # Update fields
            if 'level_id' in serializer.validated_data:
                level_id = serializer.validated_data['level_id']
                user_skill.level = SkillLevel.objects.get(id=level_id) if level_id else None
            
            if 'status' in serializer.validated_data:
                new_status = serializer.validated_data['status']
                
                if new_status == 'learned' and user_skill.status != 'learned':
                    # Mark as learned
                    user_skill.mark_as_learned(user_skill.level)
                elif new_status == 'in_progress':
                    user_skill.mark_in_progress()
                else:
                    user_skill.status = new_status
            
            if 'proof_url' in serializer.validated_data:
                user_skill.proof_url = serializer.validated_data['proof_url']
            
            user_skill.save()
            
            result_serializer = UserSkillSerializer(user_skill)
            return Response(result_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Remove a skill from user's profile"""
        user_skill = self.get_object()
        user_skill.delete()
        
        # Update user profile completion
        request.user.update_profile_completion()
        
        return Response(
            {'message': 'Skill removed successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def mark_learned(self, request, pk=None):
        """Mark a skill as learned"""
        user_skill = self.get_object()
        serializer = MarkSkillLearnedSerializer(data=request.data)
        
        if serializer.is_valid():
            level_id = serializer.validated_data.get('level_id')
            proof_url = serializer.validated_data.get('proof_url')
            
            level = SkillLevel.objects.get(id=level_id) if level_id else user_skill.level
            
            if proof_url:
                user_skill.proof_url = proof_url
            
            user_skill.mark_as_learned(level)
            
            result_serializer = UserSkillSerializer(user_skill)
            return Response({
                'message': 'Skill marked as learned!',
                'skill': result_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        """Mark a skill as in progress"""
        user_skill = self.get_object()
        user_skill.mark_in_progress()
        
        result_serializer = UserSkillSerializer(user_skill)
        return Response({
            'message': 'Skill marked as in progress',
            'skill': result_serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def learned(self, request):
        """Get all learned skills"""
        skills = self.get_queryset().filter(status='learned')
        serializer = self.get_serializer(skills, many=True)
        
        return Response({
            'count': skills.count(),
            'skills': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def in_progress(self, request):
        """Get all skills in progress"""
        skills = self.get_queryset().filter(status='in_progress')
        serializer = self.get_serializer(skills, many=True)
        
        return Response({
            'count': skills.count(),
            'skills': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of user's skills"""
        user_skills = self.get_queryset()
        
        summary = {
            'total': user_skills.count(),
            'learned': user_skills.filter(status='learned').count(),
            'in_progress': user_skills.filter(status='in_progress').count(),
            'not_started': user_skills.filter(status='not_started').count(),
            'by_category': {}
        }
        
        # Group by category
        for category_code, category_name in Skill.CATEGORY_CHOICES:
            count = user_skills.filter(skill__category=category_code).count()
            if count > 0:
                summary['by_category'][category_name] = count
        
        return Response(summary)