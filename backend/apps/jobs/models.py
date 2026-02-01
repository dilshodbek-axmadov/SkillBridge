"""
Jobs App Models (UPDATED)
========================
Multilingual job postings with canonical skill linkage.
"""

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

    job_url = models.URLField(_('job URL'), max_length=500)
    is_active = models.BooleanField(_('active'), default=True)

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

    def __str__(self):
        return f"{self.job_title} – {self.company_name}"


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
