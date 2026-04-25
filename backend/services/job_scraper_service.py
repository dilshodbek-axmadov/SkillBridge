"""
Consolidated HH job scraping service.

This module merges the jobs app scraping pipeline components into a single,
project-level service module while preserving existing behavior.

Merged from:
  - backend/apps/jobs/extraction_service.py
  - backend/apps/jobs/scrapers/data_transformer.py
  - backend/apps/jobs/scrapers/enhanced_skill_extractor.py
  - backend/apps/jobs/utils/db_loader.py
"""

import logging
from datetime import date, timedelta

from django.db import transaction, IntegrityError
from django.utils import timezone

from apps.jobs.models import ExtractionRun, JobPosting
from services.hh_api_client import HHAPIClient

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
            stats = self._execute_pipeline(period=period) or {}

            # Step 4: Bulk deactivation — compare API listing vs DB
            deactivated = self._bulk_deactivate_missing_jobs()

            # Phase B: Resolve aliases -> canonical skills
            resolution_stats = {}
            try:
                logger.info("Starting Phase B: Skill resolution...")
                from apps.skills.utils.skill_resolver import SkillResolver

                resolver = SkillResolver(
                    auto_resolve_threshold=0.95,
                    fuzzy_match_threshold=0.85,
                    use_ai_translation=False,  # AI disabled; dictionary only
                )
                resolution_stats = resolver.resolve_all_unresolved()
                logger.info(
                    f"Resolution complete: auto_resolved={resolution_stats.get('auto_resolved', 0)}, "
                    f"new_skills={resolution_stats.get('new_skills_created', 0)}, "
                    f"needs_review={resolution_stats.get('needs_review', 0)}"
                )
            except Exception as e:
                # Do not fail Phase A run if Phase B fails.
                logger.exception(f"Phase B failed (continuing): {e}")

            # Phase C: Link jobs -> canonical skills
            linking_stats = {}
            try:
                logger.info("Starting Phase C: Job-skill linking...")
                from apps.skills.utils.job_skill_linker import JobSkillLinker

                linker = JobSkillLinker()
                linking_stats = linker.link_all_jobs()
                logger.info(
                    f"Linking complete: jobs_processed={linking_stats.get('jobs_processed', 0)}, "
                    f"links_created={linking_stats.get('job_skills_created', 0)}"
                )
            except Exception as e:
                # Do not fail Phase A run if Phase C fails.
                logger.exception(f"Phase C failed (continuing): {e}")

            # Store combined stats for logging/observability.
            stats['resolution_stats'] = resolution_stats
            stats['linking_stats'] = linking_stats

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
        ).update(is_active=False, listing_status=JobPosting.ListingStatus.ARCHIVED)

        logger.info(f"Deactivated {deactivated} jobs no longer listed on API.")
        return deactivated

    @staticmethod
    def can_retry(run_date: date, source: str = 'hh.uz') -> bool:
        """Check if a failed run exists that can be retried."""
        return ExtractionRun.objects.filter(
            source=source, run_date=run_date, status='failed'
        ).exists()

    @staticmethod
    def retry(run_date: date, source: str = 'hh.uz', full: bool = False):
        """
        Delete the failed run and re-execute.
        Clears the unique constraint so run() can proceed.
        """
        ExtractionRun.objects.filter(
            source=source, run_date=run_date, status='failed'
        ).delete()
        service = ExtractionService(source=source)
        return service.run(run_date=run_date, trigger='manual', full=full)


"""
Data Transformer (SIMPLIFIED - No Section Extraction)
=====================================================
backend/apps/jobs/scrapers/data_transformer.py

Transforms HH.uz API responses to database format.
Requirements/responsibilities stay in job_description.
"""

import re
import html
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal


