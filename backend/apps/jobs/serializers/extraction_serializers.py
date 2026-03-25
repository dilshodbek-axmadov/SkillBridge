from rest_framework import serializers
from apps.jobs.models import ExtractionRun


class ExtractionRunSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = ExtractionRun
        fields = [
            'id', 'source', 'run_date', 'status', 'trigger',
            'started_at', 'finished_at', 'duration_seconds',
            'jobs_created', 'jobs_updated', 'jobs_skipped', 'jobs_deactivated',
            'aliases_created', 'errors_count', 'error_message',
            'celery_task_id', 'created_at',
        ]


class ExtractionStatsSerializer(serializers.Serializer):
    total_runs = serializers.IntegerField()
    successful_runs = serializers.IntegerField()
    failed_runs = serializers.IntegerField()
    last_success_date = serializers.DateField(allow_null=True)
    total_jobs_in_db = serializers.IntegerField()
    jobs_created_last_7_days = serializers.IntegerField()


class ManualRunSerializer(serializers.Serializer):
    run_date = serializers.DateField(required=False)
    source = serializers.CharField(default='hh.uz', required=False)
