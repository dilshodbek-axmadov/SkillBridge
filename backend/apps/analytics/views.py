"""
Analytics App Views
===================
API views for dashboard analytics.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.analytics.services import DashboardService
from apps.users.models import User


class MarketOverviewView(APIView):
    """
    GET /api/v1/analytics/market/overview/

    Get overall market overview statistics.
    Public endpoint - useful for newcomers exploring the job market.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        service = DashboardService()
        overview = service.get_market_overview()

        return Response(overview)


class TrendingSkillsView(APIView):
    """
    GET /api/v1/analytics/market/skills/trending/

    Get most in-demand skills with trend data.

    Query params:
    - limit: number of skills to return (default: 20)
    - period: time period (7d, 30d, 90d, all) (default: 30d)
    """

    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 20))
        period = request.query_params.get('period', '30d')

        if period not in ('7d', '30d', '90d', 'all'):
            period = '30d'

        service = DashboardService()
        skills = service.get_trending_skills(limit=limit, period=period)

        return Response({
            'period': period,
            'count': len(skills),
            'skills': skills,
        })


class SalaryInsightsView(APIView):
    """
    GET /api/v1/analytics/market/salaries/

    Get salary insights by job title.

    Query params:
    - experience_level: filter by experience (all, no_experience, junior, mid, senior)
    - limit: number of results (default: 20)
    """

    permission_classes = [AllowAny]

    def get(self, request):
        experience = request.query_params.get('experience_level', 'all')
        limit = int(request.query_params.get('limit', 20))

        if experience not in ('all', 'no_experience', 'junior', 'mid', 'senior'):
            experience = 'all'

        service = DashboardService()
        salaries = service.get_salary_insights(
            experience_level=experience if experience != 'all' else None,
            limit=limit
        )

        return Response(salaries)


class JobCategoriesView(APIView):
    """
    GET /api/v1/analytics/market/categories/

    Get job openings by category with salary data.

    Query params:
    - limit: number of categories (default: 15)
    """

    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 15))

        service = DashboardService()
        categories = service.get_job_categories(limit=limit)

        return Response({
            'count': len(categories),
            'categories': categories,
        })


class SkillTrendView(APIView):
    """
    GET /api/v1/analytics/market/skills/{skill_id}/trend/

    Get historical trend data for a specific skill.

    Query params:
    - weeks: number of weeks of history (default: 12)
    """

    permission_classes = [AllowAny]

    def get(self, request, skill_id):
        weeks = int(request.query_params.get('weeks', 12))

        service = DashboardService()
        trend = service.get_skill_trend(skill_id=skill_id, weeks=weeks)

        if not trend:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(trend)


class UserProgressView(APIView):
    """
    GET /api/v1/analytics/user/progress/

    Get authenticated user's learning progress analytics.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = DashboardService()
        progress = service.get_user_progress(user=request.user)

        return Response(progress)


class UserProgressByIdView(APIView):
    """
    GET /api/v1/analytics/user/{user_id}/progress/

    Get a specific user's learning progress (admin or self only).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        # Only allow viewing own progress or admin
        if request.user.user_id != user_id and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        service = DashboardService()
        progress = service.get_user_progress(user=user)

        return Response(progress)


class DashboardSummaryView(APIView):
    """
    GET /api/v1/analytics/dashboard/

    Get complete dashboard data in a single request.
    Combines market overview, trending skills, categories, and salaries.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        service = DashboardService()

        return Response({
            'market_overview': service.get_market_overview(),
            'trending_skills': service.get_trending_skills(limit=10, period='30d'),
            'job_categories': service.get_job_categories(limit=10),
            'top_salaries': service.get_salary_insights(limit=10),
        })