class DataTransformer:
    """Transforms API data to database model format."""

    def transform_vacancy(self, api_data: Dict) -> Dict:
        """
        Transform API vacancy to JobPosting model format.

        Args:
            api_data: Full vacancy dict from HH API

        Returns:
            Dict ready for JobPosting.objects.create()
        """

        # Detect language
        original_language = self._detect_language(api_data.get('name', ''))

        # Basic fields
        transformed = {
            'external_job_id': str(api_data['id']),
            'source': 'hh.uz',
            'original_language': original_language,

            # Job info
            'job_title': api_data.get('name', '').strip(),
            'company_name': self._get_company_name(api_data),
            'job_category': self._get_job_category(api_data),

            # Description (keep as-is, no extraction)
            'job_description': self._clean_description(api_data.get('description', '')),

            # Experience & employment
            'experience_required': self._map_experience(api_data.get('experience')),
            'employment_type': self._map_employment(api_data.get('employment')),

            # Salary
            'salary_min': self._get_salary_min(api_data.get('salary')),
            'salary_max': self._get_salary_max(api_data.get('salary')),
            'salary_currency': self._get_salary_currency(api_data.get('salary')),

            # Location
            'location': self._get_location(api_data.get('area')),
            'is_remote': self._is_remote(api_data),

            # Dates
            'posted_date': self._parse_date(api_data.get('published_at')),
            'deadline_date': None,  # HH doesn't provide this

            # Meta
            'job_url': api_data.get('alternate_url', ''),
            'is_active': (
                is_live := (
                    not api_data.get('closed_for_applicants', False)
                    and not api_data.get('archived', False)
                )
            ),
            'listing_status': 'active' if is_live else 'archived',
        }

        return transformed

    def _get_company_name(self, api_data: Dict) -> str:
        """Extract company name."""
        employer = api_data.get('employer', {})
        if employer:
            return employer.get('name', '').strip()
        return ''

    def _get_job_category(self, api_data: Dict) -> str:
        """Extract job category from professional_roles."""
        roles = api_data.get('professional_roles', [])
        if roles:
            return roles[0].get('name', '').strip()
        return ''

    def _map_experience(self, experience: Optional[Dict]) -> str:
        """
        Map HH experience to our choices.

        HH values: noExperience, between1And3, between3And6, moreThan6
        Our values: no_experience, junior, mid, senior
        """
        if not experience:
            return ''

        exp_id = experience.get('id', '')

        mapping = {
            'noExperience': 'no_experience',
            'between1And3': 'junior',
            'between3And6': 'mid',
            'moreThan6': 'senior',
        }

        return mapping.get(exp_id, '')

    def _map_employment(self, employment: Optional[Dict]) -> str:
        """
        Map HH employment to our choices (FIXED).

        HH values: full, part, project, volunteer, probation
        Our values: full_time, part_time, contract, project
        """
        if not employment:
            logger.debug("No employment field, defaulting to full_time")
            return 'full_time'

        emp_id = employment.get('id', '')

        if not emp_id:
            logger.debug("Empty employment id, defaulting to full_time")
            return 'full_time'

        # Mapping according to HH.uz API documentation
        mapping = {
            'full': 'full_time',        # Полная занятость
            'part': 'part_time',        # Частичная занятость
            'project': 'project',       # Проектная работа
            'volunteer': 'part_time',   # Волонтерство → part_time
            'probation': 'full_time',   # Стажировка → full_time
        }

        result = mapping.get(emp_id, 'full_time')
        logger.debug(f"Mapped employment '{emp_id}' → '{result}'")

        return result

    def _get_salary_min(self, salary: Optional[Dict]) -> Optional[Decimal]:
        """Extract minimum salary."""
        if not salary:
            return None

        salary_from = salary.get('from')
        if salary_from:
            return Decimal(str(salary_from))

        return None

    def _get_salary_max(self, salary: Optional[Dict]) -> Optional[Decimal]:
        """Extract maximum salary."""
        if not salary:
            return None

        salary_to = salary.get('to')
        if salary_to:
            return Decimal(str(salary_to))

        return None

    def _get_salary_currency(self, salary: Optional[Dict]) -> str:
        """Extract salary currency."""
        if not salary:
            return 'UZS'

        return salary.get('currency', 'UZS')

    def _get_location(self, area: Optional[Dict]) -> str:
        """Extract location/city name."""
        if not area:
            return ''

        return area.get('name', '').strip()

    def _is_remote(self, api_data: Dict) -> bool:
        """Check if job is remote."""
        # Check schedule field
        schedule = api_data.get('schedule', {})
        if schedule:
            schedule_id = schedule.get('id', '')
            if schedule_id in ['remote', 'flexible']:
                return True

        # Check address
        address = api_data.get('address')
        if address is None:
            return True

        return False

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse ISO 8601 date string.

        Example: "2026-01-21T17:39:52+0300"
        """
        if not date_str:
            return None

        try:
            # Remove timezone info for simplicity
            date_str = date_str.split('+')[0].split('T')
            date_part = date_str[0]
            time_part = date_str[1] if len(date_str) > 1 else "00:00:00"

            return datetime.strptime(
                f"{date_part} {time_part}",
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception as e:
            logger.error(f"Date parse error: {e}")
            return None

    def _detect_language(self, text: str) -> str:
        """
        Detect language from text.

        Returns:
            'ru', 'uz', or 'en'
        """
        if not text:
            return 'ru'  # Default for HH.uz

        # Check for Cyrillic
        cyrillic_count = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF)

        if cyrillic_count > 0:
            return 'ru'  # Most HH.uz jobs are in Russian

        return 'en'

    def _clean_description(self, html_text: str) -> str:
        """
        Clean HTML description to pure readable text.

        Properly handles:
        1. Unicode escapes (\u003C → <)
        2. HTML entities (&lt; → <)
        3. HTML tags removal
        4. Formatting preservation
        """
        if not html_text:
            return ""

        # Step 1: Decode unicode escapes (\u003C → <, \u003E → >)
        # Use regex to only decode \uXXXX patterns, preserving Cyrillic text
        def decode_unicode_escape(match):
            try:
                return chr(int(match.group(1), 16))
            except ValueError:
                return match.group(0)

        html_text = re.sub(r'\\u([0-9a-fA-F]{4})', decode_unicode_escape, html_text)

        # Step 2: Decode HTML entities (&lt; → <, &gt; → >, &nbsp; → space)
        html_text = html.unescape(html_text)

        # Step 3: Replace block-level tags with newlines for readability
        # Paragraphs
        html_text = re.sub(r'<p[^>]*>', '\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</p>', '\n', html_text, flags=re.IGNORECASE)

        # Line breaks
        html_text = re.sub(r'<br\\s*/?>', '\n', html_text, flags=re.IGNORECASE)

        # List items
        html_text = re.sub(r'<li[^>]*>', '\n• ', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</li>', '', html_text, flags=re.IGNORECASE)

        # Headings (add extra newline before)
        html_text = re.sub(r'<h[1-6][^>]*>', '\n\n', html_text, flags=re.IGNORECASE)
        html_text = re.sub(r'</h[1-6]>', '\n', html_text, flags=re.IGNORECASE)

        # Step 4: Remove ALL remaining HTML tags
        html_text = re.sub(r'<[^>]+>', '', html_text)

        # Step 5: Clean up whitespace
        # Replace multiple spaces with single space
        html_text = re.sub(r' +', ' ', html_text)

        # Split into lines and clean each
        lines = []
        for line in html_text.split('\n'):
            line = line.strip()
            if line:  # Only keep non-empty lines
                lines.append(line)

        # Join with single newlines
        clean_text = '\n'.join(lines)

        # Limit consecutive newlines to max 2
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

        return clean_text.strip()

    def validate_vacancy_data(self, data: Dict) -> bool:
        """
        Validate required fields are present.

        Args:
            data: Transformed vacancy data

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'external_job_id',
            'job_title',
            'posted_date',
            'job_url',
        ]

        for field in required_fields:
            if not data.get(field):
                logger.warning(f"Missing required field: {field}")
                return False

        return True


"""
Enhanced Skill Extractor
========================
backend/apps/jobs/scrapers/enhanced_skill_extractor.py

Extracts skills from job postings with hybrid approach.
Creates canonical skills and aliases automatically.
"""

import json
from typing import List, Dict
from collections import Counter


