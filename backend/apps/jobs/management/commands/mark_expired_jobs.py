"""
Mark expired/closed jobs as inactive.
Usage:
    python manage.py mark_expired_jobs
"""

from django.core.management.base import BaseCommand
from apps.jobs.models import JobPosting
from services.hh_api_client import HHAPIClient


class Command(BaseCommand):
    help = 'Bulk-deactivate jobs no longer listed on HH API (efficient set comparison)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be deactivated, without updating the DB',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        source = 'hh.uz'
        api_client = HHAPIClient(host='hh.uz')

        # 1. Fetch all active job IDs from the API (NO period filter)
        self.stdout.write("Fetching all active IT job IDs from HH API (no period filter)...")
        api_active_ids = set()
        api_archived_ids = set()

        roles = api_client.IT_PROFESSIONAL_ROLES
        for i, role_id in enumerate(roles, 1):
            try:
                items = api_client.search_all_pages(
                    professional_role=[role_id],
                    period=None,  # No period filter — get ALL open jobs
                )
                for item in items:
                    job_id = str(item['id'])
                    if item.get('archived', False):
                        api_archived_ids.add(job_id)
                    else:
                        api_active_ids.add(job_id)

                self.stdout.write(
                    f"  Role [{i}/{len(roles)}]: +{len(items)} items "
                    f"(active: {len(api_active_ids)}, archived: {len(api_archived_ids)})"
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Role [{i}/{len(roles)}] error: {e}"))
                continue

        if not api_active_ids:
            self.stdout.write(self.style.ERROR(
                "\nGot 0 job IDs from API — something is wrong. Aborting to be safe."
            ))
            return

        self.stdout.write(
            f"\nAPI has {len(api_active_ids)} active + "
            f"{len(api_archived_ids)} archived IT jobs."
        )

        # 2. Get all active job IDs from the DB
        db_active = set(
            JobPosting.objects.filter(
                source=source,
                is_active=True,
            ).values_list('external_job_id', flat=True)
        )
        self.stdout.write(f"DB has  {len(db_active)} active jobs (source={source}).")

        # 3. Compare:
        #    a) DB jobs not in API at all → closed/removed
        #    b) DB jobs in API but archived → archived
        not_in_api = db_active - api_active_ids - api_archived_ids
        archived_in_api = db_active & api_archived_ids
        still_active = db_active & api_active_ids
        to_deactivate = not_in_api | archived_in_api

        self.stdout.write(f"\nStill active:       {len(still_active)}")
        self.stdout.write(f"Not in API:         {len(not_in_api)}")
        self.stdout.write(f"Archived in API:    {len(archived_in_api)}")
        self.stdout.write(f"Total to deactivate: {len(to_deactivate)}")

        if not to_deactivate:
            self.stdout.write(self.style.SUCCESS("\nAll DB jobs are still listed on the API!"))
            return

        # Show some examples
        sample = list(to_deactivate)[:20]
        sample_jobs = JobPosting.objects.filter(
            external_job_id__in=sample
        ).values_list('external_job_id', 'job_title', 'company_name')

        self.stdout.write("\nSample of jobs to deactivate:")
        for ext_id, title, company in sample_jobs:
            label = "[archived]" if ext_id in archived_in_api else "[not in API]"
            self.stdout.write(self.style.WARNING(f"  {ext_id} — {title} ({company}) {label}"))

        if len(to_deactivate) > 20:
            self.stdout.write(f"  ... and {len(to_deactivate) - 20} more")

        # 4. Apply or dry-run
        if dry_run:
            self.stdout.write(self.style.NOTICE(
                f"\n[DRY RUN] Would deactivate {len(to_deactivate)} jobs. "
                f"Run without --dry-run to apply."
            ))
        else:
            updated = JobPosting.objects.filter(
                source=source,
                external_job_id__in=to_deactivate,
            ).update(is_active=False, listing_status=JobPosting.ListingStatus.ARCHIVED)
            self.stdout.write(self.style.SUCCESS(
                f"\nDeactivated {updated} jobs."
            ))

