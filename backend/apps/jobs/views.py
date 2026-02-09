"""
Jobs App Views
==============
API endpoints for job listings, search, and recommendations.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from apps.jobs.services import JobService


class JobListView(APIView):
    """
    GET /api/v1/jobs/

    List active jobs with filters.

    Query params:
    - q: search query
    - category: job category
    - experience: no_experience, junior, mid, senior, all
    - employment_type: full_time, part_time, project, all
    - location: location text
    - is_remote: true/false
    - salary_min: minimum salary
    - sort: posted_date (default), salary_max, salary_min
    - limit: results per page (default 20)
    - offset: pagination offset (default 0)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        filters = {
            'q': params.get('q', ''),
            'category': params.get('category', ''),
            'experience': params.get('experience', ''),
            'employment_type': params.get('employment_type', ''),
            'location': params.get('location', ''),
            'is_remote': params.get('is_remote', ''),
            'salary_min': params.get('salary_min', ''),
            'sort': params.get('sort', 'posted_date'),
        }

        limit = min(int(params.get('limit', 20)), 50)
        offset = int(params.get('offset', 0))

        service = JobService()
        result = service.list_jobs(filters, limit=limit, offset=offset)

        return Response({
            'total': result['total'],
            'limit': limit,
            'offset': offset,
            'jobs': result['jobs'],
        })


class JobDetailView(APIView):
    """
    GET /api/v1/jobs/<job_id>/

    Get job details.
    """
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        service = JobService()
        job = service.get_job_detail(job_id)

        if not job:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(job)


class RecommendedJobsView(APIView):
    """
    GET /api/v1/jobs/recommended/

    Get personalized job recommendations based on user's skills.

    Query params:
    - limit: max results (default 20)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 50)

        service = JobService()
        result = service.recommend_jobs(request.user, limit=limit)

        return Response(result)


class JobFiltersView(APIView):
    """
    GET /api/v1/jobs/filters/

    Get available filter options (categories, locations, etc.)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        service = JobService()
        return Response(service.get_filter_options())