class EnhancedSkillExtractor:
    """
    Hybrid skill extractor:
    1. Try key_skills field first (official)
    2. If empty, extract from description using LLM or regex
    3. Return skill data ready for Skill/SkillAlias creation
    """

    def __init__(self, use_ollama: bool = False):
        """
        Initialize extractor.

        Args:
            use_ollama: Whether to use Ollama for extraction
        """
        self.use_ollama = use_ollama
        self.skill_frequency = Counter()

        # Expanded multilingual skill patterns for regex fallback.
        self.skill_patterns = [
            # English tech terms - exact word boundary matches
            r'\b(Python|Java(?:Script)?|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|R|Dart|Bash|Shell|PowerShell)\b',
            r'\b(React(?:\.js)?|Vue(?:\.js)?|Angular|Django|Flask|FastAPI|Spring(?:\s?Boot)?|Laravel|Express(?:\.js)?|Next\.js|Node\.js|NestJS|Flutter)\b',
            r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Oracle|MS\s?SQL|SQLite|ClickHouse|Cassandra|DynamoDB|Firebase)\b',
            r'\b(Power\s?BI|Tableau|Metabase|Superset|Looker|Qlik(?:View|Sense)?|Google\s?Analytics|GA4|Grafana)\b',
            r'\b(AWS|Azure|GCP|Google\s?Cloud|Docker|Kubernetes|K8s|Terraform|Ansible|Jenkins|GitLab\s?CI|GitHub\s?Actions)\b',
            r'\b(Git|Linux|Nginx|RabbitMQ|Celery|Kafka|Airflow|Spark|Hadoop|dbt|Pandas|NumPy|Scikit[\-\s]?learn|TensorFlow|PyTorch)\b',
            r'\b(SQL|HTML|CSS|SASS|GraphQL|REST(?:\s?API)?|gRPC|JSON|XML|YAML)\b',
            r'\b(Figma|Sketch|Adobe\s?XD|Photoshop|Illustrator|Jira|Confluence|Trello|Notion|Slack|Excel|Word)\b',
            r'\b(Agile|Scrum|Kanban|DevOps|CI/?CD|TDD|BDD|OOP|SOLID|MVC|MVVM|Microservices)\b',
            r'\b(Postman|Swagger|DBeaver|DataGrip|VS\s?Code|PyCharm|IntelliJ|Android\s?Studio|Xcode)\b',
            r'\b(SSRS|Report\s?Builder|Power\s?Query|Power\s?Automate|Tableau|1C)\b',
            r'\b(A/B[\s\-]?тест(?:ирование)?|A/B[\s\-]?test(?:ing)?)\b',

            # Russian skill patterns - match Cyrillic skill names from job descriptions
            r'\b(SQL|BI|API|REST|Git|Linux|Docker|Excel|Power\s?BI)\b',  # mixed-language terms common in RU text
            r'(?:знание|опыт работы с|владение|навыки?|использование)\s+([A-Za-z][A-Za-z0-9\s\.\+\#]{1,30})',  # "знание Python", "опыт работы с Docker"
            r'\b(аналитик(?:а|и)?(?:\s+данных)?|визуализаци(?:я|и)\s+данных|анализ\s+данных|бизнес[\-\s]анализ)\b',
            r'\b(машинное\s+обучение|глубокое\s+обучение|нейронн(?:ые|ая)\s+сет(?:и|ь)|обработка\s+данных)\b',
            r'\b(управление\s+проектами|управление\s+продуктом|постановка\s+задач|технические\s+требования)\b',
        ]

    def extract_skills_from_vacancy(self, vacancy_data: Dict) -> List[Dict]:
        """
        Main extraction method - hybrid approach.

        Returns list of dicts ready for database:
        [
            {
                'skill_text': 'Python',
                'language_code': 'en',
                'importance': 'core',
                'source': 'hh.uz'
            },
            ...
        ]
        """

        # Step 1: Try key_skills field
        key_skills = self._extract_from_key_skills(vacancy_data)

        # Step 2: If empty, extract from description
        if not key_skills:
            logger.debug(f"key_skills empty for {vacancy_data.get('id')}, using description")
            return self._extract_from_description(vacancy_data)

        # Step 3: If key_skills is minimal, combine both
        elif len(key_skills) < 3:
            description_skills = self._extract_from_description(vacancy_data)
            return self._merge_skills(key_skills, description_skills)

        return key_skills

    def _extract_from_key_skills(self, vacancy_data: Dict) -> List[Dict]:
        """Extract from key_skills field (official)."""
        key_skills = vacancy_data.get('key_skills', [])

        if not key_skills:
            return []

        extracted = []
        for skill_obj in key_skills:
            skill_name = skill_obj.get('name', '').strip()
            if skill_name:
                extracted.append({
                    'skill_text': skill_name,
                    'language_code': self._detect_language(skill_name),
                    'importance': 'core',
                    'source': 'hh.uz',
                })

        logger.debug(f"Extracted {len(extracted)} skills from key_skills")
        return extracted

    def _extract_from_description(self, vacancy_data: Dict) -> List[Dict]:
        """Extract from description using LLM or regex."""
        # Combine text fields
        text_parts = []

        if vacancy_data.get('name'):
            text_parts.append(vacancy_data['name'])

        if vacancy_data.get('description'):
            desc = self._strip_html(vacancy_data['description'])
            text_parts.append(desc)

        full_text = ' '.join(text_parts)

        if not full_text.strip():
            return []

        # Try LLM extraction
        if self.use_ollama:
            try:
                skills = self._extract_with_llm(full_text)
                if skills:
                    return skills
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, falling back to regex")

        # Fallback: regex extraction
        return self._extract_with_regex(full_text)

    def _extract_with_llm(self, text: str) -> List[Dict]:
        """Extract skills using Ollama LLM."""
        logger.debug("LLM extraction disabled")
        return []

    def _extract_with_regex(self, text: str) -> List[Dict]:
        """Extract skills using regex patterns (fallback)."""
        found_skills = {}  # normalized_lower -> original_text (preserve best casing)

        for pattern in self.skill_patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
                for match in matches:
                    # re.findall returns strings or tuples depending on groups
                    skill_text = match if isinstance(match, str) else match[-1]
                    skill_text = skill_text.strip()
                    if len(skill_text) < 2:
                        continue
                    key = skill_text.lower()
                    if key not in found_skills:
                        found_skills[key] = skill_text
            except re.error:
                continue

        extracted = []
        for key, original in found_skills.items():
            lang = self._detect_language(original)
            extracted.append({
                'skill_text': original,
                'language_code': lang,
                'importance': 'secondary',
                'source': 'hh.uz',
            })

        logger.debug(f"Regex extracted {len(extracted)} skills")
        return extracted

    def _merge_skills(self, skills1: List[Dict], skills2: List[Dict]) -> List[Dict]:
        """Merge two skill lists, removing duplicates."""
        seen = set()
        merged = []

        # Add all skills, deduplicating by normalized text
        for skill in skills1 + skills2:
            normalized = skill['skill_text'].lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                merged.append(skill)

        return merged

    def _detect_language(self, text: str) -> str:
        """
        Detect language from text.

        Returns:
            'ru', 'uz', or 'en'
        """
        if not text:
            return 'en'

        # Check for Cyrillic characters
        cyrillic_count = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF)

        if cyrillic_count > 0:
            # Could be Russian or Uzbek, default to Russian
            return 'ru'

        return 'en'

    def _strip_html(self, html_text: str) -> str:
        """Remove HTML tags."""
        if not html_text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', html_text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def track_skill_frequency(self, skill_text: str):
        """Track skill frequency for demand analysis."""
        normalized = skill_text.lower().strip()
        self.skill_frequency[normalized] += 1

    def get_skill_stats(self) -> Dict:
        """Get skill extraction statistics."""
        return {
            'unique_skills': len(self.skill_frequency),
            'total_mentions': sum(self.skill_frequency.values()),
            'top_skills': self.skill_frequency.most_common(20),
        }


