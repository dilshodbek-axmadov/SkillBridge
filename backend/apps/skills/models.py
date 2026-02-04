"""
Skills App Models 
===============================================
Phase-based skill resolution system:
- Phase A: Raw skills → skill_aliases (unresolved)
- Phase B: Resolver maps aliases → canonical skills
- Phase C: Link jobs → skills via resolved aliases
"""

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.users.models import User


# SKILL

class Skill(models.Model):
    """
    Canonical skill with multilingual names.
    English (name_en) is the source of truth.
    
    Example:
        name_en: "Object-Oriented Programming"
        name_ru: "Объектно-ориентированное программирование"
        name_uz: None
        category: "methodology"
    """

    CATEGORY_CHOICES = [
        ('programming', _('Programming Language')),
        ('framework', _('Framework / Library')),
        ('database', _('Database')),
        ('tool', _('Tool / Software')),
        ('cloud', _('Cloud Platform')),
        ('methodology', _('Methodology / Practice')),
        ('soft_skill', _('Soft Skill')),
        ('other', _('Other')),
    ]

    skill_id = models.AutoField(primary_key=True)

    # Multilingual names (English is required)
    name_en = models.CharField(
        _('name (English)'),
        max_length=100,
        unique=True,  # English name must be unique
        db_index=True,
        help_text=_("Canonical English name, e.g. 'Python', 'SQL', 'OOP'")
    )

    name_ru = models.CharField(
        _('name (Russian)'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Russian translation, e.g. 'Питон', 'ООП'")
    )

    name_uz = models.CharField(
        _('name (Uzbek)'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Uzbek translation")
    )

    # Normalized key for matching (generated from name_en)
    normalized_key = models.CharField(
        _('normalized key'),
        max_length=100,
        unique=True,
        db_index=True,
        editable=False,
        help_text=_("Auto-generated: 'python', 'oop', 'sql'")
    )

    # Classification
    category = models.CharField(
        _('category'),
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='other'
    )

    # Quality control
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_("Admin-reviewed and confirmed correct")
    )

    verification_notes = models.TextField(
        _('verification notes'),
        blank=True,
        help_text=_("Admin notes about verification/merging")
    )

    # Timestamps
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        db_table = 'skills'
        ordering = ['name_en']
        verbose_name = _('skill')
        verbose_name_plural = _('skills')
        indexes = [
            models.Index(fields=['name_en']),
            models.Index(fields=['normalized_key']),
            models.Index(fields=['category']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return self.name_en

    def save(self, *args, **kwargs):
        """Auto-generate normalized_key from name_en."""
        if self.name_en:
            self.normalized_key = self.normalize_key(self.name_en)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_key(text: str) -> str:
        """
        Normalize skill name to canonical key.
        
        Examples:
            'Python' → 'python'
            'C++' → 'c_plus_plus'
            'Node.js' → 'nodejs'
            'React.js' → 'reactjs'
        """
        if not text:
            return ''
        
        text = text.lower().strip()
        
        # Handle special characters
        text = text.replace('++', '_plus_plus')
        text = text.replace('#', '_sharp')
        text = text.replace('.', '')
        text = text.replace('/', '_')
        
        # Use slugify and replace hyphens with underscores
        normalized = slugify(text).replace('-', '_')
        
        return normalized

    def get_primary_alias(self, language_code='en'):
        """Get the most-used alias for this skill in given language."""
        return self.aliases.filter(
            language_code=language_code,
            status='resolved'
        ).order_by('-usage_count').first()


# SKILL ALIAS

class SkillAlias(models.Model):
    """
    Raw skill strings extracted from jobs, CVs, etc.
    Links to canonical skill after resolution.
    
    Workflow:
    1. Ingestion: skill_id=NULL, status='unresolved'
    2. Resolution: skill_id assigned, status='resolved'
    3. Job linking: Use skill_id to create job_skills
    
    Example:
        alias_text: "Питон"
        language_code: "ru"
        skill_id: → Skill(name_en="Python")
        status: "resolved"
        confidence: 0.95
    """

    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ru', _('Russian')),
        ('uz', _('Uzbek')),
    ]

    SOURCE_CHOICES = [
        ('hh.uz', _('HH.uz API')),
        ('cv', _('User CV')),
        ('manual', _('Manual Entry')),
        ('ai_extracted', _('AI Extracted')),
    ]

    STATUS_CHOICES = [
        ('unresolved', _('Unresolved')),
        ('resolved', _('Resolved')),
        ('rejected', _('Rejected')),
        ('needs_review', _('Needs Review')),
    ]

    alias_id = models.AutoField(primary_key=True)

    # Link to canonical skill (nullable during ingestion)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aliases',
        verbose_name=_('skill'),
        help_text=_("Resolved canonical skill (NULL until resolved)")
    )

    # Raw extracted data
    alias_text = models.CharField(
        _('alias text'),
        max_length=200,
        db_index=True,
        help_text=_("Raw text as extracted: 'Python', 'Питон', 'PYTHON'")
    )

    language_code = models.CharField(
        _('language'),
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='en'
    )

    source = models.CharField(
        _('source'),
        max_length=20,
        choices=SOURCE_CHOICES,
        default='hh.uz'
    )

    # Resolution metadata
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='unresolved',
        db_index=True
    )

    confidence = models.DecimalField(
        _('confidence'),
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Confidence score 0.00-1.00 for skill mapping")
    )

    # Statistics
    usage_count = models.IntegerField(
        _('usage count'),
        default=0,
        help_text=_("How many times this alias appears in data")
    )

    # Timestamps
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        db_table = 'skill_aliases'
        ordering = ['-usage_count', 'alias_text']
        verbose_name = _('skill alias')
        verbose_name_plural = _('skill aliases')
        
        # Unique constraint: same text + language + source = same alias
        unique_together = [('alias_text', 'language_code', 'source')]
        
        indexes = [
            models.Index(fields=['skill']),
            models.Index(fields=['status']),
            models.Index(fields=['language_code']),
            models.Index(fields=['alias_text']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        if self.skill:
            return f"{self.alias_text} → {self.skill.name_en} [{self.status}]"
        return f"{self.alias_text} [{self.status}]"

    def is_resolved(self):
        """Check if alias is resolved to a canonical skill."""
        return self.status == 'resolved' and self.skill_id is not None


# USER SKILL

class UserSkill(models.Model):
    """
    Skills that users possess.
    Links directly to canonical Skill, not to aliases.
    """

    PROFICIENCY_LEVELS = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert')),
    ]

    SOURCE_CHOICES = [
        ('cv', _('From CV')),
        ('manual', _('Manual')),
        ('completed_learning', _('Completed Learning')),
        ('assessment', _('Career Assessment')),
    ]

    user_skill_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name=_('user')
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_skills',
        verbose_name=_('skill')
    )

    proficiency_level = models.CharField(
        _('proficiency level'),
        max_length=20,
        choices=PROFICIENCY_LEVELS,
        default='beginner'
    )

    years_of_experience = models.FloatField(
        _('years of experience'),
        default=0.0
    )

    source = models.CharField(
        _('source'),
        max_length=30,
        choices=SOURCE_CHOICES,
        default='manual'
    )

    is_primary = models.BooleanField(
        _('primary skill'),
        default=False
    )

    added_at = models.DateTimeField(
        _('added at'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        db_table = 'user_skills'
        unique_together = [('user', 'skill')]
        ordering = ['-is_primary', 'skill__name_en']
        verbose_name = _('user skill')
        verbose_name_plural = _('user skills')

    def __str__(self):
        return f"{self.user.email} – {self.skill.name_en}"


# SKILL GAP

class SkillGap(models.Model):
    """
    Missing skills for target role.
    Links directly to canonical Skill, not to aliases.
    """

    IMPORTANCE_CHOICES = [
        ('core', _('Core')),
        ('secondary', _('Secondary')),
    ]

    PRIORITY_CHOICES = [
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('learning', _('Learning')),
        ('completed', _('Completed')),
        ('skipped', _('Skipped')),
    ]

    gap_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skill_gaps',
        verbose_name=_('user')
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='gaps',
        verbose_name=_('skill')
    )

    importance = models.CharField(
        _('importance'),
        max_length=20,
        choices=IMPORTANCE_CHOICES,
        default='secondary'
    )

    demand_priority = models.CharField(
        _('priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    identified_at = models.DateTimeField(
        _('identified at'),
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        db_table = 'skill_gaps'
        unique_together = [('user', 'skill')]
        verbose_name = _('skill gap')
        verbose_name_plural = _('skill gaps')

    def __str__(self):
        return f"{self.user.email} – gap: {self.skill.name_en}"
