"""
Skills App Views
================
API endpoints for skill gap analysis.

Endpoints:
- POST /api/v1/skills/analyze-gap/ - Analyze skill gaps
- GET /api/v1/skills/gaps/ - Get user's skill gaps
- GET /api/v1/skills/gaps/{gap_id}/ - Get specific gap
- PUT /api/v1/skills/gaps/{gap_id}/status/ - Update gap status
- GET /api/v1/skills/market-trends/ - Get market trends
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import SkillGap, MarketTrend, Skill
from .services.gap_analyzer import SkillGapAnalyzer
from apps.users.activity_log import log_user_activity
from apps.users.models import UserActivity
from .serializers import (
    AnalyzeGapRequestSerializer,
    AnalyzeGapResponseSerializer,
    SkillGapDetailSerializer,
    UpdateGapStatusRequestSerializer,
    UpdateGapStatusResponseSerializer,
    MarketTrendSerializer,
    SkillCategorySerializer,
)

logger = logging.getLogger(__name__)


class AnalyzeGapView(APIView):
    """
    POST /api/v1/skills/analyze-gap/

    Analyze skill gaps for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate request
        serializer = AnalyzeGapRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        target_role = validated.get('target_role')
        period = validated.get('period', '30d')
        language = validated.get('language', 'en')

        try:
            analyzer = SkillGapAnalyzer(user=request.user)
            result = analyzer.analyze_gaps(
                target_role=target_role,
                period=period,
                language=language
            )

            # Serialize response
            response_serializer = AnalyzeGapResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=False)

            if result.get('success'):
                missing = result.get('missing_skills') or []
                n = len(missing)
                log_user_activity(
                    request.user,
                    UserActivity.ActivityType.GAP_ANALYZED,
                    f'Skill gap analysis completed ({n} gap(s) identified).',
                    metadata={'gaps_count': n, 'target_role': result.get('target_role')},
                    link_path='/skills-gap',
                )
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Gap analysis failed for user {request.user.id}: {e}")
            return Response(
                {'error': 'Analysis failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserGapsView(APIView):
    """
    GET /api/v1/skills/gaps/

    Get all skill gaps for the authenticated user.

    Query params:
    - status: Filter by status (pending, learning, completed, skipped)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')

        # Validate status if provided
        valid_statuses = ['pending', 'learning', 'completed', 'skipped']
        if status_filter and status_filter not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        analyzer = SkillGapAnalyzer(user=request.user)
        gaps = analyzer.get_user_gaps(status=status_filter)

        # Exclude archived (skipped) gaps from default listing
        if not status_filter:
            gaps = [g for g in gaps if g['status'] != 'skipped']

        # Calculate status counts (exclude skipped from total)
        all_gaps = SkillGap.objects.filter(user=request.user)
        by_status = {
            'pending': all_gaps.filter(status='pending').count(),
            'learning': all_gaps.filter(status='learning').count(),
            'completed': all_gaps.filter(status='completed').count(),
        }

        return Response({
            'gaps': gaps,
            'total': len(gaps),
            'by_status': by_status,
        })


class GapDetailView(APIView):
    """
    GET /api/v1/skills/gaps/{gap_id}/

    Get details of a specific skill gap.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, gap_id):
        gap = get_object_or_404(
            SkillGap.objects.select_related('skill'),
            gap_id=gap_id,
            user=request.user
        )

        serializer = SkillGapDetailSerializer(gap)
        return Response(serializer.data)


class UpdateGapStatusView(APIView):
    """
    PUT /api/v1/skills/gaps/{gap_id}/status/

    Update the status of a skill gap.

    Note: When status is set to "completed", a UserSkill record is
    automatically created for the user.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, gap_id):
        # Validate request
        serializer = UpdateGapStatusRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']

        analyzer = SkillGapAnalyzer(user=request.user)
        result = analyzer.update_gap_status(gap_id=gap_id, status=new_status)

        if result:
            if result.get('old_status') != result.get('new_status'):
                log_user_activity(
                    request.user,
                    UserActivity.ActivityType.GAP_STATUS,
                    f'Skill gap updated: {result.get("skill_name", "skill")} → {new_status}.',
                    metadata={
                        'gap_id': gap_id,
                        'skill_name': result.get('skill_name'),
                        'new_status': new_status,
                    },
                    link_path='/skills-gap',
                )
            response_serializer = UpdateGapStatusResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=False)
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Skill gap not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ClearGapsView(APIView):
    """
    POST /api/v1/skills/gaps/clear/

    Archive all user's skill gaps by setting status to 'skipped'.
    Used before re-analyzing to clear previous results.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = SkillGap.objects.filter(
            user=request.user
        ).exclude(
            status='completed'
        ).update(status='skipped')

        if updated:
            log_user_activity(
                request.user,
                UserActivity.ActivityType.GAPS_CLEARED,
                f'Archived {updated} skill gap(s) before re-analysis.',
                metadata={'cleared': updated},
                link_path='/skills-gap',
            )

        return Response({
            'cleared': updated,
            'message': f'{updated} skill gap(s) archived.',
        }, status=status.HTTP_200_OK)


class MarketTrendsView(APIView):
    """
    GET /api/v1/skills/market-trends/

    Get market trends data.

    Query params:
    - period: Trend period (7d, 30d, 90d, 1y) - default: 30d
    - category: Filter by skill category
    - limit: Number of results (default: 50, max: 200)
    - offset: Pagination offset
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', '30d')
        category = request.query_params.get('category')

        try:
            limit = min(int(request.query_params.get('limit', 50)), 200)
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            return Response(
                {'error': 'limit and offset must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate period
        valid_periods = ['7d', '30d', '90d', '1y']
        if period not in valid_periods:
            return Response(
                {'error': f'Invalid period. Must be one of: {valid_periods}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build query
        queryset = MarketTrend.objects.filter(
            period=period
        ).select_related('skill').order_by('-demand_score')

        if category:
            queryset = queryset.filter(skill__category=category)

        total = queryset.count()
        trends = queryset[offset:offset + limit]

        # Serialize
        serializer = MarketTrendSerializer(trends, many=True)

        return Response({
            'trends': serializer.data,
            'total': total,
            'period': period,
            'limit': limit,
            'offset': offset,
        })


class SkillCategoriesView(APIView):
    """
    GET /api/v1/skills/categories/

    Get all skill categories with counts.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = (
            Skill.objects
            .values('category')
            .annotate(count=Count('skill_id'))
            .order_by('-count')
        )

        # Get category display names
        category_choices = dict(Skill.CATEGORY_CHOICES)

        data = [
            {
                'code': c['category'],
                'name': str(category_choices.get(c['category'], c['category'])),
                'count': c['count'],
            }
            for c in categories
        ]

        serializer = SkillCategorySerializer(data, many=True)
        return Response({'categories': serializer.data})