# Comprehensive skill categorization mappings
SKILL_CATEGORIES = {
    'programming_language': {
        'exact': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'csharp', 'c',
            'c #', 'php', 'ruby', 'go', 'golang', 'rust', 'swift', 'kotlin', 'scala', 'r',
            'perl', 'lua', 'haskell', 'erlang', 'elixir', 'clojure', 'f#', 'fsharp',
            'dart', 'groovy', 'objective-c', 'objectivec', 'cobol', 'fortran',
            'assembly', 'vba', 'delphi', 'pascal', 'matlab', 'julia', 'apex',
            'abap', 'pl/sql', 'plsql', 't-sql', 'tsql', 'solidity', 'move',
            'bash', 'shell', 'powershell', 'zsh', 'html', 'css', 'sass', 'scss', 'less',
            '1c', '1c programming', '1c configuration', 'xml', 'json', 'yaml', 'graphql'
        ],
        'contains': ['programming']
    },
    'library_or_package': {
        'exact': [
            'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly', 'bokeh',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'xgboost',
            'lightgbm', 'catboost', 'opencv', 'pillow', 'nltk', 'spacy', 'gensim',
            'transformers', 'huggingface', 'langchain', 'openai', 'anthropic',
            'selenium', 'beautifulsoup', 'scrapy', 'requests', 'httpx', 'aiohttp',
            'pytest', 'unittest', 'nose', 'mock', 'faker', 'factory_boy',
            'celery', 'dramatiq', 'rq', 'huey', 'apscheduler',
            'sqlalchemy', 'peewee', 'tortoise-orm', 'mongoengine', 'motor',
            'pydantic', 'marshmallow', 'attrs', 'dataclasses',
            'jwt', 'bcrypt', 'cryptography', 'passlib',
            'boto3', 'botocore', 's3fs', 'paramiko', 'fabric',
            'lodash', 'underscore', 'ramda', 'axios', 'fetch', 'jquery',
            'moment', 'dayjs', 'date-fns', 'luxon',
            'redux', 'mobx', 'zustand', 'recoil', 'jotai', 'valtio',
            'rxjs', 'ngrx', 'akita', 'ngxs',
            'styled-components', 'emotion', 'tailwindcss', 'material-ui', 'mui',
            'chakra-ui', 'ant-design', 'antd', 'bootstrap', 'bulma', 'semantic-ui',
            'three.js', 'threejs', 'd3', 'd3.js', 'chart.js', 'chartjs', 'echarts',
            'socket.io', 'ws', 'primus',
            'bloc', 'cubit', 'provider', 'riverpod', 'getx', 'mobx',
            'dio', 'http', 'chopper', 'retrofit',
            'hive', 'sharedpreferences', 'realm', 'objectbox', 'isar',
            'get_it', 'injectable', 'freezed', 'json_serializable',
            'spring-boot', 'spring-security', 'spring-data', 'spring-cloud',
            'hibernate', 'mybatis', 'jpa', 'jdbc',
            'lombok', 'mapstruct', 'gson', 'jackson', 'okhttp',
            'junit', 'testng', 'mockito', 'powermock', 'assertj',
            'log4j', 'slf4j', 'logback',
            'guava', 'apache-commons', 'commons-lang', 'commons-io',
            'newtonsoft', 'json.net', 'automapper', 'mediatr', 'fluentvalidation',
            'entity-framework', 'ef-core', 'dapper', 'npgsql',
            'xunit', 'nunit', 'mstest', 'moq', 'nsubstitute'
        ],
        'contains': ['sdk', 'library', 'package', 'module', 'plugin', 'extension']
    },
    'framework': {
        'exact': [
            'django', 'flask', 'fastapi', 'tornado', 'pyramid', 'bottle', 'falcon',
            'starlette', 'sanic', 'aiohttp', 'quart', 'litestar',
            'react', 'vue', 'vuejs', 'angular', 'angularjs', 'svelte', 'solid',
            'next.js', 'nextjs', 'nuxt', 'nuxtjs', 'gatsby', 'remix', 'astro',
            'express', 'expressjs', 'koa', 'hapi', 'fastify', 'nestjs', 'adonis',
            'spring', 'springboot', 'spring-boot', 'struts', 'jsf', 'vaadin', 'micronaut', 'quarkus',
            'laravel', 'symfony', 'codeigniter', 'yii', 'cakephp', 'zend', 'slim', 'lumen',
            'rails', 'ruby on rails', 'sinatra', 'hanami',
            'asp.net', 'aspnet', '.net', 'dotnet', '.net core', 'dotnet core', 'blazor', 'maui',
            'gin', 'echo', 'fiber', 'beego', 'revel', 'buffalo',
            'flutter', 'react-native', 'react native', 'ionic', 'xamarin', 'cordova', 'capacitor',
            'electron', 'tauri', 'qt', 'gtk', 'wxwidgets', 'tkinter',
            'unity', 'unreal', 'godot', 'cocos2d', 'phaser',
            'wordpress', 'drupal', 'joomla', 'magento', 'shopify', 'woocommerce',
            'strapi', 'directus', 'payload', 'keystone', 'sanity',
            'graphql', 'apollo', 'relay', 'hasura', 'prisma',
            'grpc', 'thrift', 'protobuf',
            'airflow', 'prefect', 'dagster', 'luigi', 'argo',
            'dbt', 'great-expectations', 'mlflow', 'kubeflow', 'metaflow'
        ],
        'contains': ['framework', '.js', 'js']
    },
    'database': {
        'exact': [
            'sql', 'postgresql', 'postgres', 'mysql', 'mariadb', 'sqlite', 'oracle',
            'mssql', 'ms sql', 'sql server', 'sqlserver',
            'mongodb', 'mongo', 'couchdb', 'couchbase', 'dynamodb', 'cosmosdb',
            'redis', 'memcached', 'hazelcast', 'ignite',
            'elasticsearch', 'elastic', 'opensearch', 'solr', 'algolia', 'meilisearch',
            'neo4j', 'arangodb', 'orientdb', 'janusgraph', 'neptune', 'tigergraph',
            'cassandra', 'scylladb', 'hbase', 'bigtable',
            'timescaledb', 'influxdb', 'questdb', 'clickhouse', 'druid', 'pinot',
            'cockroachdb', 'tidb', 'yugabytedb', 'vitess', 'planetscale',
            'firebase', 'firestore', 'supabase', 'appwrite', 'neon', 'turso',
            'snowflake', 'bigquery', 'redshift', 'synapse', 'athena', 'presto', 'trino',
            'duckdb', 'polars', 'datafusion'
        ],
        'contains': ['sql', 'database', 'db', 'nosql']
    },
    'data_engineering': {
        'exact': [
            'etl', 'elt', 'data pipeline', 'data warehouse', 'dwh', 'data lake',
            'spark', 'pyspark', 'databricks', 'delta lake', 'iceberg', 'hudi',
            'hadoop', 'hdfs', 'hive', 'pig', 'sqoop', 'flume', 'oozie',
            'kafka', 'kafka streams', 'ksqldb', 'confluent',
            'flink', 'storm', 'samza', 'beam', 'pulsar',
            'nifi', 'streamsets', 'talend', 'informatica', 'fivetran', 'airbyte', 'stitch',
            'dbt', 'dataform', 'sqlmesh',
            'great expectations', 'soda', 'monte carlo', 'data quality',
            'data modeling', 'dimensional modeling', 'star schema', 'snowflake schema',
            'data governance', 'data catalog', 'data lineage', 'metadata',
            'cdc', 'change data capture', 'debezium',
            'data orchestration', 'workflow orchestration',
            'lakehouse', 'data mesh', 'data fabric',
            'big data', 'data science', 'machine learning', 'ml', 'deep learning', 'dl',
            'ai', 'artificial intelligence', 'neural networks', 'nlp', 'computer vision',
            'data preprocessing', 'feature engineering', 'model training', 'mlops'
        ],
        'contains': ['etl', 'data engineer', 'data pipeline', 'warehouse', 'lakehouse', 'big data']
    },
    'cloud_platform': {
        'exact': [
            'aws', 'amazon web services', 'ec2', 's3', 'lambda', 'ecs', 'eks', 'fargate',
            'rds', 'aurora', 'dynamodb', 'elasticache', 'sqs', 'sns', 'kinesis',
            'cloudfront', 'route53', 'api gateway', 'cloudwatch', 'iam', 'cognito',
            'azure', 'microsoft azure', 'azure devops', 'azure functions', 'azure aks',
            'gcp', 'google cloud', 'google cloud platform', 'gke', 'cloud run', 'cloud functions',
            'bigquery', 'cloud storage', 'pub/sub', 'dataflow', 'composer',
            'digitalocean', 'linode', 'vultr', 'hetzner', 'ovh',
            'heroku', 'render', 'railway', 'fly.io', 'vercel', 'netlify', 'cloudflare',
            'alibaba cloud', 'aliyun', 'tencent cloud', 'huawei cloud', 'yandex cloud',
            'openstack', 'vmware', 'vsphere', 'vcenter', 'proxmox'
        ],
        'contains': ['aws', 'azure', 'gcp', 'cloud']
    },
    'devops_infrastructure': {
        'exact': [
            'docker', 'containerd', 'podman', 'buildah', 'kaniko', 'skopeo',
            'kubernetes', 'k8s', 'openshift', 'rancher', 'nomad',
            'helm', 'kustomize', 'argocd', 'argo cd', 'fluxcd', 'spinnaker',
            'terraform', 'terragrunt', 'pulumi', 'crossplane', 'cdktf',
            'ansible', 'puppet', 'chef', 'salt', 'saltstack',
            'packer', 'vagrant', 'cloud-init',
            'jenkins', 'gitlab ci', 'github actions', 'circleci', 'travis ci',
            'azure pipelines', 'bitbucket pipelines', 'teamcity', 'bamboo', 'drone',
            'nginx', 'apache', 'httpd', 'haproxy', 'traefik', 'envoy', 'istio', 'linkerd',
            'prometheus', 'grafana', 'datadog', 'new relic', 'splunk', 'elastic stack', 'elk',
            'jaeger', 'zipkin', 'opentelemetry', 'otel',
            'vault', 'consul', 'etcd', 'zookeeper',
            'linux', 'ubuntu', 'centos', 'rhel', 'debian', 'alpine', 'fedora', 'rocky linux',
            'systemd', 'cron', 'ssh', 'sftp', 'rsync',
            'ci/cd', 'cicd', 'continuous integration', 'continuous delivery', 'continuous deployment',
            'gitops', 'infrastructure as code', 'iac', 'configuration management',
            'site reliability', 'sre', 'platform engineering',
            'load balancing', 'auto scaling', 'high availability', 'disaster recovery'
        ],
        'contains': ['devops', 'infrastructure', 'deployment', 'container', 'orchestration']
    },
    'testing_qa': {
        'exact': [
            'unit testing', 'integration testing', 'e2e testing', 'end-to-end testing',
            'functional testing', 'regression testing', 'smoke testing', 'sanity testing',
            'acceptance testing', 'uat', 'user acceptance testing',
            'performance testing', 'load testing', 'stress testing', 'soak testing',
            'security testing', 'penetration testing', 'pentest', 'vulnerability testing',
            'api testing', 'contract testing', 'pact', 'consumer-driven contracts',
            'mutation testing', 'property-based testing', 'fuzzing', 'fuzz testing',
            'tdd', 'test-driven development', 'bdd', 'behavior-driven development',
            'jest', 'mocha', 'jasmine', 'karma', 'cypress', 'playwright', 'puppeteer',
            'selenium', 'webdriver', 'appium', 'detox', 'espresso', 'xcuitest',
            'junit', 'testng', 'mockito', 'pytest', 'unittest', 'robot framework',
            'postman', 'insomnia', 'httpie', 'curl',
            'jmeter', 'gatling', 'locust', 'k6', 'artillery', 'wrk', 'ab',
            'testrail', 'testlink', 'zephyr', 'xray', 'qtest', 'practitest',
            'qase', 'testmo', 'testomat', 'allure', 'reportportal',
            'sonarqube', 'sonar', 'codeclimate', 'codecov', 'coveralls',
            'quality assurance', 'qa', 'qc', 'quality control',
            'test automation', 'test management', 'test strategy', 'test plan',
            'defect tracking', 'bug tracking', 'issue tracking'
        ],
        'contains': ['testing', 'test', 'qa', 'quality']
    },
    'bi_analytics': {
        'exact': [
            'power bi', 'powerbi', 'tableau', 'looker', 'metabase', 'superset', 'redash',
            'qlik', 'qlikview', 'qliksense', 'sisense', 'mode', 'thoughtspot', 'domo',
            'google analytics', 'ga4', 'google tag manager', 'gtm', 'mixpanel', 'amplitude',
            'segment', 'heap', 'pendo', 'fullstory', 'hotjar', 'clarity',
            'data studio', 'looker studio', 'google data studio',
            'excel', 'google sheets', 'pivot tables', 'vlookup', 'xlookup',
            'data visualization', 'data analysis', 'business intelligence', 'bi',
            'reporting', 'dashboards', 'kpi', 'metrics', 'analytics',
            'a/b testing', 'ab testing', 'experimentation', 'optimizely', 'vwo',
            'attribution', 'funnel analysis', 'cohort analysis', 'retention analysis',
            'predictive analytics', 'descriptive analytics', 'prescriptive analytics',
            'statistical analysis', 'statistics', 'hypothesis testing', 'regression analysis',
            'sas', 'spss', 'stata', 'minitab', 'r studio', 'rstudio', 'jupyter'
        ],
        'contains': ['analytics', 'visualization', 'bi', 'reporting', 'dashboard']
    },
    'tools_software': {
        'exact': [
            'git', 'github', 'gitlab', 'bitbucket', 'svn', 'mercurial', 'perforce',
            'jira', 'confluence', 'trello', 'asana', 'monday', 'clickup', 'notion',
            'linear', 'height', 'shortcut', 'basecamp', 'wrike', 'smartsheet',
            'slack', 'discord', 'teams', 'microsoft teams', 'zoom', 'google meet',
            'vscode', 'visual studio', 'intellij', 'pycharm', 'webstorm', 'rider',
            'xcode', 'android studio', 'eclipse', 'netbeans', 'vim', 'neovim', 'emacs',
            'postman', 'insomnia', 'swagger', 'openapi', 'graphql playground',
            'dbeaver', 'datagrip', 'pgadmin', 'mongodb compass', 'redis insight',
            'charles', 'fiddler', 'wireshark', 'mitmproxy',
            'terminal', 'iterm', 'warp', 'alacritty', 'hyper',
            'ms office', 'microsoft office', 'word', 'powerpoint', 'outlook',
            'google workspace', 'g suite', 'google docs', 'google drive',
            'obsidian', 'roam', 'logseq', 'bear', 'apple notes', 'evernote',
            '1password', 'lastpass', 'bitwarden', 'dashlane',
            'loom', 'screen recording', 'obs', 'camtasia',
            'bitrix', 'bitrix24', 'bitrix 1c', 'amocrm', 'zoho',
            'chatgpt', 'ai tools', 'copilot', 'github copilot', 'cursor',
            'camunda', 'bizagi', 'bpmn tools',
            'arduino', 'raspberry pi', 'esp32', 'stm32', 'microcontroller',
            'anydesk', 'teamviewer', 'remote desktop',
            'cmake', 'make', 'gradle', 'maven', 'npm', 'yarn', 'pnpm', 'pip', 'poetry',
            'cocoapods', 'carthage', 'spm', 'swift package manager',
            'webpack', 'vite', 'rollup', 'parcel', 'esbuild', 'turbopack'
        ],
        'contains': ['tool', 'software', 'ide', 'editor']
    },
    'design_creative': {
        'exact': [
            'figma', 'sketch', 'adobe xd', 'xd', 'invision', 'framer', 'principle',
            'photoshop', 'illustrator', 'indesign', 'lightroom', 'after effects', 'premiere',
            'affinity designer', 'affinity photo', 'affinity publisher',
            'canva', 'miro', 'figjam', 'whimsical', 'lucidchart', 'draw.io',
            'blender', '3ds max', 'maya', 'cinema 4d', 'zbrush', 'substance',
            'autocad', 'solidworks', 'fusion 360', 'revit', 'sketchup',
            'ui design', 'ux design', 'ui/ux', 'user interface', 'user experience',
            'wireframing', 'prototyping', 'mockups', 'design systems', 'design tokens',
            'motion design', 'animation', 'motion graphics', 'video editing',
            'graphic design', 'visual design', 'brand design', 'logo design',
            'typography', 'color theory', 'composition', 'layout design',
            '3d modeling', '3d rendering', 'cad', 'product design', 'industrial design',
            'lottie', 'rive', 'spine', 'dragonbones'
        ],
        'contains': ['design', 'creative', 'adobe', '3d', 'animation', 'ux', 'ui']
    },
    'business_product_management': {
        'exact': [
            'product management', 'product owner', 'product strategy', 'product roadmap',
            'project management', 'program management', 'portfolio management',
            'pmp', 'prince2', 'pmbok', 'pmi', 'capm',
            'business analysis', 'business analyst', 'requirements gathering', 'requirements management',
            'bpmn', 'business process', 'process modeling', 'process improvement',
            'stakeholder management', 'change management', 'risk management',
            'okr', 'kpi', 'objectives and key results', 'goal setting',
            'market research', 'competitive analysis', 'swot', 'pest',
            'user research', 'customer research', 'user interviews', 'surveys',
            'personas', 'user stories', 'use cases', 'job stories', 'jtbd',
            'prioritization', 'rice', 'moscow', 'kano', 'weighted scoring',
            'roadmapping', 'sprint planning', 'backlog grooming', 'refinement',
            'go-to-market', 'gtm', 'product launch', 'mvp', 'minimum viable product',
            'product-led growth', 'plg', 'growth hacking', 'growth marketing',
            'saas', 'b2b', 'b2c', 'enterprise', 'startup',
            'six sigma', 'lean', 'lean startup', 'design thinking', 'design sprint',
            'branding', 'brand promotion', 'brand management', 'brand strategy',
            'btl', 'atl', 'advertising', 'marketing strategy', 'content strategy',
            'customer journey', 'cjm', 'customer experience', 'cx',
            'brd', 'prd', 'frd', 'srs', 'functional requirements', 'technical requirements',
            'budgeting', 'forecasting', 'financial planning', 'cost management',
            'vendor management', 'contract negotiation', 'procurement',
            'operations management', 'supply chain management', 'logistics management'
        ],
        'contains': ['product', 'management', 'business', 'strategy', 'roadmap', 'branding']
    },
    'security': {
        'exact': [
            'cybersecurity', 'information security', 'infosec', 'appsec', 'application security',
            'network security', 'cloud security', 'endpoint security', 'mobile security',
            'owasp', 'owasp top 10', 'secure coding', 'security best practices',
            'penetration testing', 'pentest', 'ethical hacking', 'red team', 'blue team',
            'vulnerability assessment', 'vulnerability management', 'cve', 'cvss',
            'siem', 'splunk', 'elk security', 'qradar', 'sentinel', 'chronicle',
            'soar', 'security orchestration', 'incident response', 'ir', 'dfir',
            'soc', 'security operations', 'threat hunting', 'threat intelligence',
            'malware analysis', 'reverse engineering', 'forensics', 'digital forensics',
            'encryption', 'cryptography', 'pki', 'ssl', 'tls', 'https', 'certificates',
            'iam', 'identity management', 'access management', 'sso', 'saml', 'oauth', 'oidc',
            'mfa', 'multi-factor authentication', '2fa', 'passwordless',
            'firewall', 'waf', 'ids', 'ips', 'nids', 'hids',
            'vpn', 'zero trust', 'ztna', 'sase', 'casb',
            'dlp', 'data loss prevention', 'data protection', 'gdpr', 'pci dss', 'hipaa', 'sox',
            'iso 27001', 'soc 2', 'nist', 'cis', 'security frameworks',
            'devsecops', 'security automation', 'security as code',
            'burp suite', 'nessus', 'qualys', 'nmap', 'metasploit', 'wireshark',
            'snyk', 'veracode', 'checkmarx', 'sonarqube', 'semgrep', 'trivy',
            'check point', 'checkpoint', 'kaspersky', 'symantec', 'mcafee', 'crowdstrike',
            'carbon black', 'sentinelone', 'defender', 'antivirus', 'edr', 'xdr',
            'kali linux', 'parrot os', 'ctf', 'capture the flag'
        ],
        'contains': ['security', 'cyber', 'encryption', 'firewall', 'vulnerability']
    },
    'networking': {
        'exact': [
            'tcp/ip', 'tcpip', 'tcp', 'ip', 'udp', 'icmp', 'arp',
            'dns', 'dhcp', 'http', 'https', 'ftp', 'sftp', 'ssh', 'telnet',
            'smtp', 'imap', 'pop3', 'snmp', 'ntp', 'syslog',
            'osi model', 'networking fundamentals', 'network protocols',
            'lan', 'wan', 'man', 'vlan', 'vxlan', 'mpls', 'sd-wan',
            'routing', 'switching', 'bgp', 'ospf', 'eigrp', 'rip', 'is-is',
            'cisco', 'ccna', 'ccnp', 'ccie', 'juniper', 'jncia', 'jncip',
            'arista', 'mikrotik', 'ubiquiti', 'unifi', 'fortinet', 'palo alto',
            'network administration', 'network engineering', 'network architecture',
            'load balancer', 'f5', 'nginx', 'haproxy', 'cdn', 'cloudflare',
            'wireless', 'wifi', 'wi-fi', '802.11', 'bluetooth', '5g', 'lte',
            'network monitoring', 'nagios', 'zabbix', 'prtg', 'cacti', 'netflow',
            'packet analysis', 'tcpdump', 'wireshark', 'network troubleshooting',
            'network security', 'firewall', 'acl', 'nat', 'pat', 'vpn', 'ipsec'
        ],
        'contains': ['network', 'cisco', 'routing', 'switching', 'tcp', 'dns', 'vlan']
    },
    'operating_system': {
        'exact': [
            'linux', 'unix', 'ubuntu', 'debian', 'centos', 'rhel', 'red hat',
            'fedora', 'arch linux', 'alpine', 'rocky linux', 'alma linux', 'suse', 'opensuse',
            'windows', 'windows server', 'windows 10', 'windows 11', 'active directory', 'ad',
            'macos', 'mac os', 'darwin', 'ios', 'ipados',
            'android', 'aosp', 'lineageos',
            'freebsd', 'openbsd', 'netbsd',
            'kernel', 'shell scripting', 'bash scripting', 'powershell scripting',
            'system administration', 'sysadmin', 'system engineering',
            'file systems', 'ext4', 'xfs', 'btrfs', 'zfs', 'ntfs', 'apfs',
            'process management', 'memory management', 'disk management',
            'virtualization', 'vmware', 'hyper-v', 'kvm', 'qemu', 'virtualbox',
            'containerization', 'lxc', 'lxd', 'cgroups', 'namespaces',
            'package management', 'apt', 'yum', 'dnf', 'pacman', 'brew', 'chocolatey'
        ],
        'contains': ['linux', 'windows', 'macos', 'unix', 'operating system', 'os admin']
    },
    'methodology_process': {
        'exact': [
            'agile', 'scrum', 'kanban', 'lean', 'xp', 'extreme programming',
            'safe', 'scaled agile', 'less', 'nexus', 'spotify model',
            'waterfall', 'v-model', 'spiral', 'incremental', 'iterative',
            'sdlc', 'software development lifecycle', 'devops', 'devsecops', 'gitops',
            'ci/cd', 'cicd', 'continuous integration', 'continuous delivery', 'continuous deployment',
            'tdd', 'test-driven development', 'bdd', 'behavior-driven development', 'atdd',
            'ddd', 'domain-driven design', 'clean architecture', 'hexagonal architecture',
            'microservices', 'monolith', 'soa', 'service-oriented', 'event-driven', 'cqrs', 'event sourcing',
            'oop', 'object-oriented', 'functional programming', 'fp', 'reactive programming',
            'solid', 'dry', 'kiss', 'yagni', 'grasp', 'design patterns',
            'code review', 'pair programming', 'mob programming', 'trunk-based development',
            'feature flags', 'feature toggles', 'a/b testing', 'canary deployment', 'blue-green',
            'documentation', 'technical writing', 'api design', 'system design',
            'refactoring', 'technical debt', 'legacy modernization',
            'sprint', 'retrospective', 'daily standup', 'planning poker', 'story points',
            'api', 'api development', 'rest', 'restful', 'rest api', 'soap',
            'backend development', 'frontend development', 'fullstack development', 'full-stack',
            'software architecture', 'architecture', 'system architecture', 'solution architecture',
            'code optimization', 'performance optimization', 'scalability',
            'mvc', 'mvvm', 'mvp', 'clean code', 'software design',
            'version control', 'branching strategy', 'git flow', 'github flow'
        ],
        'contains': ['agile', 'methodology', 'process', 'sdlc', 'development lifecycle', 'architecture']
    },
    'soft_skill': {
        'exact': [
            'communication', 'written communication', 'verbal communication', 'presentation',
            'leadership', 'team leadership', 'people management', 'mentoring', 'coaching',
            'teamwork', 'collaboration', 'cross-functional', 'remote collaboration',
            'problem solving', 'critical thinking', 'analytical thinking', 'logical thinking',
            'creativity', 'innovation', 'ideation', 'brainstorming',
            'time management', 'prioritization', 'organization', 'planning',
            'adaptability', 'flexibility', 'resilience', 'growth mindset',
            'attention to detail', 'accuracy', 'precision', 'thoroughness',
            'decision making', 'judgment', 'risk assessment', 'cost-benefit analysis',
            'conflict resolution', 'negotiation', 'mediation', 'diplomacy',
            'emotional intelligence', 'eq', 'empathy', 'self-awareness',
            'customer focus', 'client management', 'stakeholder communication',
            'public speaking', 'facilitation', 'training', 'knowledge sharing',
            'initiative', 'proactivity', 'self-motivation', 'ownership',
            'work ethic', 'reliability', 'accountability', 'integrity',
            'stress management', 'work-life balance', 'mindfulness',
            'networking', 'relationship building', 'influence',
            'analytical skills', 'analytical ability', 'analytical studies',
            'communicability', 'articulate speech', 'presentation skills',
            'client focus', 'client orientation', 'customer orientation',
            'attentiveness', 'diligence', 'punctuality', 'responsibility',
            'multitasking', 'multi-tasking', 'quick learner', 'fast learner',
            'desire to learn', 'learning ability', 'self-development',
            'patience', 'persistence', 'determination', 'motivation'
        ],
        'contains': ['communication', 'leadership', 'teamwork', 'interpersonal', 'skill']
    },
    'domain_specific': {
        'exact': [
            'accounting', 'bookkeeping', 'financial reporting', 'gaap', 'ifrs',
            'finance', 'financial analysis', 'financial modeling', 'valuation', 'dcf',
            'banking', 'investment banking', 'retail banking', 'fintech',
            'trading', 'algorithmic trading', 'quantitative finance', 'risk modeling',
            'insurance', 'actuarial', 'underwriting', 'claims processing',
            'healthcare', 'health informatics', 'hl7', 'fhir', 'hipaa', 'medical coding',
            'pharmaceutical', 'pharmacology', 'clinical trials', 'fda', 'gxp',
            'biotechnology', 'genomics', 'bioinformatics', 'drug discovery',
            'ecommerce', 'retail', 'pos', 'inventory management', 'supply chain',
            'logistics', 'transportation', 'fleet management', 'last mile',
            'manufacturing', 'mes', 'erp', 'mrp', 'lean manufacturing', 'six sigma',
            'real estate', 'property management', 'proptech', 'mls',
            'legal', 'legal tech', 'contract management', 'ediscovery', 'compliance',
            'education', 'edtech', 'lms', 'e-learning', 'curriculum design',
            'hr', 'human resources', 'hris', 'talent acquisition', 'payroll',
            'marketing', 'digital marketing', 'seo', 'sem', 'ppc', 'social media marketing',
            'sales', 'crm', 'salesforce', 'hubspot', 'pipedrive', 'sales ops',
            'gaming', 'game development', 'game design', 'game mechanics',
            'media', 'publishing', 'content management', 'cms', 'journalism',
            'telecommunications', 'telecom', '5g', 'voip', 'sip',
            'automotive', 'autonomous vehicles', 'adas', 'can bus', 'autosar',
            'aerospace', 'aviation', 'satellite', 'space tech',
            'energy', 'oil and gas', 'renewable energy', 'smart grid', 'utilities',
            'government', 'govtech', 'civic tech', 'public sector'
        ],
        'contains': ['industry', 'domain', 'sector', 'vertical']
    }
}


