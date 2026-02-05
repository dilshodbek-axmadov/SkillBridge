"""
Analytics App Models
====================
Pre-computed analytics data for dashboard performance.

These models cache aggregated data from jobs, skills, and learning apps
for fast dashboard rendering. Updated periodically via management command.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.skills.models import Skill


class DashboardSnapshot(models.Model):
    """
    Point-in-time snapshot of overall market statistics.
    One record per snapshot, typically refreshed daily.
    """

    snapshot_id = models.AutoField(primary_key=True)

    # Job market overview
    total_active_jobs = models.IntegerField(
        _('total active jobs'),
        default=0,
        help_text=_('Total number of active job postings')
    )
    jobs_posted_last_7d = models.IntegerField(
        _('jobs posted (7d)'),
        default=0,
        help_text=_('Jobs posted in last 7 days')
    )
    jobs_posted_last_30d = models.IntegerField(
        _('jobs posted (30d)'),
        default=0,
        help_text=_('Jobs posted in last 30 days')
    )

    # Company stats
    total_companies = models.IntegerField(
        _('total companies'),
        default=0,
        help_text=_('Unique companies with job postings')
    )

    # Skill stats
    total_skills_tracked = models.IntegerField(
        _('skills tracked'),
        default=0,
        help_text=_('Total canonical skills in system')
    )
    skills_in_demand = models.IntegerField(
        _('skills in demand'),
        default=0,
        help_text=_('Skills appearing in active jobs')
    )

    # Salary overview (in USD for comparison)
    avg_salary_min = models.DecimalField(
        _('average min salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    avg_salary_max = models.DecimalField(
        _('average max salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    median_salary = models.DecimalField(
        _('median salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Remote work stats
    remote_jobs_percentage = models.FloatField(
        _('remote jobs %'),
        default=0.0,
        help_text=_('Percentage of remote-friendly jobs')
    )

    # Experience distribution (JSON)
    experience_distribution = models.JSONField(
        _('experience distribution'),
        default=dict,
        help_text=_('Job count by experience level')
    )

    # Timestamps
    snapshot_date = models.DateField(
        _('snapshot date'),
        auto_now_add=True
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )

    class Meta:
        db_table = 'dashboard_snapshots'
        ordering = ['-snapshot_date']
        verbose_name = _('dashboard snapshot')
        verbose_name_plural = _('dashboard snapshots')
        get_latest_by = 'snapshot_date'

    def __str__(self):
        return f"Dashboard Snapshot - {self.snapshot_date}"


class SkillDemandSnapshot(models.Model):
    """
    Skill demand analytics snapshot.
    Tracks skill popularity and trends for dashboard.
    """

    snapshot_id = models.AutoField(primary_key=True)

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='demand_snapshots',
        verbose_name=_('skill')
    )

    # Demand metrics
    job_count = models.IntegerField(
        _('job count'),
        default=0,
        help_text=_('Number of jobs requiring this skill')
    )
    demand_rank = models.IntegerField(
        _('demand rank'),
        default=0,
        help_text=_('Rank among all skills (1 = most in-demand)')
    )
    demand_score = models.FloatField(
        _('demand score'),
        default=0.0,
        help_text=_('Normalized demand score (0-100)')
    )
    demand_change_7d = models.FloatField(
        _('demand change (7d)'),
        null=True,
        blank=True,
        help_text=_('Percentage change in last 7 days')
    )
    demand_change_30d = models.FloatField(
        _('demand change (30d)'),
        null=True,
        blank=True,
        help_text=_('Percentage change in last 30 days')
    )

    # Salary associated with this skill
    avg_salary_with_skill = models.DecimalField(
        _('avg salary with skill'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Snapshot period
    period = models.CharField(
        _('period'),
        max_length=10,
        choices=[
            ('7d', _('Last 7 days')),
            ('30d', _('Last 30 days')),
            ('90d', _('Last 90 days')),
            ('all', _('All time')),
        ],
        default='30d'
    )

    snapshot_date = models.DateField(
        _('snapshot date'),
        auto_now_add=True
    )

    class Meta:
        db_table = 'skill_demand_snapshots'
        ordering = ['demand_rank']
        verbose_name = _('skill demand snapshot')
        verbose_name_plural = _('skill demand snapshots')
        unique_together = [('skill', 'period', 'snapshot_date')]
        indexes = [
            models.Index(fields=['period', 'demand_rank']),
            models.Index(fields=['snapshot_date']),
        ]

    def __str__(self):
        return f"{self.skill.name_en} - Rank #{self.demand_rank} ({self.period})"


class JobCategorySnapshot(models.Model):
    """
    Job category analytics snapshot.
    Tracks job openings and salaries by category.
    """

    snapshot_id = models.AutoField(primary_key=True)

    category_name = models.CharField(
        _('category name'),
        max_length=100,
        help_text=_('Job category (e.g., "Backend Development")')
    )

    # Job counts
    job_count = models.IntegerField(
        _('job count'),
        default=0
    )
    job_count_change_7d = models.FloatField(
        _('change (7d) %'),
        null=True,
        blank=True
    )

    # Salary stats for category
    avg_salary_min = models.DecimalField(
        _('avg min salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    avg_salary_max = models.DecimalField(
        _('avg max salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Experience breakdown (JSON: {"junior": 10, "mid": 20, ...})
    experience_breakdown = models.JSONField(
        _('experience breakdown'),
        default=dict
    )

    # Top skills in this category (JSON: [{"skill_id": 1, "name": "Python", "count": 50}, ...])
    top_skills = models.JSONField(
        _('top skills'),
        default=list
    )

    snapshot_date = models.DateField(
        _('snapshot date'),
        auto_now_add=True
    )

    class Meta:
        db_table = 'job_category_snapshots'
        ordering = ['-job_count']
        verbose_name = _('job category snapshot')
        verbose_name_plural = _('job category snapshots')
        unique_together = [('category_name', 'snapshot_date')]

    def __str__(self):
        return f"{self.category_name} - {self.job_count} jobs"


class SalarySnapshot(models.Model):
    """
    Salary analytics by job title/role.
    """

    snapshot_id = models.AutoField(primary_key=True)

    job_title_normalized = models.CharField(
        _('job title'),
        max_length=200,
        help_text=_('Normalized job title (e.g., "Backend Developer")')
    )

    # Sample size
    job_count = models.IntegerField(
        _('job count'),
        default=0,
        help_text=_('Number of jobs with salary data')
    )

    # Salary statistics
    salary_min = models.DecimalField(
        _('min salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_max = models.DecimalField(
        _('max salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_avg = models.DecimalField(
        _('avg salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_median = models.DecimalField(
        _('median salary'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Percentiles
    salary_p25 = models.DecimalField(
        _('25th percentile'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    salary_p75 = models.DecimalField(
        _('75th percentile'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Currency (for display purposes)
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='UZS'
    )

    # Experience level filter
    experience_level = models.CharField(
        _('experience level'),
        max_length=20,
        choices=[
            ('all', _('All levels')),
            ('no_experience', _('No Experience')),
            ('junior', _('Junior')),
            ('mid', _('Mid-level')),
            ('senior', _('Senior')),
        ],
        default='all'
    )

    snapshot_date = models.DateField(
        _('snapshot date'),
        auto_now_add=True
    )

    class Meta:
        db_table = 'salary_snapshots'
        ordering = ['-salary_avg']
        verbose_name = _('salary snapshot')
        verbose_name_plural = _('salary snapshots')
        unique_together = [('job_title_normalized', 'experience_level', 'snapshot_date')]

    def __str__(self):
        return f"{self.job_title_normalized} - {self.salary_avg} {self.currency}"


class SkillTrendHistory(models.Model):
    """
    Historical skill demand for trend charts.
    Stores weekly snapshots for time-series analysis.
    """

    history_id = models.AutoField(primary_key=True)

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='trend_history',
        verbose_name=_('skill')
    )

    # Weekly metrics
    week_start = models.DateField(
        _('week start'),
        help_text=_('Start of the week (Monday)')
    )
    job_count = models.IntegerField(
        _('job count'),
        default=0
    )
    demand_score = models.FloatField(
        _('demand score'),
        default=0.0
    )

    class Meta:
        db_table = 'skill_trend_history'
        ordering = ['-week_start']
        verbose_name = _('skill trend history')
        verbose_name_plural = _('skill trend history')
        unique_together = [('skill', 'week_start')]
        indexes = [
            models.Index(fields=['skill', 'week_start']),
        ]

    def __str__(self):
        return f"{self.skill.name_en} - Week of {self.week_start}"
