"""
Jobs App Models
===============
Models for job postings, job skills, and market trend analysis.

Tables:
- JobPosting
- JobSkill
- MarketTrend
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.skills.models import Skill


class JobPosting(models.Model):
    """
    Job postings scraped from hh.uz and other sources.
    Stores complete job information.
    """
    
    EXPERIENCE_LEVELS = [
        ('no_experience', _('No Experience')),
        ('junior', _('Junior (1-3 years)')),
        ('mid', _('Mid-level (3-5 years)')),
        ('senior', _('Senior (5+ years)')),
        ('lead', _('Lead/Principal')),
    ]
    
    job_id = models.AutoField(
        primary_key=True
    )
    external_job_id = models.CharField(
        _('external job ID'),
        max_length=100,
        unique=True,
        help_text=_('Job ID from source (e.g., hh.uz job ID).')
    )
    job_title = models.CharField(
        _('job title'),
        max_length=200,
        help_text=_('Position title.')
    )
    company_name = models.CharField(
        _('company name'),
        max_length=200,
        help_text=_('Hiring company name.')
    )
    job_category = models.CharField(
        _('job category'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Job category (e.g., "Development", "Data Science").')
    )
    experience_required = models.CharField(
        _('experience required'),
        max_length=50,
        choices=EXPERIENCE_LEVELS,
        default='no_experience',
        help_text=_('Required experience level.')
    )
    salary_min = models.DecimalField(
        _('minimum salary'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Minimum salary offered.')
    )
    salary_max = models.DecimalField(
        _('maximum salary'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Maximum salary offered.')
    )
    salary_currency = models.CharField(
        _('salary currency'),
        max_length=3,
        default='UZS',
        help_text=_('Currency code (UZS, USD, etc.).')
    )
    location = models.CharField(
        _('location'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Job location/city.')
    )
    job_description = models.TextField(
        _('job description'),
        help_text=_('Full job description text.')
    )
    requirements = models.TextField(
        _('requirements'),
        blank=True,
        null=True,
        help_text=_('Job requirements and qualifications.')
    )
    responsibilities = models.TextField(
        _('responsibilities'),
        blank=True,
        null=True,
        help_text=_('Job responsibilities.')
    )
    benefits = models.TextField(
        _('benefits'),
        blank=True,
        null=True,
        help_text=_('Benefits and perks.')
    )
    posted_date = models.DateField(
        _('posted date'),
        help_text=_('Date when job was posted.')
    )
    deadline_date = models.DateField(
        _('deadline date'),
        blank=True,
        null=True,
        help_text=_('Application deadline.')
    )
    job_url = models.URLField(
        _('job URL'),
        max_length=500,
        help_text=_('Link to original job posting.')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether job is still available.')
    )
    is_remote = models.BooleanField(
        _('remote work'),
        default=False,
        help_text=_('Whether position allows remote work.')
    )
    employment_type = models.CharField(
        _('employment type'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Full-time, Part-time, Contract, etc.')
    )
    source = models.CharField(
        _('source'),
        max_length=50,
        default='hh.uz',
        help_text=_('Job board source.')
    )
    scraped_at = models.DateTimeField(
        _('scraped at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('job posting')
        verbose_name_plural = _('job postings')
        ordering = ['-posted_date', '-scraped_at']
        db_table = 'job_postings'
        indexes = [
            models.Index(fields=['job_category']),
            models.Index(fields=['experience_required']),
            models.Index(fields=['location']),
            models.Index(fields=['posted_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['external_job_id']),
        ]
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
    
    @property
    def salary_range(self):
        """Return formatted salary range."""
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f} - {self.salary_max:,.0f} {self.salary_currency}"
        elif self.salary_min:
            return f"From {self.salary_min:,.0f} {self.salary_currency}"
        elif self.salary_max:
            return f"Up to {self.salary_max:,.0f} {self.salary_currency}"
        return _("Not specified")


class JobSkill(models.Model):
    """
    Skills required for specific job postings.
    Links jobs to skills with importance level.
    """
    
    IMPORTANCE_LEVELS = [
        ('core', _('Core/Required')),
        ('secondary', _('Secondary/Preferred')),
        ('nice_to_have', _('Nice to Have')),
    ]
    
    job_skill_id = models.AutoField(
        primary_key=True
    )
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='required_skills',
        verbose_name=_('job posting')
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='job_requirements',
        verbose_name=_('skill')
    )
    importance = models.CharField(
        _('importance'),
        max_length=20,
        choices=IMPORTANCE_LEVELS,
        default='secondary',
        help_text=_('Importance of this skill for the job.')
    )
    years_required = models.FloatField(
        _('years required'),
        default=0.0,
        blank=True,
        null=True,
        help_text=_('Minimum years of experience required.')
    )
    extracted_at = models.DateTimeField(
        _('extracted at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('job skill')
        verbose_name_plural = _('job skills')
        ordering = ['-importance', 'skill__skill_name']
        db_table = 'job_skills'
        unique_together = [['job', 'skill']]
        indexes = [
            models.Index(fields=['job', 'skill']),
            models.Index(fields=['importance']),
        ]
    
    def __str__(self):
        return f"{self.job.job_title} - {self.skill.skill_name} ({self.importance})"


class MarketTrend(models.Model):
    """
    Aggregated market trends and analytics.
    Tracks skill demand, salary trends, and job counts over time.
    """
    
    trend_id = models.AutoField(
        primary_key=True
    )
    job_category = models.CharField(
        _('job category'),
        max_length=100,
        help_text=_('Job category (e.g., "Backend Development").')
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='market_trends',
        verbose_name=_('skill'),
        blank=True,
        null=True,
        help_text=_('Specific skill (optional, for skill-based trends).')
    )
    demand_score = models.FloatField(
        _('demand score'),
        default=0.0,
        help_text=_('Demand score (0-10) based on job frequency.')
    )
    average_salary = models.DecimalField(
        _('average salary'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Average salary for this category/skill.')
    )
    salary_currency = models.CharField(
        _('salary currency'),
        max_length=3,
        default='UZS'
    )
    job_count = models.IntegerField(
        _('job count'),
        default=0,
        help_text=_('Number of jobs requiring this skill/in this category.')
    )
    growth_rate = models.FloatField(
        _('growth rate'),
        default=0.0,
        help_text=_('Growth rate compared to previous period (%).')
    )
    analysis_period_start = models.DateField(
        _('analysis period start'),
        help_text=_('Start date of analysis period.')
    )
    analysis_period_end = models.DateField(
        _('analysis period end'),
        help_text=_('End date of analysis period.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('market trend')
        verbose_name_plural = _('market trends')
        ordering = ['-demand_score', '-created_at']
        db_table = 'market_trends'
        indexes = [
            models.Index(fields=['job_category']),
            models.Index(fields=['skill']),
            models.Index(fields=['demand_score']),
            models.Index(fields=['analysis_period_start', 'analysis_period_end']),
        ]
    
    def __str__(self):
        if self.skill:
            return f"{self.skill.skill_name} - {self.job_category} (Score: {self.demand_score})"
        return f"{self.job_category} Trend (Score: {self.demand_score})"
    
    @property
    def period_display(self):
        """Return formatted analysis period."""
        return f"{self.analysis_period_start} to {self.analysis_period_end}"