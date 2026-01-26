"""
Skills App Models
=================
Models for skill management, user skills, skill gaps, and skill normalization.

Tables:
- Skill
- UserSkill
- SkillGap
- SkillMapping
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import User


class Skill(models.Model):
    """
    Master skill database.
    Stores all skills in normalized English with translations.
    """
    
    SKILL_CATEGORIES = [
        ('programming', _('Programming Language')),
        ('framework', _('Framework')),
        ('library', _('Library')),
        ('tool', _('Tool/Software')),
        ('database', _('Database')),
        ('cloud', _('Cloud Platform')),
        ('soft_skill', _('Soft Skill')),
        ('methodology', _('Methodology')),
        ('other', _('Other')),
    ]
    
    skill_id = models.AutoField(
        primary_key=True
    )
    skill_name = models.CharField(
        _('skill name'),
        max_length=100,
        unique=True,
        help_text=_('Normalized skill name in English.')
    )
    category = models.CharField(
        _('category'),
        max_length=50,
        choices=SKILL_CATEGORIES,
        default='other',
        help_text=_('Skill category type.')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Brief description of the skill.')
    )
    translations = models.JSONField(
        _('translations'),
        default=dict,
        blank=True,
        help_text=_('Translations: {"ru": "Python", "uz": "Python"}')
    )
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether this skill has been manually verified.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('skill')
        verbose_name_plural = _('skills')
        ordering = ['skill_name']
        db_table = 'skills'
        indexes = [
            models.Index(fields=['skill_name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.skill_name
    
    def get_translated_name(self, language='en'):
        """
        Get skill name in specified language.
        Falls back to English if translation not available.
        """
        if language == 'en':
            return self.skill_name
        return self.translations.get(language, self.skill_name)


class SkillMapping(models.Model):
    """
    Maps various skill name variations to normalized skills.
    Helps with deduplication and translation tracking.
    """
    
    LANGUAGES = [
        ('en', _('English')),
        ('ru', _('Russian')),
        ('uz', _('Uzbek')),
    ]
    
    SOURCES = [
        ('hh.uz', _('hh.uz Job Posting')),
        ('cv', _('User CV')),
        ('manual', _('Manual Entry')),
        ('ai_extracted', _('AI Extracted')),
    ]
    
    mapping_id = models.AutoField(
        primary_key=True
    )
    original_text = models.CharField(
        _('original text'),
        max_length=200,
        help_text=_('Original skill text as extracted.')
    )
    normalized_skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='mappings',
        verbose_name=_('normalized skill')
    )
    language = models.CharField(
        _('language'),
        max_length=2,
        choices=LANGUAGES,
        help_text=_('Language of original text.')
    )
    source = models.CharField(
        _('source'),
        max_length=20,
        choices=SOURCES,
        help_text=_('Where this mapping came from.')
    )
    confidence_score = models.FloatField(
        _('confidence score'),
        default=1.0,
        help_text=_('Confidence in this mapping (0.0-1.0).')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('skill mapping')
        verbose_name_plural = _('skill mappings')
        ordering = ['-created_at']
        db_table = 'skill_mappings'
        unique_together = [['original_text', 'language', 'source']]
        indexes = [
            models.Index(fields=['original_text']),
            models.Index(fields=['normalized_skill']),
        ]
    
    def __str__(self):
        return f"{self.original_text} → {self.normalized_skill.skill_name}"


class UserSkill(models.Model):
    """
    Skills that users possess.
    Tracks proficiency, experience, and source.
    """
    
    PROFICIENCY_LEVELS = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert')),
    ]
    
    SKILL_SOURCES = [
        ('cv', _('From CV')),
        ('manual', _('Manually Added')),
        ('completed_learning', _('Completed from Roadmap')),
        ('assessment', _('From Career Assessment')),
    ]
    
    user_skill_id = models.AutoField(
        primary_key=True
    )
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
        default='beginner',
        help_text=_('User proficiency in this skill.')
    )
    years_of_experience = models.FloatField(
        _('years of experience'),
        default=0.0,
        help_text=_('Years of experience with this skill.')
    )
    source = models.CharField(
        _('source'),
        max_length=30,
        choices=SKILL_SOURCES,
        default='manual',
        help_text=_('How this skill was added.')
    )
    is_primary = models.BooleanField(
        _('primary skill'),
        default=False,
        help_text=_('Whether this is a primary/core skill for the user.')
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
        verbose_name = _('user skill')
        verbose_name_plural = _('user skills')
        ordering = ['-is_primary', '-proficiency_level', 'skill__skill_name']
        db_table = 'user_skills'
        unique_together = [['user', 'skill']]
        indexes = [
            models.Index(fields=['user', 'skill']),
            models.Index(fields=['proficiency_level']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.skill.skill_name} ({self.proficiency_level})"


class SkillGap(models.Model):
    """
    Identified skill gaps for users.
    Shows missing skills needed for target role.
    """
    
    IMPORTANCE_LEVELS = [
        ('core', _('Core/Essential')),
        ('secondary', _('Secondary/Nice to Have')),
    ]
    
    PRIORITY_LEVELS = [
        ('high', _('High Priority')),
        ('medium', _('Medium Priority')),
        ('low', _('Low Priority')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('learning', _('Currently Learning')),
        ('completed', _('Completed')),
        ('skipped', _('Skipped')),
    ]
    
    gap_id = models.AutoField(
        primary_key=True
    )
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
        choices=IMPORTANCE_LEVELS,
        default='secondary',
        help_text=_('How important this skill is for target role.')
    )
    demand_priority = models.CharField(
        _('demand priority'),
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='medium',
        help_text=_('Priority based on market demand.')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text=_('Current learning status.')
    )
    target_proficiency = models.CharField(
        _('target proficiency'),
        max_length=20,
        choices=UserSkill.PROFICIENCY_LEVELS,
        default='intermediate',
        help_text=_('Target proficiency level to achieve.')
    )
    estimated_learning_hours = models.IntegerField(
        _('estimated learning hours'),
        default=0,
        help_text=_('Estimated hours needed to learn this skill.')
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
        verbose_name = _('skill gap')
        verbose_name_plural = _('skill gaps')
        ordering = ['-importance', '-demand_priority', 'skill__skill_name']
        db_table = 'skill_gaps'
        unique_together = [['user', 'skill']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['importance', 'demand_priority']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Gap: {self.skill.skill_name}"
    
    def mark_as_completed(self):
        """
        Mark skill gap as completed and add to user's skills.
        """
        self.status = 'completed'
        self.save()
        
        # Add to user's skills if not already exists
        UserSkill.objects.get_or_create(
            user=self.user,
            skill=self.skill,
            defaults={
                'proficiency_level': self.target_proficiency,
                'source': 'completed_learning'
            }
        )