"""
Extraction Service
==================
Wraps the existing scraping pipeline with ExtractionRun tracking
and full-batch atomic transactions.

Deactivation strategy (efficient):
  1. Fetch ALL active IT job IDs from HH API (~13 paginated calls)
  2. Compare with DB active job IDs
  3. Jobs in DB but NOT in API → mark is_active=False (single bulk update)
"""

import logging
from datetime import date, timedelta

from django.db import transaction, IntegrityError
from django.utils import timezone

from apps.jobs.models import ExtractionRun, JobPosting
from apps.jobs.scrapers.hh_api_client import HHAPIClient
from apps.jobs.scrapers.enhanced_skill_extractor import EnhancedSkillExtractor
from apps.jobs.scrapers.data_transformer import DataTransformer
from apps.jobs.utils.db_loader import DatabaseLoader

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Orchestrates a single extraction run with tracking and atomicity.
    """

    def __init__(self, source='hh.uz'):
        self.source = source

    def run(self, run_date: date = None, trigger: str = 'scheduled',
            full: bool = False) -> ExtractionRun:
        """
        Execute a full extraction for the given date.

        1. Claim the run via unique constraint (source, run_date).
        2. Search HH API for jobs posted since the last successful run.
        3. Process and load all vacancies in a single atomic block.
        4. Bulk-deactivate DB jobs no longer listed on API.
        5. Update ExtractionRun with stats.

        Args:
            full: If True, use period=None to fetch ALL open vacancies
                  (backfill mode). Otherwise, use incremental period.
        """
        run_date = run_date or timezone.localdate()

        # Step 1: Claim the run (duplicate guard)
        extraction_run = self._claim_run(run_date, trigger)
        if extraction_run is None:
            logger.info(f"Run already exists for {self.source}/{run_date}, skipping.")
            return ExtractionRun.objects.get(
                source=self.source, run_date=run_date
            )

        try:
            extraction_run.status = 'running'
            extraction_run.started_at = timezone.now()
            extraction_run.save(update_fields=['status', 'started_at'])

            # Step 2: Determine search period
            if full:
                period = None
                logger.info(
                    f"Starting FULL extraction for {self.source}/{run_date} "
                    f"(no period filter — all open vacancies)"
                )
            else:
                date_from = self._get_date_from(run_date)
                period = max((run_date - date_from).days, 1)
                logger.info(
                    f"Starting extraction for {self.source}/{run_date}, "
                    f"period={period} days (since {date_from})"
                )

            # Step 3: Search, process, load (atomic)
            stats = self._execute_pipeline(period=period)

            # Step 4: Bulk deactivation — compare API listing vs DB
            deactivated = self._bulk_deactivate_missing_jobs()

            # Step 5: Record success
            extraction_run.status = 'success'
            extraction_run.finished_at = timezone.now()
            extraction_run.jobs_created = stats.get('jobs_created', 0)
            extraction_run.jobs_updated = stats.get('jobs_updated', 0)
            extraction_run.jobs_skipped = stats.get('jobs_skipped', 0)
            extraction_run.jobs_deactivated = deactivated
            extraction_run.aliases_created = stats.get('aliases_created', 0)
            extraction_run.errors_count = stats.get('errors', 0)
            extraction_run.save()

            logger.info(
                f"Extraction success: created={stats.get('jobs_created', 0)}, "
                f"updated={stats.get('jobs_updated', 0)}, "
                f"deactivated={deactivated}"
            )
            return extraction_run

        except Exception as exc:
            extraction_run.status = 'failed'
            extraction_run.finished_at = timezone.now()
            extraction_run.error_message = str(exc)[:2000]
            extraction_run.save()
            logger.exception(f"Extraction failed for {run_date}")
            raise

    def _claim_run(self, run_date, trigger):
        """
        Attempt to create an ExtractionRun row.
        Returns the instance on success, None if duplicate.
        """
        try:
            return ExtractionRun.objects.create(
                source=self.source,
                run_date=run_date,
                status='pending',
                trigger=trigger,
            )
        except IntegrityError:
            return None

    def _get_date_from(self, run_date):
        """
        Find the date of the last successful extraction.
        Falls back to (run_date - 1 day) for daily runs.
        """
        last_success = (
            ExtractionRun.objects
            .filter(source=self.source, status='success', run_date__lt=run_date)
            .order_by('-run_date')
            .values_list('run_date', flat=True)
            .first()
        )
        if last_success:
            return last_success
        return run_date - timedelta(days=1)

    def _execute_pipeline(self, period: int) -> dict:
        """
        Run the scraping pipeline inside a single atomic transaction.
        Re-uses existing components.
        """
        api_client = HHAPIClient(host='hh.uz')
        skill_extractor = EnhancedSkillExtractor(use_ollama=False)
        data_transformer = DataTransformer()
        db_loader = DatabaseLoader()

        # Search all IT roles (bypass 2000-result limit)
        vacancy_items = self._search_all_roles(api_client, period)

        if not vacancy_items:
            logger.info("No vacancy items found.")
            return db_loader.get_stats()

        logger.info(f"Found {len(vacancy_items)} unique vacancy items.")

        # Process vacancies (fetch details + extract skills)
        vacancies_with_skills = self._process_vacancies(
            api_client, skill_extractor, data_transformer, vacancy_items
        )

        logger.info(f"Processed {len(vacancies_with_skills)} valid vacancies.")

        if not vacancies_with_skills:
            return db_loader.get_stats()

        # Load entire batch atomically
        with transaction.atomic():
            stats = db_loader.load_batch(vacancies_with_skills)

        return stats

    def _search_all_roles(self, api_client, period):
        """Search each IT role separately (bypass 2000-result limit)."""
        all_items = {}
        roles = api_client.IT_PROFESSIONAL_ROLES

        for i, role_id in enumerate(roles, 1):
            try:
                items = api_client.search_all_pages(
                    professional_role=[role_id],
                    period=period,
                )
                for item in items:
                    all_items[item['id']] = item

                if items:
                    logger.debug(
                        f"Role [{i}/{len(roles)}] {role_id}: "
                        f"{len(items)} items (total unique: {len(all_items)})"
                    )
            except Exception as e:
                logger.error(f"Error searching role {role_id}: {e}")
                continue

        return list(all_items.values())

    def _process_vacancies(self, api_client, skill_extractor,
                           data_transformer, vacancy_items):
        """Fetch full details, extract skills, transform."""
        results = []

        for i, item in enumerate(vacancy_items, 1):
            try:
                full = api_client.get_vacancy(item['id'])

                if not api_client.is_it_role(full.get('professional_roles', [])):
                    continue

                skills = skill_extractor.extract_skills_from_vacancy(full)
                for s in skills:
                    skill_extractor.track_skill_frequency(s['skill_text'])

                data = data_transformer.transform_vacancy(full)
                if not data_transformer.validate_vacancy_data(data):
                    continue

                data['skills'] = skills
                results.append(data)

                if i % 50 == 0:
                    logger.info(f"Processed {i}/{len(vacancy_items)} vacancies...")

            except Exception as e:
                logger.error(f"Error processing vacancy {item['id']}: {e}")
                continue

        return results

    def _bulk_deactivate_missing_jobs(self) -> int:
        """
        Efficient deactivation: fetch ALL active job IDs from the API
        via paginated search (NO period filter = all open jobs), then
        compare with the DB. Jobs in DB but not in API → deactivate.
        Jobs in API with archived=true → also deactivate.

        Returns:
            Number of jobs deactivated.
        """
        api_client = HHAPIClient(host='hh.uz')

        # 1. Fetch all currently listed IT job IDs from the API
        #    period=None → no date filter → returns ALL open vacancies
        logger.info("Fetching all active job IDs from API for deactivation check...")
        api_active_ids = set()
        api_archived_ids = set()

        for role_id in api_client.IT_PROFESSIONAL_ROLES:
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
            except Exception as e:
                logger.error(f"Error fetching role {role_id} for deactivation: {e}")
                continue

        if not api_active_ids:
            logger.warning("Got 0 job IDs from API — skipping deactivation to be safe.")
            return 0

        logger.info(
            f"API returned {len(api_active_ids)} active + "
            f"{len(api_archived_ids)} archived job IDs."
        )

        # 2. Get all active job external IDs from the DB
        db_active = set(
            JobPosting.objects.filter(
                source=self.source,
                is_active=True,
            ).values_list('external_job_id', flat=True)
        )

        logger.info(f"DB has {len(db_active)} active jobs for source '{self.source}'.")

        # 3. Jobs to deactivate:
        #    a) In DB but NOT in API at all (removed/closed)
        #    b) In DB AND in API but archived=true
        not_in_api = db_active - api_active_ids - api_archived_ids
        archived_in_api = db_active & api_archived_ids
        to_deactivate = not_in_api | archived_in_api

        if to_deactivate:
            logger.info(
                f"Deactivating {len(to_deactivate)} jobs "
                f"({len(not_in_api)} not in API, {len(archived_in_api)} archived)."
            )

        if not to_deactivate:
            logger.info("All DB jobs are still active on the API.")
            return 0

        # 4. Bulk update in one query
        deactivated = JobPosting.objects.filter(
            source=self.source,
            external_job_id__in=to_deactivate,
        ).update(is_active=False)

        logger.info(f"Deactivated {deactivated} jobs no longer listed on API.")
        return deactivated

    @staticmethod
    def can_retry(run_date: date, source: str = 'hh.uz') -> bool:
        """Check if a failed run exists that can be retried."""
        return ExtractionRun.objects.filter(
            source=source, run_date=run_date, status='failed'
        ).exists()

    @staticmethod
    def retry(run_date: date, source: str = 'hh.uz'):
        """
        Delete the failed run and re-execute.
        Clears the unique constraint so run() can proceed.
        """
        ExtractionRun.objects.filter(
            source=source, run_date=run_date, status='failed'
        ).delete()
        service = ExtractionService(source=source)
        return service.run(run_date=run_date, trigger='manual')