def categorize_skill(skill_text: str) -> str:
    """
    Auto-categorize skill based on comprehensive pattern matching.

    Args:
        skill_text: Skill name

    Returns:
        Category from SKILL_CATEGORIES keys
    """
    import re

    if not skill_text:
        return 'other'

    skill_lower = skill_text.lower().strip()
    # Normalize: remove dots, replace separators with spaces
    skill_normalized = skill_lower.replace('-', ' ').replace('_', ' ').replace('.', ' ')
    skill_normalized = ' '.join(skill_normalized.split())  # Normalize whitespace

    # First pass: exact matches only (highest priority)
    for category, patterns in SKILL_CATEGORIES.items():
        exact_patterns = patterns.get('exact', [])
        if skill_lower in exact_patterns or skill_normalized in exact_patterns:
            return category

    # Second pass: check if skill starts with or equals a known pattern
    # This handles cases like "Python 3", "React.js", "AWS S3"
    for category, patterns in SKILL_CATEGORIES.items():
        exact_patterns = patterns.get('exact', [])
        for pattern in exact_patterns:
            # Check if skill starts with pattern followed by space/number/version
            if len(pattern) >= 3:  # Only for patterns with 3+ chars
                if skill_normalized.startswith(pattern + ' ') or skill_normalized.startswith(pattern + '3'):
                    return category
                # Check if pattern is a complete word in the skill
                word_pattern = r'\b' + re.escape(pattern) + r'\b'
                if re.search(word_pattern, skill_normalized):
                    return category

    # Third pass: contains patterns (for suffix/keyword matching)
    for category, patterns in SKILL_CATEGORIES.items():
        contains_patterns = patterns.get('contains', [])
        for contains_pattern in contains_patterns:
            # Must be a complete word match, not a substring
            word_pattern = r'\b' + re.escape(contains_pattern) + r'\b'
            if re.search(word_pattern, skill_normalized):
                return category

    return 'other'


