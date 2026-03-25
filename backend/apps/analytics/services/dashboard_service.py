"""
Dashboard Analytics Service
===========================
Service for computing and retrieving dashboard analytics.

Provides both real-time queries and cached snapshot data.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional

from django.db import transaction
from django.db.models import Count, Avg, Min, Max, Q, F
from django.db.models.functions import TruncWeek
from django.utils import timezone

from apps.analytics.models import (
    DashboardSnapshot,
    SkillDemandSnapshot,
    JobCategorySnapshot,
    SalarySnapshot,
    SkillTrendHistory,
)
from apps.jobs.models import JobPosting, JobSkill
from apps.skills.models import Skill, UserSkill, SkillGap, MarketTrend
from apps.learning.models import LearningRoadmap, RoadmapItem, UserLearningProgress
from apps.users.models import User

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service for dashboard analytics data.
    """

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Get market overview data.
        Returns cached snapshot if available, otherwise computes real-time.
        """

        today = date.today()

        # Try to get today's snapshot
        try:
            snapshot = DashboardSnapshot.objects.filter(
                snapshot_date=today
            ).latest('created_at')

            # Last updated: most recent job posting update
            last_job_update = JobPosting.objects.order_by('-updated_at').values_list('updated_at', flat=True).first()
            hours_ago = None
            if last_job_update:
                delta = timezone.now() - last_job_update
                hours_ago = round(delta.total_seconds() / 3600, 1)

            return {
                'source': 'cached',
                'snapshot_date': snapshot.snapshot_date.isoformat(),
                'last_updated_hours_ago': hours_ago,
                'total_active_jobs': snapshot.total_active_jobs,
                'jobs_posted_last_7d': snapshot.jobs_posted_last_7d,
                'jobs_posted_last_30d': snapshot.jobs_posted_last_30d,
                'total_companies': snapshot.total_companies,
                'total_skills_tracked': snapshot.total_skills_tracked,
                'skills_in_demand': snapshot.skills_in_demand,
                'salary_overview': {
                    'avg_min': float(snapshot.avg_salary_min) if snapshot.avg_salary_min else None,
                    'avg_max': float(snapshot.avg_salary_max) if snapshot.avg_salary_max else None,
                    'median': float(snapshot.median_salary) if snapshot.median_salary else None,
                },
                'remote_jobs_percentage': snapshot.remote_jobs_percentage,
                'experience_distribution': snapshot.experience_distribution,
            }
        except DashboardSnapshot.DoesNotExist:
            pass

        # Compute real-time
        return self._compute_market_overview()

    def _compute_market_overview(self) -> Dict[str, Any]:
        """Compute market overview in real-time."""

        now = timezone.now()
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        six_months_ago = now - timedelta(days=180)

        # Job counts (exclude jobs older than 6 months)
        active_jobs = JobPosting.objects.filter(is_active=True, posted_date__gte=six_months_ago)
        total_active = active_jobs.count()
        jobs_7d = active_jobs.filter(posted_date__gte=last_7d).count()
        jobs_30d = active_jobs.filter(posted_date__gte=last_30d).count()

        # Company count
        companies = active_jobs.values('company_name').distinct().count()

        # Skill counts
        total_skills = Skill.objects.count()
        skills_in_demand = JobSkill.objects.filter(
            job_posting__is_active=True
        ).values('skill_id').distinct().count()

        # Salary stats
        salary_stats = active_jobs.filter(
            salary_min__isnull=False
        ).aggregate(
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
        )

        # Remote percentage
        remote_count = active_jobs.filter(is_remote=True).count()
        remote_pct = (remote_count / total_active * 100) if total_active > 0 else 0

        # Experience distribution
        exp_dist = dict(
            active_jobs.values('experience_required')
            .annotate(count=Count('job_id'))
            .values_list('experience_required', 'count')
        )

        # Last updated: most recent job posting update
        last_job_update = active_jobs.order_by('-updated_at').values_list('updated_at', flat=True).first()
        hours_ago = None
        if last_job_update:
            delta = now - last_job_update
            hours_ago = round(delta.total_seconds() / 3600, 1)

        return {
            'source': 'real-time',
            'snapshot_date': date.today().isoformat(),
            'last_updated_hours_ago': hours_ago,
            'total_active_jobs': total_active,
            'jobs_posted_last_7d': jobs_7d,
            'jobs_posted_last_30d': jobs_30d,
            'total_companies': companies,
            'total_skills_tracked': total_skills,
            'skills_in_demand': skills_in_demand,
            'salary_overview': {
                'avg_min': float(salary_stats['avg_min']) if salary_stats['avg_min'] else None,
                'avg_max': float(salary_stats['avg_max']) if salary_stats['avg_max'] else None,
                'median': None,  # Requires more complex query
            },
            'remote_jobs_percentage': round(remote_pct, 1),
            'experience_distribution': exp_dist,
        }

    def get_trending_skills(
        self,
        limit: int = 20,
        period: str = '30d'
    ) -> List[Dict[str, Any]]:
        """
        Get trending skills with demand data.
        """

        today = date.today()

        # Try cached data first
        snapshots = SkillDemandSnapshot.objects.filter(
            snapshot_date=today,
            period=period
        ).select_related('skill').order_by('demand_rank')[:limit]

        if snapshots.exists():
            return [
                {
                    'rank': s.demand_rank,
                    'skill_id': s.skill_id,
                    'skill_name': s.skill.name_en,
                    'skill_name_ru': s.skill.name_ru,
                    'category': s.skill.category,
                    'job_count': s.job_count,
                    'demand_score': s.demand_score,
                    'demand_change_7d': s.demand_change_7d,
                    'demand_change_30d': s.demand_change_30d,
                    'avg_salary': float(s.avg_salary_with_skill) if s.avg_salary_with_skill else None,
                }
                for s in snapshots
            ]

        # Compute real-time from MarketTrend
        trends = MarketTrend.objects.filter(
            period=period
        ).select_related('skill').order_by('-demand_score')[:limit]

        return [
            {
                'rank': idx + 1,
                'skill_id': t.skill_id,
                'skill_name': t.skill.name_en,
                'skill_name_ru': t.skill.name_ru,
                'category': t.skill.category,
                'job_count': t.job_count,
                'demand_score': t.demand_score,
                'demand_change_7d': None,
                'demand_change_30d': t.growth_rate,
                'avg_salary': float(t.avg_salary) if t.avg_salary else None,
            }
            for idx, t in enumerate(trends)
        ]

    def get_salary_insights(
        self,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get salary insights by job title.
        """

        today = date.today()

        # Try cached data
        queryset = SalarySnapshot.objects.filter(snapshot_date=today)
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
        else:
            queryset = queryset.filter(experience_level='all')

        snapshots = queryset.order_by('-salary_avg')[:limit]

        if snapshots.exists():
            return {
                'source': 'cached',
                'experience_filter': experience_level or 'all',
                'salaries': [
                    {
                        'job_title': s.job_title_normalized,
                        'job_count': s.job_count,
                        'salary_min': float(s.salary_min) if s.salary_min else None,
                        'salary_max': float(s.salary_max) if s.salary_max else None,
                        'salary_avg': float(s.salary_avg) if s.salary_avg else None,
                        'salary_median': float(s.salary_median) if s.salary_median else None,
                        'salary_p25': float(s.salary_p25) if s.salary_p25 else None,
                        'salary_p75': float(s.salary_p75) if s.salary_p75 else None,
                        'currency': s.currency,
                    }
                    for s in snapshots
                ]
            }

        # Compute real-time
        return self._compute_salary_insights(experience_level, limit)

    def _compute_salary_insights(
        self,
        experience_level: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """Compute salary insights in real-time."""

        six_months_ago = timezone.now() - timedelta(days=180)
        queryset = JobPosting.objects.filter(
            is_active=True,
            salary_min__isnull=False,
            posted_date__gte=six_months_ago,
        )

        if experience_level and experience_level != 'all':
            queryset = queryset.filter(experience_required=experience_level)

        # Group by job title and compute stats
        salary_by_title = queryset.values('job_title').annotate(
            job_count=Count('job_id'),
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
            min_salary=Min('salary_min'),
            max_salary=Max('salary_max'),
        ).filter(job_count__gte=2).order_by('-avg_max')[:limit]

        return {
            'source': 'real-time',
            'experience_filter': experience_level or 'all',
            'salaries': [
                {
                    'job_title': s['job_title'],
                    'job_count': s['job_count'],
                    'salary_min': float(s['min_salary']) if s['min_salary'] else None,
                    'salary_max': float(s['max_salary']) if s['max_salary'] else None,
                    'salary_avg': float((s['avg_min'] + s['avg_max']) / 2) if s['avg_min'] and s['avg_max'] else None,
                    'salary_median': None,
                    'salary_p25': None,
                    'salary_p75': None,
                    'currency': 'UZS',
                }
                for s in salary_by_title
            ]
        }

    def get_job_categories(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get job openings by category.
        """

        today = date.today()

        # Try cached
        snapshots = JobCategorySnapshot.objects.filter(
            snapshot_date=today
        ).order_by('-job_count')[:limit]

        if snapshots.exists():
            return [
                {
                    'category': s.category_name,
                    'job_count': s.job_count,
                    'change_7d': s.job_count_change_7d,
                    'avg_salary_min': float(s.avg_salary_min) if s.avg_salary_min else None,
                    'avg_salary_max': float(s.avg_salary_max) if s.avg_salary_max else None,
                    'experience_breakdown': s.experience_breakdown,
                    'top_skills': s.top_skills,
                }
                for s in snapshots
            ]

        # Compute real-time (exclude jobs older than 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        categories = JobPosting.objects.filter(
            is_active=True,
            posted_date__gte=six_months_ago,
        ).values('job_category').annotate(
            job_count=Count('job_id'),
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
        ).filter(job_count__gte=1).order_by('-job_count')[:limit]

        return [
            {
                'category': c['job_category'] or 'Other',
                'job_count': c['job_count'],
                'change_7d': None,
                'avg_salary_min': float(c['avg_min']) if c['avg_min'] else None,
                'avg_salary_max': float(c['avg_max']) if c['avg_max'] else None,
                'experience_breakdown': {},
                'top_skills': [],
            }
            for c in categories
        ]

    def get_skill_trend(
        self,
        skill_id: int,
        weeks: int = 12
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical trend data for a skill.
        """

        try:
            skill = Skill.objects.get(skill_id=skill_id)
        except Skill.DoesNotExist:
            return None

        # Get trend history
        history = SkillTrendHistory.objects.filter(
            skill_id=skill_id
        ).order_by('-week_start')[:weeks]

        if history.exists():
            return {
                'skill_id': skill_id,
                'skill_name': skill.name_en,
                'trend_data': [
                    {
                        'week_start': h.week_start.isoformat(),
                        'job_count': h.job_count,
                        'demand_score': h.demand_score,
                    }
                    for h in reversed(list(history))
                ]
            }

        # Compute from job postings
        cutoff = timezone.now() - timedelta(weeks=weeks)
        weekly_data = JobSkill.objects.filter(
            skill_id=skill_id,
            job_posting__posted_date__gte=cutoff
        ).annotate(
            week=TruncWeek('job_posting__posted_date')
        ).values('week').annotate(
            count=Count('job_skill_id')
        ).order_by('week')

        return {
            'skill_id': skill_id,
            'skill_name': skill.name_en,
            'trend_data': [
                {
                    'week_start': w['week'].date().isoformat() if w['week'] else None,
                    'job_count': w['count'],
                    'demand_score': 0,  # Would need normalization
                }
                for w in weekly_data
            ]
        }

    def get_user_progress(self, user: User) -> Dict[str, Any]:
        """
        Get user's learning progress analytics.
        """

        # Skills learned
        user_skills = UserSkill.objects.filter(user=user)
        skills_count = user_skills.count()
        skills_by_level = dict(
            user_skills.values('proficiency_level')
            .annotate(count=Count('user_skill_id'))
            .values_list('proficiency_level', 'count')
        )

        # Skill gaps
        gaps = SkillGap.objects.filter(user=user)
        gaps_total = gaps.count()
        gaps_completed = gaps.filter(status='completed').count()

        # Roadmap progress
        roadmaps = LearningRoadmap.objects.filter(user=user, is_active=True)
        roadmap_stats = []
        total_completion = 0

        for roadmap in roadmaps:
            items = roadmap.items.all()
            completed = items.filter(status='completed').count()
            total = items.count()
            pct = (completed / total * 100) if total > 0 else 0
            total_completion += pct

            roadmap_stats.append({
                'roadmap_id': roadmap.roadmap_id,
                'title': roadmap.title,
                'target_role': roadmap.target_role,
                'total_items': total,
                'completed': completed,
                'completion_percentage': round(pct, 1),
            })

        avg_roadmap_completion = (total_completion / len(roadmap_stats)) if roadmap_stats else 0

        # Learning progress
        learning_progress = UserLearningProgress.objects.filter(user=user)
        resources_started = learning_progress.count()
        resources_completed = learning_progress.filter(status='completed').count()
        total_hours = sum(p.time_spent_hours or 0 for p in learning_progress)

        return {
            'user_id': user.user_id,
            'skills': {
                'total_learned': skills_count,
                'by_proficiency': skills_by_level,
            },
            'skill_gaps': {
                'total': gaps_total,
                'completed': gaps_completed,
                'remaining': gaps_total - gaps_completed,
            },
            'roadmaps': {
                'active_count': len(roadmap_stats),
                'avg_completion': round(avg_roadmap_completion, 1),
                'details': roadmap_stats,
            },
            'learning': {
                'resources_started': resources_started,
                'resources_completed': resources_completed,
                'total_hours_logged': round(total_hours, 1),
            },
        }


    def get_top_job_titles(
        self,
        limit: int = 10,
        period: str = 'all'
    ) -> List[Dict[str, Any]]:
        """
        Get top job titles by posting count.

        Args:
            limit: Number of titles to return (default 10).
            period: Time filter — '7d', '30d', '90d', or 'all'.
        """

        six_months_ago = timezone.now() - timedelta(days=180)
        jobs = JobPosting.objects.filter(is_active=True, posted_date__gte=six_months_ago)

        if period != 'all':
            days = {'7d': 7, '30d': 30, '90d': 90}.get(period, 30)
            cutoff = timezone.now() - timedelta(days=days)
            jobs = jobs.filter(posted_date__gte=cutoff)

        titles = (
            jobs
            .values('job_title')
            .annotate(count=Count('job_id'))
            .order_by('-count')[:limit]
        )

        return [
            {'job_title': t['job_title'], 'count': t['count']}
            for t in titles
        ]


class SnapshotGenerator:
    """
    Generates and refreshes analytics snapshots.
    Called by management command.
    """

    def refresh_all(self):
        """Refresh all analytics snapshots."""

        logger.info("Starting analytics snapshot refresh...")

        self.refresh_dashboard_snapshot()
        self.refresh_skill_demand_snapshots()
        self.refresh_job_category_snapshots()
        self.refresh_salary_snapshots()
        self.refresh_skill_trend_history()

        logger.info("Analytics snapshot refresh complete.")

    @transaction.atomic
    def refresh_dashboard_snapshot(self):
        """Create new dashboard snapshot."""

        logger.info("Refreshing dashboard snapshot...")

        now = timezone.now()
        today = date.today()
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        six_months_ago = now - timedelta(days=180)

        active_jobs = JobPosting.objects.filter(is_active=True, posted_date__gte=six_months_ago)
        total_active = active_jobs.count()

        if total_active == 0:
            logger.warning("No active jobs found, skipping dashboard snapshot")
            return

        # Salary stats
        salary_jobs = active_jobs.filter(salary_min__isnull=False)
        salary_stats = salary_jobs.aggregate(
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
        )

        # Median calculation (simplified)
        salaries = list(salary_jobs.values_list('salary_min', flat=True))
        median = sorted(salaries)[len(salaries) // 2] if salaries else None

        # Experience distribution
        exp_dist = dict(
            active_jobs.values('experience_required')
            .annotate(count=Count('job_id'))
            .values_list('experience_required', 'count')
        )

        # Remote percentage
        remote_count = active_jobs.filter(is_remote=True).count()
        remote_pct = (remote_count / total_active * 100) if total_active > 0 else 0

        DashboardSnapshot.objects.update_or_create(
            snapshot_date=today,
            defaults={
                'total_active_jobs': total_active,
                'jobs_posted_last_7d': active_jobs.filter(posted_date__gte=last_7d).count(),
                'jobs_posted_last_30d': active_jobs.filter(posted_date__gte=last_30d).count(),
                'total_companies': active_jobs.values('company_name').distinct().count(),
                'total_skills_tracked': Skill.objects.count(),
                'skills_in_demand': JobSkill.objects.filter(
                    job_posting__is_active=True
                ).values('skill_id').distinct().count(),
                'avg_salary_min': salary_stats['avg_min'],
                'avg_salary_max': salary_stats['avg_max'],
                'median_salary': median,
                'remote_jobs_percentage': round(remote_pct, 1),
                'experience_distribution': exp_dist,
            }
        )

        logger.info("Dashboard snapshot created")

    @transaction.atomic
    def refresh_skill_demand_snapshots(self):
        """Create skill demand snapshots."""

        logger.info("Refreshing skill demand snapshots...")

        today = date.today()

        # Delete old snapshots for today
        SkillDemandSnapshot.objects.filter(snapshot_date=today).delete()

        # Get skill counts from active jobs (last 6 months only)
        six_months_ago = timezone.now() - timedelta(days=180)
        skill_counts = JobSkill.objects.filter(
            job_posting__is_active=True,
            job_posting__posted_date__gte=six_months_ago,
        ).values('skill_id').annotate(
            job_count=Count('job_posting_id', distinct=True)
        ).order_by('-job_count')

        if not skill_counts:
            logger.warning("No skill data found")
            return

        max_count = skill_counts[0]['job_count'] if skill_counts else 1

        # Create snapshots
        for rank, sc in enumerate(skill_counts, 1):
            try:
                skill = Skill.objects.get(skill_id=sc['skill_id'])
            except Skill.DoesNotExist:
                continue

            # Get salary for jobs with this skill
            avg_salary = JobPosting.objects.filter(
                is_active=True,
                posted_date__gte=six_months_ago,
                job_skills__skill_id=sc['skill_id'],
                salary_min__isnull=False
            ).aggregate(avg=Avg('salary_min'))['avg']

            # Demand score (0-100 normalized)
            demand_score = (sc['job_count'] / max_count * 100) if max_count > 0 else 0

            SkillDemandSnapshot.objects.create(
                skill=skill,
                job_count=sc['job_count'],
                demand_rank=rank,
                demand_score=round(demand_score, 2),
                avg_salary_with_skill=avg_salary,
                period='30d',
                snapshot_date=today,
            )

        logger.info(f"Created {len(skill_counts)} skill demand snapshots")

    @transaction.atomic
    def refresh_job_category_snapshots(self):
        """Create job category snapshots."""

        logger.info("Refreshing job category snapshots...")

        today = date.today()

        # Delete old snapshots
        JobCategorySnapshot.objects.filter(snapshot_date=today).delete()

        # Get categories (last 6 months only)
        six_months_ago = timezone.now() - timedelta(days=180)
        categories = JobPosting.objects.filter(
            is_active=True,
            posted_date__gte=six_months_ago,
        ).values('job_category').annotate(
            job_count=Count('job_id'),
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
        ).order_by('-job_count')

        for cat in categories:
            category_name = cat['job_category'] or 'Other'

            # Experience breakdown
            exp_breakdown = dict(
                JobPosting.objects.filter(
                    is_active=True,
                    posted_date__gte=six_months_ago,
                    job_category=cat['job_category']
                ).values('experience_required').annotate(
                    count=Count('job_id')
                ).values_list('experience_required', 'count')
            )

            # Top skills in category
            top_skills = list(
                JobSkill.objects.filter(
                    job_posting__is_active=True,
                    job_posting__posted_date__gte=six_months_ago,
                    job_posting__job_category=cat['job_category']
                ).values('skill__skill_id', 'skill__name_en').annotate(
                    count=Count('job_skill_id')
                ).order_by('-count')[:5].values('skill__skill_id', 'skill__name_en', 'count')
            )

            JobCategorySnapshot.objects.create(
                category_name=category_name,
                job_count=cat['job_count'],
                avg_salary_min=cat['avg_min'],
                avg_salary_max=cat['avg_max'],
                experience_breakdown=exp_breakdown,
                top_skills=[
                    {'skill_id': s['skill__skill_id'], 'name': s['skill__name_en'], 'count': s['count']}
                    for s in top_skills
                ],
                snapshot_date=today,
            )

        logger.info(f"Created {len(categories)} job category snapshots")

    @transaction.atomic
    def refresh_salary_snapshots(self):
        """Create salary snapshots by job title."""

        logger.info("Refreshing salary snapshots...")

        today = date.today()

        # Delete old snapshots
        SalarySnapshot.objects.filter(snapshot_date=today).delete()

        # Get salary data by normalized job title (last 6 months only)
        six_months_ago = timezone.now() - timedelta(days=180)
        salary_data = JobPosting.objects.filter(
            is_active=True,
            salary_min__isnull=False,
            posted_date__gte=six_months_ago,
        ).values('job_title').annotate(
            job_count=Count('job_id'),
            min_sal=Min('salary_min'),
            max_sal=Max('salary_max'),
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
        ).filter(job_count__gte=2).order_by('-avg_max')[:50]

        for s in salary_data:
            SalarySnapshot.objects.create(
                job_title_normalized=s['job_title'][:200],
                job_count=s['job_count'],
                salary_min=s['min_sal'],
                salary_max=s['max_sal'],
                salary_avg=(s['avg_min'] + s['avg_max']) / 2 if s['avg_min'] and s['avg_max'] else None,
                experience_level='all',
                snapshot_date=today,
            )

        logger.info(f"Created {len(salary_data)} salary snapshots")

    @transaction.atomic
    def refresh_skill_trend_history(self):
        """Update skill trend history (weekly)."""

        logger.info("Refreshing skill trend history...")

        # Get current week start (Monday)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # Check if already have data for this week
        if SkillTrendHistory.objects.filter(week_start=week_start).exists():
            logger.info("Skill trend history already exists for this week")
            return

        # Get skill counts for current week
        week_end = week_start + timedelta(days=7)
        skill_counts = JobSkill.objects.filter(
            job_posting__posted_date__gte=week_start,
            job_posting__posted_date__lt=week_end
        ).values('skill_id').annotate(
            job_count=Count('job_posting_id', distinct=True)
        )

        if not skill_counts:
            return

        max_count = max(sc['job_count'] for sc in skill_counts) if skill_counts else 1

        for sc in skill_counts:
            demand_score = (sc['job_count'] / max_count * 100) if max_count > 0 else 0

            SkillTrendHistory.objects.update_or_create(
                skill_id=sc['skill_id'],
                week_start=week_start,
                defaults={
                    'job_count': sc['job_count'],
                    'demand_score': round(demand_score, 2),
                }
            )

        logger.info(f"Updated skill trend history for week of {week_start}")
