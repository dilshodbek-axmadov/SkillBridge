# backend/apps/users/management/commands/initialize_system.py
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.jobs.models import JobPosting
from apps.skills.models import MarketTrend
from apps.chatbot.models import JobVector, SkillVector

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize the system by scraping jobs, calculating trends, and building RAG index if data is missing'

    def handle(self, *args, **options):
        # 1. Sync jobs if none exist
        if not JobPosting.objects.exists():
            self.stdout.write(self.style.WARNING('No jobs found. Running sync_jobs --full...'))
            try:
                call_command('sync_jobs', full=True)
                self.stdout.write(self.style.SUCCESS('Successfully synced jobs'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to sync jobs: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('Jobs already exist, skipping sync_jobs'))

        # 2. Calculate market trends if none exist
        if not MarketTrend.objects.exists():
            self.stdout.write(self.style.WARNING('No market trends found. Running calculate_market_trends...'))
            try:
                call_command('calculate_market_trends', all_periods=True)
                self.stdout.write(self.style.SUCCESS('Successfully calculated market trends'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to calculate market trends: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('Market trends already exist, skipping calculate_market_trends'))

        # 3. Build RAG index if none exist
        # We check both JobVector and SkillVector to ensure a full index is built if either is empty
        if not JobVector.objects.exists() or not SkillVector.objects.exists():
            self.stdout.write(self.style.WARNING('RAG vectors missing. Running build_rag_index --full...'))
            try:
                call_command('build_rag_index', full=True)
                self.stdout.write(self.style.SUCCESS('Successfully built RAG index'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to build RAG index: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('RAG index already exists, skipping build_rag_index'))

        # 4. Refresh analytics
        self.stdout.write(self.style.WARNING('Refreshing analytics...'))
        try:
            call_command('refresh_analytics')
            self.stdout.write(self.style.SUCCESS('Successfully refreshed analytics'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to refresh analytics: {e}'))

        self.stdout.write(self.style.SUCCESS('System initialization complete'))