def get_category_display_name(category: str) -> str:
    """Get human-readable category name."""
    display_names = {
        'programming_language': 'Programming Language',
        'library_or_package': 'Library / Package',
        'framework': 'Framework',
        'database': 'Database',
        'data_engineering': 'Data Engineering',
        'cloud_platform': 'Cloud Platform',
        'devops_infrastructure': 'DevOps / Infrastructure',
        'testing_qa': 'Testing / QA',
        'bi_analytics': 'BI / Analytics',
        'tools_software': 'Tools / Software',
        'design_creative': 'Design / Creative',
        'business_product_management': 'Business / Product Management',
        'security': 'Security',
        'networking': 'Networking',
        'operating_system': 'Operating System',
        'methodology_process': 'Methodology / Process',
        'soft_skill': 'Soft Skill',
        'domain_specific': 'Domain Specific',
        'other': 'Other'
    }
    return display_names.get(category, 'Other')


"""
Database Loader (UPDATED - Phase A: Ingestion)
===============================================
backend/apps/jobs/utils/db_loader.py

Phase A: Raw skill extraction and storage
- Extract skills from jobs
- Store in skill_aliases with status='unresolved'
- Track job-alias mapping in job_skill_extractions
- Do NOT create canonical skills yet
"""

from typing import Tuple
from apps.skills.models import SkillAlias
from apps.jobs.models import JobSkillExtraction


