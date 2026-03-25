"""
Jobs App Models (UPDATED)
========================
Multilingual job postings with canonical skill linkage.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.skills.models import Skill, SkillAlias


# ==================== JOB POSTING ====================

class JobPosting(models.Model):

    EXPERIENCE_CHOICES = [
        ('no_experience', _('No Experience')),
        ('junior', _('Junior (1–3 years)')),
        ('mid', _('Mid (3–6 years)')),
        ('senior', _('Senior (6+ years)')),
    ]

    EMPLOYMENT_CHOICES = [
        ('full_time', _('Full-time')),
        ('part_time', _('Part-time')),
        ('project', _('Project-based')),
    ]

    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ru', _('Russian')),
        ('uz', _('Uzbek')),
    ]

    class ListingStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ACTIVE = 'active', _('Active')
        ARCHIVED = 'archived', _('Archived')

    job_id = models.AutoField(primary_key=True)

    external_job_id = models.CharField(
        _('external job ID'),
        max_length=50,
        unique=True,
        db_index=True
    )

    source = models.CharField(
        _('source'),
        max_length=50,
        default='hh.uz'
    )

    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_job_postings',
        null=True,
        blank=True,
        verbose_name=_('posted by'),
        help_text=_('Recruiter who created this listing on the platform; null for scraped jobs (e.g. hh.uz).'),
    )

    original_language = models.CharField(
        _('original language'),
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='ru'
    )

    job_title = models.CharField(_('job title'), max_length=255)
    company_name = models.CharField(_('company'), max_length=255, blank=True)
    job_category = models.CharField(_('category'), max_length=100, blank=True)

    job_description = models.TextField(_('description'), blank=True)
    
    experience_required = models.CharField(
        _('experience'),
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        blank=True
    )

    employment_type = models.CharField(
        _('employment type'),
        max_length=20,
        choices=EMPLOYMENT_CHOICES,
        default='full_time'
    )

    salary_min = models.DecimalField(
        _('min salary'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    salary_max = models.DecimalField(
        _('max salary'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    salary_currency = models.CharField(
        _('currency'),
        max_length=3,
        default='UZS'
    )

    location = models.CharField(_('location'), max_length=255, blank=True)
    is_remote = models.BooleanField(_('remote'), default=False)

    posted_date = models.DateTimeField(_('posted date'))
    deadline_date = models.DateTimeField(_('deadline'), null=True, blank=True)

    job_url = models.URLField(_('job URL'), max_length=500, blank=True, default='')
    is_active = models.BooleanField(_('active'), default=True)

    listing_status = models.CharField(
        _('listing status'),
        max_length=20,
        choices=ListingStatus.choices,
        default=ListingStatus.ACTIVE,
        db_index=True,
        help_text=_('draft = not public; active = visible in job search; archived = closed listing.'),
    )
    view_count = models.PositiveIntegerField(_('view count'), default=0)

    scraped_at = models.DateTimeField(_('scraped at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    skills = models.ManyToManyField(
        Skill,
        through='JobSkill',
        related_name='job_postings'
    )

    class Meta:
        db_table = 'job_postings'
        ordering = ['-posted_date']
        verbose_name = _('job posting')
        verbose_name_plural = _('job postings')
        indexes = [
            models.Index(fields=['posted_by', '-posted_date']),
            models.Index(fields=['source', 'is_active']),
        ]

    def __str__(self):
        return f"{self.job_title} – {self.company_name}"


class JobApplication(models.Model):
    """Developer application to a job posting (SkillBridge platform roles)."""

    application_id = models.AutoField(primary_key=True)
    job_posting = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('job posting'),
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications',
        verbose_name=_('applicant'),
    )
    created_at = models.DateTimeField(_('applied at'), auto_now_add=True)

    class Meta:
        db_table = 'job_applications'
        verbose_name = _('job application')
        verbose_name_plural = _('job applications')
        constraints = [
            models.UniqueConstraint(
                fields=['job_posting', 'applicant'],
                name='unique_job_applicant',
            ),
        ]
        indexes = [
            models.Index(fields=['job_posting', '-created_at']),
        ]

    def __str__(self):
        return f"{self.applicant_id} → job {self.job_posting_id}"


# ==================== JOB TRANSLATION ====================

class JobPostingTranslation(models.Model):

    QUALITY_CHOICES = [
        ('raw', _('Raw AI')),
        ('reviewed', _('Reviewed')),
        ('verified', _('Verified')),
    ]

    translation_id = models.AutoField(primary_key=True)

    job_posting = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='translations'
    )

    language_code = models.CharField(
        _('language'),
        max_length=2
    )

    job_title = models.CharField(_('job title'), max_length=255)
    job_category = models.CharField(_('category'), max_length=100, blank=True)
    job_description = models.TextField(_('description'), blank=True)
    requirements = models.TextField(_('requirements'), blank=True)
    responsibilities = models.TextField(_('responsibilities'), blank=True)

    translated_by = models.CharField(
        _('translated by'),
        max_length=20,
        choices=[('ai', _('AI')), ('human', _('Human'))],
        default='ai'
    )

    translation_quality = models.CharField(
        _('quality'),
        max_length=20,
        choices=QUALITY_CHOICES,
        default='raw'
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'job_posting_translations'
        unique_together = [('job_posting', 'language_code')]
        verbose_name = _('job translation')
        verbose_name_plural = _('job translations')


# ==================== JOB SKILL ====================

class JobSkill(models.Model):
    """
    Skill requirements for jobs.
    """

    IMPORTANCE_CHOICES = [
        ('core', _('Core')),
        ('secondary', _('Secondary')),
    ]

    job_skill_id = models.AutoField(primary_key=True)

    job_posting = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='job_skills'
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='job_skills'
    )

    importance = models.CharField(
        _('importance'),
        max_length=20,
        choices=IMPORTANCE_CHOICES,
        default='core'
    )

    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )

    class Meta:
        db_table = 'job_skills'
        unique_together = [('job_posting', 'skill')]
        verbose_name = _('job skill')
        verbose_name_plural = _('job skills')

    def __str__(self):
        return f"{self.job_posting.job_title} → {self.skill.name_en}"
    


class JobSkillExtraction(models.Model):
    """
    Tracks which aliases were extracted from which jobs.
    
    This is the missing link that connects:
    - Jobs → Aliases (during ingestion)
    - Jobs → Skills (after resolution via aliases)
    
    Workflow:
    1. Scrape job → extract skills → create SkillAlias entries
    2. For each alias, create JobSkillExtraction to remember source job
    3. After resolution, use this table to populate final job_skills table
    """

    extraction_id = models.AutoField(primary_key=True)

    job_posting = models.ForeignKey(
        'jobs.JobPosting',
        on_delete=models.CASCADE,
        related_name='skill_extractions',
        verbose_name=_('job posting')
    )

    alias = models.ForeignKey(
        SkillAlias,
        on_delete=models.CASCADE,
        related_name='job_extractions',
        verbose_name=_('skill alias')
    )

    importance = models.CharField(
        _('importance'),
        max_length=20,
        choices=[
            ('core', _('Core / Required')),
            ('secondary', _('Secondary / Nice-to-have')),
        ],
        default='core'
    )

    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )

    class Meta:
        db_table = 'job_skill_extractions'
        unique_together = [('job_posting', 'alias')]
        verbose_name = _('job skill extraction')
        verbose_name_plural = _('job skill extractions')
        indexes = [
            models.Index(fields=['job_posting']),
            models.Index(fields=['alias']),
        ]

    def __str__(self):
        return f"Job {self.job_posting_id} → {self.alias.alias_text}"


# ==================== EXTRACTION RUN ====================

class ExtractionRun(models.Model):
    """
    Tracks each job extraction run.
    Unique constraint on (source, run_date) prevents duplicate daily runs.
    """

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('running', _('Running')),
        ('success', _('Success')),
        ('failed', _('Failed')),
    ]

    TRIGGER_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('manual', _('Manual')),
        ('startup', _('Startup Catch-up')),
    ]

    id = models.AutoField(primary_key=True)

    source = models.CharField(
        _('source'),
        max_length=50,
        default='hh.uz',
    )

    run_date = models.DateField(
        _('run date'),
        help_text=_('The calendar date this extraction covers.'),
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )

    trigger = models.CharField(
        _('trigger'),
        max_length=20,
        choices=TRIGGER_CHOICES,
        default='scheduled',
    )

    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    finished_at = models.DateTimeField(_('finished at'), null=True, blank=True)

    jobs_created = models.IntegerField(_('jobs created'), default=0)
    jobs_updated = models.IntegerField(_('jobs updated'), default=0)
    jobs_skipped = models.IntegerField(_('jobs skipped'), default=0)
    jobs_deactivated = models.IntegerField(_('jobs deactivated'), default=0)
    aliases_created = models.IntegerField(_('aliases created'), default=0)
    errors_count = models.IntegerField(_('errors'), default=0)

    error_message = models.TextField(_('error message'), blank=True)

    celery_task_id = models.CharField(
        _('celery task ID'),
        max_length=255,
        blank=True,
        db_index=True,
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        db_table = 'extraction_runs'
        ordering = ['-run_date', '-started_at']
        verbose_name = _('extraction run')
        verbose_name_plural = _('extraction runs')
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'run_date'],
                name='unique_source_run_date',
            )
        ]

    def __str__(self):
        return f"{self.source} | {self.run_date} | {self.status}"

    @property
    def duration_seconds(self):
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
