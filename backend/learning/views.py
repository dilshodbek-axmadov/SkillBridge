"""
Views for Learning app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum
from datetime import timedelta

from .models import (
    LearningRoadmap, RoadmapItem,
    LearningResource, RoadmapResource
)
from .serializers import (
    LearningRoadmapSerializer, LearningRoadmapListSerializer,
    RoadmapItemSerializer, RoadmapItemUpdateSerializer,
    LearningResourceSerializer, RoadmapResourceSerializer,
    RoadmapProgressSerializer, SkillResourceRecommendationSerializer
)
from skills.models import UserSkill


class LearningRoadmapViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing learning roadmaps
    
    Endpoints:
    - GET /api/learning/roadmaps/ - List user's roadmaps
    - POST /api/learning/roadmaps/ - Create new roadmap
    - GET /api/learning/roadmaps/{id}/ - Get roadmap details
    - PUT /api/learning/roadmaps/{id}/ - Update roadmap
    - DELETE /api/learning/roadmaps/{id}/ - Delete roadmap
    - GET /api/learning/roadmaps/active/ - Get active roadmap
    - POST /api/learning/roadmaps/{id}/activate/ - Set as active roadmap
    - POST /api/learning/roadmaps/{id}/deactivate/ - Deactivate roadmap
    - GET /api/learning/roadmaps/{id}/progress/ - Get detailed progress
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get roadmaps for current user"""
        return LearningRoadmap.objects.filter(
            user=self.request.user
        ).select_related('role').prefetch_related(
            'roadmap_items__skill',
            'roadmap_items__roadmap_resources__resource'
        ).order_by('-is_active', '-created_date')
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail"""
        if self.action == 'list':
            return LearningRoadmapListSerializer
        return LearningRoadmapSerializer
    
    def perform_create(self, serializer):
        """Create roadmap for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get user's active roadmap
        
        GET /api/learning/roadmaps/active/
        """
        roadmap = self.get_queryset().filter(is_active=True).first()
        
        if not roadmap:
            return Response(
                {'detail': 'No active roadmap found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(roadmap)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Set this roadmap as active (deactivates others)
        
        POST /api/learning/roadmaps/{id}/activate/
        """
        roadmap = self.get_object()
        
        # Deactivate all other roadmaps
        LearningRoadmap.objects.filter(
            user=request.user
        ).update(is_active=False)
        
        # Activate this roadmap
        roadmap.is_active = True
        roadmap.save()
        
        serializer = self.get_serializer(roadmap)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate this roadmap
        
        POST /api/learning/roadmaps/{id}/deactivate/
        """
        roadmap = self.get_object()
        roadmap.is_active = False
        roadmap.save()
        
        serializer = self.get_serializer(roadmap)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get detailed progress statistics for roadmap
        
        GET /api/learning/roadmaps/{id}/progress/
        """
        roadmap = self.get_object()
        
        # Get statistics
        items = roadmap.roadmap_items.all()
        total_skills = items.count()
        completed = items.filter(status='completed')
        completed_skills = completed.count()
        in_progress_skills = items.filter(status='in_progress').count()
        pending_skills = items.filter(status='pending').count()
        
        # Calculate time estimates
        total_estimated_weeks = items.aggregate(
            total=Sum('estimated_duration_weeks')
        )['total'] or 0
        
        weeks_completed = completed.aggregate(
            total=Sum('actual_duration_weeks')
        )['total'] or 0
        
        # Check if on track
        if total_skills > 0:
            expected_progress = (weeks_completed / total_estimated_weeks * 100) if total_estimated_weeks > 0 else 0
            is_on_track = roadmap.completion_percentage >= (expected_progress * 0.9)  # Within 10%
        else:
            is_on_track = True
        
        progress_data = {
            'roadmap_id': roadmap.id,
            'role_title': roadmap.role.title,
            'completion_percentage': roadmap.completion_percentage,
            'total_skills': total_skills,
            'completed_skills': completed_skills,
            'in_progress_skills': in_progress_skills,
            'pending_skills': pending_skills,
            'total_estimated_weeks': total_estimated_weeks,
            'weeks_completed': weeks_completed,
            'estimated_completion_date': roadmap.estimated_completion_date,
            'is_on_track': is_on_track
        }
        
        serializer = RoadmapProgressSerializer(progress_data)
        return Response(serializer.data)


class RoadmapItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roadmap items
    
    Endpoints:
    - GET /api/learning/roadmap-items/ - List roadmap items
    - POST /api/learning/roadmap-items/ - Create roadmap item
    - GET /api/learning/roadmap-items/{id}/ - Get item details
    - PATCH /api/learning/roadmap-items/{id}/ - Update item
    - DELETE /api/learning/roadmap-items/{id}/ - Delete item
    - POST /api/learning/roadmap-items/{id}/start/ - Mark as in-progress
    - POST /api/learning/roadmap-items/{id}/complete/ - Mark as completed
    - POST /api/learning/roadmap-items/{id}/reset/ - Reset to pending
    - GET /api/learning/roadmap-items/next/ - Get next item to learn
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RoadmapItemSerializer
    
    def get_queryset(self):
        """Get roadmap items for current user's roadmaps"""
        return RoadmapItem.objects.filter(
            roadmap__user=self.request.user
        ).select_related(
            'roadmap', 'roadmap__role', 'skill'
        ).prefetch_related(
            'roadmap_resources__resource'
        ).order_by('roadmap', 'sequence_order')
    
    def get_serializer_class(self):
        """Use update serializer for partial updates"""
        if self.action in ['update', 'partial_update', 'start', 'complete', 'reset']:
            return RoadmapItemUpdateSerializer
        return RoadmapItemSerializer
    
    @action(detail=False, methods=['get'])
    def next(self, request):
        """
        Get next item to learn from active roadmap
        
        GET /api/learning/roadmap-items/next/
        """
        active_roadmap = LearningRoadmap.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if not active_roadmap:
            return Response(
                {'detail': 'No active roadmap found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        next_item = active_roadmap.get_next_skill()
        
        if not next_item:
            return Response(
                {'detail': 'All items completed!'},
                status=status.HTTP_200_OK
            )
        
        serializer = RoadmapItemSerializer(next_item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Mark roadmap item as in-progress
        
        POST /api/learning/roadmap-items/{id}/start/
        """
        item = self.get_object()
        
        if item.status != 'pending':
            return Response(
                {'detail': f'Cannot start item with status: {item.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item.status = 'in_progress'
        item.started_date = timezone.now()
        item.save()
        
        # Update roadmap completion
        item.roadmap.update_completion_percentage()
        
        serializer = RoadmapItemSerializer(item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark roadmap item as completed
        
        POST /api/learning/roadmap-items/{id}/complete/
        Body: {
            "actual_duration_weeks": 4,
            "notes": "Optional completion notes"
        }
        """
        item = self.get_object()
        
        if item.status not in ['pending', 'in_progress']:
            return Response(
                {'detail': f'Cannot complete item with status: {item.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get actual duration from request
        actual_duration = request.data.get('actual_duration_weeks')
        if not actual_duration:
            return Response(
                {'detail': 'actual_duration_weeks is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update item
        item.status = 'completed'
        item.completed_date = timezone.now()
        item.actual_duration_weeks = actual_duration
        
        if request.data.get('notes'):
            item.notes = request.data.get('notes')
        
        item.save()
        
        # Update or create UserSkill as learned
        UserSkill.objects.update_or_create(
            user=item.roadmap.user,
            skill=item.skill,
            defaults={
                'proficiency_level': 'intermediate',  # Default level
                'years_of_experience': actual_duration / 52,  # Convert weeks to years
                'is_primary': False,
                'last_used_date': timezone.now()
            }
        )
        
        # Update roadmap completion
        item.roadmap.update_completion_percentage()
        
        serializer = RoadmapItemSerializer(item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """
        Reset roadmap item to pending
        
        POST /api/learning/roadmap-items/{id}/reset/
        """
        item = self.get_object()
        
        if item.status == 'completed':
            return Response(
                {'detail': 'Cannot reset completed items'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item.status = 'pending'
        item.started_date = None
        item.save()
        
        # Update roadmap completion
        item.roadmap.update_completion_percentage()
        
        serializer = RoadmapItemSerializer(item)
        return Response(serializer.data)


class LearningResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for learning resources
    
    Endpoints:
    - GET /api/learning/resources/ - List all resources (with filters)
    - POST /api/learning/resources/ - Create resource (admin)
    - GET /api/learning/resources/{id}/ - Get resource details
    - PUT /api/learning/resources/{id}/ - Update resource (admin)
    - DELETE /api/learning/resources/{id}/ - Delete resource (admin)
    - GET /api/learning/resources/for-skill/{skill_id}/ - Get resources for a skill
    - GET /api/learning/resources/recommended/ - Get recommended resources
    """
    serializer_class = LearningResourceSerializer
    
    def get_queryset(self):
        """Get learning resources with optional filters"""
        queryset = LearningResource.objects.all()
        
        # Filter by resource type
        resource_type = self.request.query_params.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filter by free/paid
        is_free = self.request.query_params.get('is_free')
        if is_free is not None:
            queryset = queryset.filter(is_free=is_free.lower() == 'true')
        
        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language__icontains=language)
        
        # Search by title/description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Sort by rating
        queryset = queryset.order_by('-rating', '-created_date')
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='for-skill/(?P<skill_id>[^/.]+)')
    def for_skill(self, request, skill_id=None):
        """
        Get learning resources recommended for a specific skill
        
        GET /api/learning/resources/for-skill/{skill_id}/
        """
        from skills.models import Skill
        
        skill = get_object_or_404(Skill, id=skill_id)
        
        # Get resources from roadmap items for this skill
        roadmap_resources = RoadmapResource.objects.filter(
            roadmap_item__skill=skill
        ).select_related('resource').distinct()
        
        # Get unique resources
        resources = [rr.resource for rr in roadmap_resources]
        
        # If no specific resources, get resources matching skill difficulty
        if not resources:
            resources = LearningResource.objects.filter(
                difficulty=skill.difficulty_level
            ).order_by('-rating')[:10]
        
        # Calculate statistics
        total_resources = len(resources)
        free_count = sum(1 for r in resources if r.is_free)
        paid_count = total_resources - free_count
        
        response_data = {
            'skill_id': skill.id,
            'skill_name': skill.name,
            'recommended_resources': LearningResourceSerializer(resources, many=True).data,
            'total_resources': total_resources,
            'free_resources_count': free_count,
            'paid_resources_count': paid_count
        }
        
        serializer = SkillResourceRecommendationSerializer(response_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """
        Get recommended resources based on user's active roadmap
        
        GET /api/learning/resources/recommended/
        """
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get active roadmap
        active_roadmap = LearningRoadmap.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if not active_roadmap:
            return Response(
                {'detail': 'No active roadmap found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get resources for in-progress and next pending items
        in_progress_items = active_roadmap.roadmap_items.filter(
            status='in_progress'
        )
        next_item = active_roadmap.get_next_skill()
        
        items = list(in_progress_items)
        if next_item:
            items.append(next_item)
        
        # Get resources for these items
        roadmap_resources = RoadmapResource.objects.filter(
            roadmap_item__in=items,
            is_recommended=True
        ).select_related('resource').order_by('-resource__rating')[:20]
        
        resources = [rr.resource for rr in roadmap_resources]
        
        serializer = LearningResourceSerializer(resources, many=True)
        return Response(serializer.data)


class RoadmapResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roadmap resources
    
    Endpoints:
    - GET /api/learning/roadmap-resources/ - List roadmap resources
    - POST /api/learning/roadmap-resources/ - Add resource to roadmap item
    - DELETE /api/learning/roadmap-resources/{id}/ - Remove resource
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RoadmapResourceSerializer
    
    def get_queryset(self):
        """Get roadmap resources for current user's roadmaps"""
        return RoadmapResource.objects.filter(
            roadmap_item__roadmap__user=self.request.user
        ).select_related(
            'roadmap_item', 'roadmap_item__skill', 'resource'
        ).order_by('-added_date')