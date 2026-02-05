"""
Learning App Views
==================
API views for learning roadmaps, roadmap items, and resources.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.learning.models import LearningRoadmap, RoadmapItem, LearningResource
from apps.learning.services import RoadmapGenerator, ResourceRecommender
from apps.learning.serializers import (
    RoadmapItemDetailSerializer,
    GenerateRoadmapRequestSerializer,
    UpdateItemStatusRequestSerializer,
    UpdateProgressRequestSerializer,
    LearningResourceSerializer,
)


class GenerateRoadmapView(APIView):
    """
    POST /api/v1/roadmaps/generate/

    Generate personalized learning roadmap using AI.
    Input: user profile, skill gaps, target role
    AI creates structured learning path with sequenced skills.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateRoadmapRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_role = serializer.validated_data.get('target_role')
        language = serializer.validated_data.get('language', 'en')
        max_skills = serializer.validated_data.get('max_skills', 15)

        generator = RoadmapGenerator(user=request.user)
        result = generator.generate_roadmap(
            target_role=target_role,
            language=language,
            max_skills=max_skills
        )

        if result.get('success'):
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class UserRoadmapsView(APIView):
    """
    GET /api/v1/roadmaps/

    Get all roadmaps for the authenticated user.
    Query params:
    - active_only: bool (default: true) - filter to active roadmaps only
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get('active_only', 'true').lower() == 'true'

        generator = RoadmapGenerator(user=request.user)
        roadmaps = generator.get_user_roadmaps(active_only=active_only)

        return Response({
            'count': len(roadmaps),
            'roadmaps': roadmaps,
        })


class RoadmapDetailView(APIView):
    """
    GET /api/v1/roadmaps/{roadmap_id}/

    Get single roadmap with full details including all items.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id):
        generator = RoadmapGenerator(user=request.user)
        roadmap = generator.get_roadmap_detail(roadmap_id)

        if not roadmap:
            return Response(
                {'error': 'Roadmap not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(roadmap)

    def delete(self, request, roadmap_id):
        """Deactivate (soft delete) a roadmap."""
        try:
            roadmap = LearningRoadmap.objects.get(
                roadmap_id=roadmap_id,
                user=request.user
            )
        except LearningRoadmap.DoesNotExist:
            return Response(
                {'error': 'Roadmap not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        roadmap.is_active = False
        roadmap.save()

        return Response({
            'roadmap_id': roadmap_id,
            'is_active': False,
            'message': 'Roadmap deactivated successfully',
        })


class UpdateItemStatusView(APIView):
    """
    PUT /api/v1/roadmaps/items/{item_id}/status/

    Update roadmap item status.
    Auto-adds completed skills to user_skills.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        serializer = UpdateItemStatusRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        generator = RoadmapGenerator(user=request.user)
        result = generator.update_item_status(item_id, new_status)

        if not result:
            return Response(
                {'error': 'Roadmap item not found or invalid status'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)


class RoadmapItemDetailView(APIView):
    """
    GET /api/v1/roadmaps/items/{item_id}/

    Get single roadmap item with details.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, item_id):
        try:
            item = RoadmapItem.objects.select_related(
                'skill', 'roadmap'
            ).prefetch_related('prerequisites__skill').get(
                item_id=item_id,
                roadmap__user=request.user
            )
        except RoadmapItem.DoesNotExist:
            return Response(
                {'error': 'Roadmap item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RoadmapItemDetailSerializer(item)
        return Response(serializer.data)


class RoadmapProgressView(APIView):
    """
    GET /api/v1/roadmaps/{roadmap_id}/progress/

    Get roadmap progress summary.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id):
        try:
            roadmap = LearningRoadmap.objects.prefetch_related('items').get(
                roadmap_id=roadmap_id,
                user=request.user
            )
        except LearningRoadmap.DoesNotExist:
            return Response(
                {'error': 'Roadmap not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        items = roadmap.items.all()
        total = items.count()
        completed = items.filter(status='completed').count()
        in_progress = items.filter(status='in_progress').count()
        skipped = items.filter(status='skipped').count()
        pending = total - completed - in_progress - skipped

        # Calculate time estimates
        total_hours = sum(i.estimated_duration_hours for i in items)
        completed_hours = sum(
            i.estimated_duration_hours
            for i in items.filter(status='completed')
        )
        remaining_hours = total_hours - completed_hours

        return Response({
            'roadmap_id': roadmap_id,
            'title': roadmap.title,
            'completion_percentage': roadmap.completion_percentage,
            'stats': {
                'total_items': total,
                'completed': completed,
                'in_progress': in_progress,
                'pending': pending,
                'skipped': skipped,
            },
            'time_estimates': {
                'total_hours': total_hours,
                'completed_hours': completed_hours,
                'remaining_hours': remaining_hours,
            },
        })


class LearningResourcesView(APIView):
    """
    GET /api/v1/roadmaps/resources/

    Get learning resources with filters.
    Query params:
    - skill_id: filter by skill
    - resource_type: filter by type (video, book, etc.)
    - difficulty_level: filter by difficulty
    - is_free: filter by free/paid
    - language: filter by content language
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = LearningResource.objects.select_related('skill')

        # Apply filters
        skill_id = request.query_params.get('skill_id')
        if skill_id:
            queryset = queryset.filter(skill_id=skill_id)

        resource_type = request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        difficulty = request.query_params.get('difficulty_level')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)

        is_free = request.query_params.get('is_free')
        if is_free is not None:
            queryset = queryset.filter(is_free=is_free.lower() == 'true')

        language = request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        resources = queryset[start:end]

        serializer = LearningResourceSerializer(resources, many=True)

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'resources': serializer.data,
        })


# =============================================================================
# Resource Recommendation Views
# =============================================================================

class SkillResourcesView(APIView):
    """
    GET /api/v1/resources/skill/{skill_id}/

    Get AI-recommended learning resources for a specific skill.
    Prioritizes free YouTube videos and official documentation.

    Query params:
    - language: preferred content language (en/ru/uz)
    - generate_if_missing: if true, AI generates recommendations if none exist
    - limit: max number of resources to return
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, skill_id):
        language = request.query_params.get('language', 'en')
        generate = request.query_params.get('generate_if_missing', 'true').lower() == 'true'
        limit = int(request.query_params.get('limit', 10))

        recommender = ResourceRecommender(user=request.user)
        result = recommender.get_resources_for_skill(
            skill_id=skill_id,
            language=language,
            generate_if_missing=generate,
            limit=limit
        )

        if result.get('success'):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_404_NOT_FOUND)


class StartResourceView(APIView):
    """
    POST /api/v1/resources/{resource_id}/start/

    Mark a learning resource as started for the current user.
    Creates a new UserLearningProgress record.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, resource_id):
        recommender = ResourceRecommender(user=request.user)
        result = recommender.start_resource(resource_id)

        if not result:
            return Response(
                {'error': 'Resource not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        status_code = status.HTTP_201_CREATED if result.get('created') else status.HTTP_200_OK
        return Response(result, status=status_code)


class UpdateResourceProgressView(APIView):
    """
    PUT /api/v1/resources/{resource_id}/progress/

    Update user's progress on a learning resource.

    Request body:
    - progress_percentage: int (0-100)
    - status: str (started/in_progress/completed/abandoned)
    - notes: str (optional)
    - rating: int (1-5, optional)
    - time_spent_hours: float (optional)
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, resource_id):
        serializer = UpdateProgressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recommender = ResourceRecommender(user=request.user)
        result = recommender.update_progress(
            resource_id=resource_id,
            progress_percentage=serializer.validated_data.get('progress_percentage'),
            status=serializer.validated_data.get('status'),
            notes=serializer.validated_data.get('notes'),
            rating=serializer.validated_data.get('rating'),
            time_spent_hours=serializer.validated_data.get('time_spent_hours'),
        )

        if not result:
            return Response(
                {'error': 'Progress record not found. Start the resource first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)


class UserLearningProgressView(APIView):
    """
    GET /api/v1/resources/progress/

    Get all learning progress for the current user.

    Query params:
    - status: filter by status (started/in_progress/completed/abandoned)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')

        recommender = ResourceRecommender(user=request.user)
        progress = recommender.get_user_progress(status=status_filter)

        return Response({
            'count': len(progress),
            'progress': progress,
        })
