"""
Calculate Market Trends Command
===============================
Aggregates job posting data to populate the market_trends table.

Usage:
    python manage.py calculate_market_trends
    python manage.py calculate_market_trends --period=30d
    python manage.py calculate_market_trends --all-periods
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Avg
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.skills.models import Skill, MarketTrend, SkillAlias
from apps.jobs.models import JobPosting, JobSkill, JobSkillExtraction
from django.db import models as db_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate market trends from job posting data'

    PERIODS = {
        '7d': 7,
        '30d': 30,
        '90d': 90,
        '1y': 365,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            choices=self.PERIODS.keys(),
            default='30d',
            help='Period to calculate (default: 30d)'
        )
        parser.add_argument(
            '--all-periods',
            action='store_true',
            help='Calculate for all periods'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be calculated without saving'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']

        if options['all_periods']:
            periods = list(self.PERIODS.keys())
        else:
            periods = [options['period']]

        self.stdout.write(f"Calculating market trends for periods: {periods}")

        for period in periods:
            self.calculate_period(period)

        self.stdout.write(self.style.SUCCESS("Market trends calculation complete"))

    def calculate_period(self, period: str):
        """Calculate market trends for a specific period."""

        days = self.PERIODS[period]
        cutoff_date = timezone.now() - timedelta(days=days)
        previous_cutoff = cutoff_date - timedelta(days=days)

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"Calculating trends for period: {period} ({days} days)")
        self.stdout.write(f"Date range: {cutoff_date.date()} to {timezone.now().date()}")

        # Get all active job postings in the period
        current_jobs = JobPosting.objects.filter(
            posted_date__gte=cutoff_date,
            is_active=True
        )

        previous_jobs = JobPosting.objects.filter(
            posted_date__gte=previous_cutoff,
            posted_date__lt=cutoff_date,
            is_active=True
        )

        current_job_count = current_jobs.count()
        previous_job_count = previous_jobs.count()

        self.stdout.write(f"Current period jobs: {current_job_count}")
        self.stdout.write(f"Previous period jobs: {previous_job_count}")

        if current_job_count == 0:
            self.stdout.write(self.style.WARNING(
                f"No jobs found for period {period}. Skipping."
            ))
            return

        # Calculate skill statistics using JobSkill (resolved skills)
        # First try JobSkill, if empty fall back to JobSkillExtraction

        skill_stats = self._calculate_from_job_skills(
            current_jobs, previous_jobs, period
        )

        if not skill_stats:
            self.stdout.write("No JobSkill data, trying JobSkillExtraction...")
            skill_stats = self._calculate_from_extractions(
                current_jobs, previous_jobs, period
            )

        if not skill_stats:
            self.stdout.write(self.style.WARNING(
                f"No skill data found for period {period}"
            ))
            return

        # Calculate max job count for normalization
        max_job_count = max(s['job_count'] for s in skill_stats.values())

        # Create MarketTrend entries
        trends_created = 0
        trends_updated = 0

        with transaction.atomic():
            for skill_id, stats in skill_stats.items():
                # Normalize demand score to 0-100
                demand_score = (stats['job_count'] / max_job_count) * 100 if max_job_count > 0 else 0

                # Calculate growth rate (NULL if no previous data)
                if stats['previous_count'] > 0:
                    growth_rate = ((stats['job_count'] - stats['previous_count'])
                                   / stats['previous_count']) * 100
                    growth_rate = round(growth_rate, 2)
                else:
                    growth_rate = None  # No previous data = NULL

                trend_data = {
                    'demand_score': round(demand_score, 2),
                    'job_count': stats['job_count'],
                    'growth_rate': growth_rate,
                    'avg_salary': stats.get('avg_salary'),
                }

                if self.dry_run:
                    skill = Skill.objects.get(skill_id=skill_id)
                    growth_str = f"{growth_rate:.1f}%" if growth_rate is not None else "N/A"
                    self.stdout.write(
                        f"  Would update: {skill.name_en} - "
                        f"demand={demand_score:.1f}, jobs={stats['job_count']}, "
                        f"growth={growth_str}"
                    )
                else:
                    trend, created = MarketTrend.objects.update_or_create(
                        skill_id=skill_id,
                        period=period,
                        defaults=trend_data
                    )

                    if created:
                        trends_created += 1
                    else:
                        trends_updated += 1

        if not self.dry_run:
            self.stdout.write(
                f"Created {trends_created} trends, updated {trends_updated} trends"
            )

    def _calculate_from_job_skills(self, current_jobs, previous_jobs, period):
        """Calculate stats from JobSkill table (resolved skills)."""

        # Current period skill counts
        current_skills = (
            JobSkill.objects
            .filter(job_posting__in=current_jobs)
            .values('skill_id')
            .annotate(
                job_count=Count('job_posting', distinct=True),
                avg_salary=Avg(
                    Coalesce('job_posting__salary_min', 'job_posting__salary_max'),
                    output_field=db_models.DecimalField()
                )
            )
        )

        if not current_skills.exists():
            return None

        # Previous period skill counts
        previous_skills = (
            JobSkill.objects
            .filter(job_posting__in=previous_jobs)
            .values('skill_id')
            .annotate(job_count=Count('job_posting', distinct=True))
        )

        # Build previous counts lookup
        previous_counts = {s['skill_id']: s['job_count'] for s in previous_skills}

        # Build result
        skill_stats = {}
        for skill_data in current_skills:
            skill_id = skill_data['skill_id']
            skill_stats[skill_id] = {
                'job_count': skill_data['job_count'],
                'previous_count': previous_counts.get(skill_id, 0),
                'avg_salary': skill_data['avg_salary'],
            }

        self.stdout.write(f"Found {len(skill_stats)} skills with JobSkill data")
        return skill_stats

    def _calculate_from_extractions(self, current_jobs, previous_jobs, period):
        """Calculate stats from JobSkillExtraction (via aliases)."""

        # Get resolved aliases with their canonical skill IDs
        resolved_aliases = SkillAlias.objects.filter(
            status='resolved',
            skill_id__isnull=False
        ).values_list('alias_id', 'skill_id')

        alias_to_skill = dict(resolved_aliases)

        if not alias_to_skill:
            self.stdout.write("No resolved aliases found")
            return None

        # Current period extractions
        current_extractions = (
            JobSkillExtraction.objects
            .filter(
                job_posting__in=current_jobs,
                alias_id__in=alias_to_skill.keys()
            )
            .values('alias_id', 'job_posting_id')
            .annotate(
                salary=Avg(
                    Coalesce(
                        'job_posting__salary_min',
                        'job_posting__salary_max'
                    )
                )
            )
        )

        # Previous period extractions
        previous_extractions = (
            JobSkillExtraction.objects
            .filter(
                job_posting__in=previous_jobs,
                alias_id__in=alias_to_skill.keys()
            )
            .values('alias_id')
            .annotate(job_count=Count('job_posting', distinct=True))
        )

        # Build previous counts by skill
        previous_by_skill = {}
        for ext in previous_extractions:
            skill_id = alias_to_skill.get(ext['alias_id'])
            if skill_id:
                previous_by_skill[skill_id] = (
                    previous_by_skill.get(skill_id, 0) + ext['job_count']
                )

        # Aggregate current by skill
        skill_stats = {}
        for ext in current_extractions:
            skill_id = alias_to_skill.get(ext['alias_id'])
            if not skill_id:
                continue

            if skill_id not in skill_stats:
                skill_stats[skill_id] = {
                    'job_ids': set(),
                    'salaries': [],
                    'previous_count': previous_by_skill.get(skill_id, 0),
                }

            skill_stats[skill_id]['job_ids'].add(ext['job_posting_id'])
            if ext['salary']:
                skill_stats[skill_id]['salaries'].append(ext['salary'])

        # Convert to final format
        result = {}
        for skill_id, data in skill_stats.items():
            avg_salary = None
            if data['salaries']:
                avg_salary = Decimal(sum(data['salaries'])) / len(data['salaries'])

            result[skill_id] = {
                'job_count': len(data['job_ids']),
                'previous_count': data['previous_count'],
                'avg_salary': avg_salary,
            }

        self.stdout.write(f"Found {len(result)} skills with extraction data")
        return result
