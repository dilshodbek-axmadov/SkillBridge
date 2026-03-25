"""
Celery Tasks for Job Extraction
================================
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='apps.jobs.tasks.run_daily_extraction',
    max_retries=2,
    default_retry_delay=300,
    acks_late=True,
)
def run_daily_extraction(self, run_date_iso=None, trigger='scheduled'):
    """
    Celery task that wraps ExtractionService.run().

    Args:
        run_date_iso: Optional ISO date string (YYYY-MM-DD).
                      Defaults to today in the server's local timezone.
        trigger: 'scheduled', 'manual', or 'startup'
    """
    from apps.jobs.extraction_service import ExtractionService
    from datetime import date

    run_date = date.fromisoformat(run_date_iso) if run_date_iso else timezone.localdate()
    service = ExtractionService(source='hh.uz')

    try:
        extraction_run = service.run(run_date=run_date, trigger=trigger)

        if extraction_run.celery_task_id == '' and self.request.id:
            extraction_run.celery_task_id = self.request.id
            extraction_run.save(update_fields=['celery_task_id'])

        return {
            'status': extraction_run.status,
            'run_date': str(extraction_run.run_date),
            'jobs_created': extraction_run.jobs_created,
            'jobs_updated': extraction_run.jobs_updated,
        }

    except Exception as exc:
        logger.exception(f"Extraction task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(name='apps.jobs.tasks.retry_failed_extraction')
def retry_failed_extraction(run_date_iso, source='hh.uz'):
    """
    Retry a previously failed extraction run.
    Called from the admin API endpoint.
    """
    from apps.jobs.extraction_service import ExtractionService
    from datetime import date

    run_date = date.fromisoformat(run_date_iso)
    extraction_run = ExtractionService.retry(run_date=run_date, source=source)

    return {
        'status': extraction_run.status,
        'run_date': str(extraction_run.run_date),
        'jobs_created': extraction_run.jobs_created,
    }