class DatabaseLoader:
    """
    Phase A: Loads job postings and raw skill aliases.

    Workflow:
    1. Load job posting
    2. Extract raw skills → SkillAlias (unresolved)
    3. Track job-alias mapping → JobSkillExtraction
    4. Skills table remains untouched (resolution happens later)
    """

    def __init__(self):
        self.stats = {
            'jobs_created': 0,
            'jobs_updated': 0,
            'jobs_skipped': 0,
            'aliases_created': 0,
            'aliases_reused': 0,
            'extractions_created': 0,
            'errors': 0,
        }

    def load_vacancy(self, vacancy_data: Dict, skills_data: List[Dict]) -> Tuple[JobPosting, Dict]:
        """
        Load single vacancy with raw skill aliases.

        Args:
            vacancy_data: Transformed job data
            skills_data: List of skill dicts from extractor:
                [
                    {
                        'skill_text': 'Python',
                        'language_code': 'en',
                        'importance': 'core',
                        'source': 'hh.uz'
                    },
                    ...
                ]

        Returns:
            (JobPosting instance, stats dict)
        """
        stats = {
            'created': False,
            'updated': False,
            'aliases_created': 0,
            'aliases_reused': 0,
            'extractions_created': 0,
        }

        try:
            with transaction.atomic():
                # Step 1: Get or create job posting
                job, created = JobPosting.objects.update_or_create(
                    external_job_id=vacancy_data['external_job_id'],
                    defaults=vacancy_data
                )

                if created:
                    stats['created'] = True
                    logger.debug(f"✓ Created job: {job.job_title}")
                else:
                    stats['updated'] = True
                    logger.debug(f"↻ Updated job: {job.job_title}")

                # Step 2: Load raw skill aliases
                if skills_data:
                    alias_stats = self._ingest_raw_skills(job, skills_data)
                    stats.update(alias_stats)

                return job, stats

        except Exception as e:
            logger.error(f"Error loading vacancy {vacancy_data.get('external_job_id')}: {e}")
            raise

    def _ingest_raw_skills(self, job: JobPosting, skills_data: List[Dict]) -> Dict:
        """
        Phase A: Ingest raw skills into skill_aliases.

        DO NOT create canonical skills here!
        Just store raw strings with status='unresolved'.

        Args:
            job: JobPosting instance
            skills_data: List of extracted skills

        Returns:
            Stats dict
        """
        stats = {
            'aliases_created': 0,
            'aliases_reused': 0,
            'extractions_created': 0,
        }

        for skill_data in skills_data:
            try:
                skill_text = skill_data['skill_text'].strip()
                language_code = skill_data.get('language_code', 'en')
                importance = skill_data.get('importance', 'secondary')
                source = skill_data.get('source', 'hh.uz')

                if not skill_text:
                    continue

                # Get or create skill alias (unresolved)
                alias, alias_created = self._get_or_create_alias(
                    skill_text=skill_text,
                    language_code=language_code,
                    source=source
                )

                if alias_created:
                    stats['aliases_created'] += 1
                    logger.debug(f"  + New alias: {skill_text} ({language_code})")
                else:
                    stats['aliases_reused'] += 1
                    logger.debug(f"  ↻ Reused alias: {skill_text} ({language_code})")

                # Track job-alias mapping
                extraction, extraction_created = JobSkillExtraction.objects.get_or_create(
                    job_posting=job,
                    alias=alias,
                    defaults={'importance': importance}
                )

                if extraction_created:
                    stats['extractions_created'] += 1

            except Exception as e:
                logger.error(f"Error ingesting skill '{skill_data.get('skill_text')}': {e}")
                continue

        return stats

    def _get_or_create_alias(
        self,
        skill_text: str,
        language_code: str,
        source: str
    ) -> Tuple[SkillAlias, bool]:
        """
        Get or create SkillAlias (unresolved).

        Key points:
        - skill_id = NULL (not resolved yet)
        - status = 'unresolved'
        - If alias exists, increment usage_count

        Args:
            skill_text: Raw skill text
            language_code: 'en', 'ru', or 'uz'
            source: Where skill came from

        Returns:
            (SkillAlias instance, created)
        """

        # Try to find existing alias
        alias = SkillAlias.objects.filter(
            alias_text=skill_text,
            language_code=language_code,
            source=source
        ).first()

        if alias:
            # Increment usage count
            alias.usage_count += 1
            alias.save(update_fields=['usage_count'])
            return alias, False

        # Create new alias (unresolved)
        alias = SkillAlias.objects.create(
            skill=None,  # ← KEY: Not resolved yet
            alias_text=skill_text,
            language_code=language_code,
            source=source,
            status='unresolved',
            usage_count=1
        )

        return alias, True

    def load_batch(self, vacancies: List[Dict]) -> Dict:
        """
        Load batch of vacancies.

        Args:
            vacancies: List of vacancy dicts, each with 'skills' key

        Returns:
            Overall statistics dict
        """
        for vacancy_data in vacancies:
            try:
                # Extract skills from vacancy_data
                skills_data = vacancy_data.pop('skills', [])

                # Load job with skills
                job, job_stats = self.load_vacancy(vacancy_data, skills_data)

                # Update overall stats
                if job_stats['created']:
                    self.stats['jobs_created'] += 1
                elif job_stats['updated']:
                    self.stats['jobs_updated'] += 1
                else:
                    self.stats['jobs_skipped'] += 1

                self.stats['aliases_created'] += job_stats['aliases_created']
                self.stats['aliases_reused'] += job_stats['aliases_reused']
                self.stats['extractions_created'] += job_stats['extractions_created']

            except Exception as e:
                logger.error(f"Error in batch: {e}")
                self.stats['errors'] += 1

        return self.stats

    def get_stats(self) -> Dict:
        """Get loading statistics."""
        return self.stats.copy()

    def print_stats(self):
        """Print loading statistics in readable format."""
        print("\n" + "="*60)
        print("PHASE A: INGESTION COMPLETE")
        print("="*60)
        print(f"\n📊 JOB POSTINGS:")
        print(f"  Jobs created:    {self.stats['jobs_created']:>6}")
        print(f"  Jobs updated:    {self.stats['jobs_updated']:>6}")
        print(f"  Jobs skipped:    {self.stats['jobs_skipped']:>6}")

        print(f"\n🏷️  SKILL ALIASES (Raw):")
        print(f"  New aliases:     {self.stats['aliases_created']:>6}")
        print(f"  Reused aliases:  {self.stats['aliases_reused']:>6}")
        print(f"  Total unique:    {self.stats['aliases_created']:>6}")

        print(f"\n🔗 JOB-ALIAS MAPPINGS:")
        print(f"  Extractions:     {self.stats['extractions_created']:>6}")

        if self.stats['errors'] > 0:
            print(f"\n⚠️  ERRORS:")
            print(f"  Errors:          {self.stats['errors']:>6}")

        print("\n" + "="*60)
        print("NEXT STEP: Phases B and C run automatically in sync_jobs")
        print("Optional admin tasks:")
        print("  python manage.py recategorize_skills")
        print("  python manage.py calculate_market_trends")
        print("="*60 + "\n")

