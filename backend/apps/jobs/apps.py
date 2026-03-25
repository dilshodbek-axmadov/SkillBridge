from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.jobs'

    def ready(self):
        """
        On Celery worker startup, check if today's extraction has run.
        If not, dispatch a catch-up task.

        Only runs inside the Celery worker process (not manage.py or wsgi).
        """
        import os
        if os.environ.get('CELERY_WORKER_RUNNING') != '1':
            return

        from django.utils import timezone
        from apps.jobs.models import ExtractionRun

        today = timezone.localdate()
        already_ran = ExtractionRun.objects.filter(
            source='hh.uz',
            run_date=today,
            status__in=['pending', 'running', 'success'],
        ).exists()

        if not already_ran:
            from apps.jobs.tasks import run_daily_extraction
            run_daily_extraction.apply_async(
                kwargs={'trigger': 'startup'},
                countdown=30,
            )
