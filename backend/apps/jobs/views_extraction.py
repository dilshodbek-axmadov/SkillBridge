"""
Admin-only views for extraction run management.
"""

from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.utils import timezone

from apps.jobs.models import ExtractionRun, JobPosting
from apps.jobs.serializers.extraction_serializers import (
    ExtractionRunSerializer,
    ExtractionStatsSerializer,
    ManualRunSerializer,
)
from apps.jobs.tasks import run_daily_extraction, retry_failed_extraction


class ExtractionRunListView(APIView):
    """
    GET /api/v1/jobs/extraction-runs/
    List all extraction runs (paginated, newest first).
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 50)
        offset = int(request.query_params.get('offset', 0))

        qs = ExtractionRun.objects.all()

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        total = qs.count()
        runs = qs[offset:offset + limit]
        serializer = ExtractionRunSerializer(runs, many=True)

        return Response({
            'total': total,
            'runs': serializer.data,
        })


class ExtractionStatsView(APIView):
    """
    GET /api/v1/jobs/extraction-stats/
    Summary statistics for the admin dashboard.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        last_success = (
            ExtractionRun.objects
            .filter(status='success')
            .order_by('-run_date')
            .values_list('run_date', flat=True)
            .first()
        )

        data = {
            'total_runs': ExtractionRun.objects.count(),
            'successful_runs': ExtractionRun.objects.filter(status='success').count(),
            'failed_runs': ExtractionRun.objects.filter(status='failed').count(),
            'last_success_date': last_success,
            'total_jobs_in_db': JobPosting.objects.count(),
            'jobs_created_last_7_days': JobPosting.objects.filter(
                scraped_at__gte=seven_days_ago
            ).count(),
        }

        serializer = ExtractionStatsSerializer(data)
        return Response(serializer.data)


class ManualExtractionView(APIView):
    """
    POST /api/v1/jobs/extraction-runs/trigger/
    Manually trigger an extraction for today (or a specified date).
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ManualRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        run_date = serializer.validated_data.get('run_date') or timezone.localdate()
        source = serializer.validated_data.get('source', 'hh.uz')

        existing = ExtractionRun.objects.filter(
            source=source, run_date=run_date,
            status__in=['pending', 'running', 'success'],
        ).first()

        if existing:
            return Response(
                {
                    'detail': f'Run already exists with status: {existing.status}',
                    'run': ExtractionRunSerializer(existing).data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        task = run_daily_extraction.apply_async(
            kwargs={
                'run_date_iso': run_date.isoformat(),
                'trigger': 'manual',
            }
        )

        return Response(
            {
                'detail': 'Extraction task dispatched.',
                'task_id': task.id,
                'run_date': run_date.isoformat(),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class RetryExtractionView(APIView):
    """
    POST /api/v1/jobs/extraction-runs/<id>/retry/
    Retry a failed extraction run.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, run_id):
        try:
            run = ExtractionRun.objects.get(id=run_id)
        except ExtractionRun.DoesNotExist:
            return Response(
                {'detail': 'Run not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if run.status != 'failed':
            return Response(
                {'detail': f'Can only retry failed runs. Current status: {run.status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = retry_failed_extraction.apply_async(
            kwargs={
                'run_date_iso': run.run_date.isoformat(),
                'source': run.source,
            }
        )

        return Response(
            {
                'detail': 'Retry task dispatched.',
                'task_id': task.id,
                'run_date': run.run_date.isoformat(),
            },
            status=status.HTTP_202_ACCEPTED,
        )
