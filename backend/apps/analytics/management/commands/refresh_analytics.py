"""
Refresh Analytics Snapshots
===========================

Management command to refresh all analytics snapshot data.
Should be run periodically (e.g., daily via cron job).

Usage:
    python manage.py refresh_analytics
    python manage.py refresh_analytics --dashboard-only
    python manage.py refresh_analytics --skills-only
"""

from django.core.management.base import BaseCommand

from apps.analytics.services import SnapshotGenerator


class Command(BaseCommand):
    help = 'Refresh analytics dashboard snapshots'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dashboard-only',
            action='store_true',
            help='Only refresh dashboard overview snapshot',
        )
        parser.add_argument(
            '--skills-only',
            action='store_true',
            help='Only refresh skill demand snapshots',
        )
        parser.add_argument(
            '--categories-only',
            action='store_true',
            help='Only refresh job category snapshots',
        )
        parser.add_argument(
            '--salaries-only',
            action='store_true',
            help='Only refresh salary snapshots',
        )
        parser.add_argument(
            '--trends-only',
            action='store_true',
            help='Only refresh skill trend history',
        )

    def handle(self, *args, **options):
        generator = SnapshotGenerator()

        dashboard_only = options.get('dashboard_only')
        skills_only = options.get('skills_only')
        categories_only = options.get('categories_only')
        salaries_only = options.get('salaries_only')
        trends_only = options.get('trends_only')

        # If no specific flag, refresh all
        refresh_all = not any([
            dashboard_only, skills_only, categories_only,
            salaries_only, trends_only
        ])

        try:
            if refresh_all:
                self.stdout.write("Refreshing all analytics snapshots...")
                generator.refresh_all()
                self.stdout.write(
                    self.style.SUCCESS("All analytics snapshots refreshed successfully!")
                )
            else:
                if dashboard_only:
                    self.stdout.write("Refreshing dashboard snapshot...")
                    generator.refresh_dashboard_snapshot()
                    self.stdout.write(self.style.SUCCESS("Dashboard snapshot refreshed!"))

                if skills_only:
                    self.stdout.write("Refreshing skill demand snapshots...")
                    generator.refresh_skill_demand_snapshots()
                    self.stdout.write(self.style.SUCCESS("Skill demand snapshots refreshed!"))

                if categories_only:
                    self.stdout.write("Refreshing job category snapshots...")
                    generator.refresh_job_category_snapshots()
                    self.stdout.write(self.style.SUCCESS("Job category snapshots refreshed!"))

                if salaries_only:
                    self.stdout.write("Refreshing salary snapshots...")
                    generator.refresh_salary_snapshots()
                    self.stdout.write(self.style.SUCCESS("Salary snapshots refreshed!"))

                if trends_only:
                    self.stdout.write("Refreshing skill trend history...")
                    generator.refresh_skill_trend_history()
                    self.stdout.write(self.style.SUCCESS("Skill trend history refreshed!"))

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Error refreshing analytics: {e}")
            )
            raise
