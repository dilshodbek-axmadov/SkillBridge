"""
Career App Models
=================
Models for career assessment, recommendations, and role matching.

Tables:
- CareerQuestion
- QuestionOption
- CareerRole
- RoleMatchingRule
- UserCareerAssessment
- AssessmentAnswer
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import User


class CareerQuestion(models.Model):
    """
    Career assessment questions to help match users with IT roles.
    Multi-language support for EN/RU/UZ.
    """
    
    QUESTION_CATEGORIES = [
        ('interest', _('Interest & Passion')),
        ('work_environment', _('Work Environment')),
        ('work_style', _('Work Style')),
        ('skills', _('Skills & Strengths')),
        ('goals', _('Career Goals')),
    ]
    
    QUESTION_TYPES = [
        ('single_choice', _('Single Choice')),
        ('multiple_choice', _('Multiple Choice')),
        ('rating', _('Rating Scale')),
    ]
    
    question_id = models.AutoField(
        primary_key=True
    )
    category = models.CharField(
        _('category'),
        max_length=50,
        choices=QUESTION_CATEGORIES,
        help_text=_('Question category.')
    )
    question_text_en = models.TextField(
        _('question text (English)'),
        help_text=_('Question text in English.')
    )
    question_text_ru = models.TextField(
        _('question text (Russian)'),
        help_text=_('Question text in Russian.')
    )
    question_text_uz = models.TextField(
        _('question text (Uzbek)'),
        help_text=_('Question text in Uzbek.')
    )
    question_type = models.CharField(
        _('question type'),
        max_length=20,
        choices=QUESTION_TYPES,
        default='single_choice',
        help_text=_('Type of question.')
    )
    sequence_order = models.IntegerField(
        _('sequence order'),
        help_text=_('Order in which question appears (1, 2, 3...).')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this question is currently active.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('career question')
        verbose_name_plural = _('career questions')
        ordering = ['sequence_order']
        db_table = 'career_questions'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['sequence_order']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Q{self.sequence_order}: {self.question_text_en[:50]}"
    
    def get_question_text(self, language='en'):
        """Get question text in specified language."""
        return getattr(self, f'question_text_{language}', self.question_text_en)


class QuestionOption(models.Model):
    """
    Answer options for career assessment questions.
    Multi-language support.
    """
    
    option_id = models.AutoField(
        primary_key=True
    )
    question = models.ForeignKey(
        CareerQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('question')
    )
    option_text_en = models.CharField(
        _('option text (English)'),
        max_length=500,
        help_text=_('Option text in English.')
    )
    option_text_ru = models.CharField(
        _('option text (Russian)'),
        max_length=500,
        help_text=_('Option text in Russian.')
    )
    option_text_uz = models.CharField(
        _('option text (Uzbek)'),
        max_length=500,
        help_text=_('Option text in Uzbek.')
    )
    option_value = models.CharField(
        _('option value'),
        max_length=100,
        help_text=_('Internal value for matching logic.')
    )
    display_order = models.IntegerField(
        _('display order'),
        help_text=_('Order in which option is displayed.')
    )
    icon_name = models.CharField(
        _('icon name'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Icon identifier for UI display.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('question option')
        verbose_name_plural = _('question options')
        ordering = ['question', 'display_order']
        db_table = 'question_options'
        indexes = [
            models.Index(fields=['question', 'display_order']),
        ]
    
    def __str__(self):
        return f"{self.question.sequence_order}.{self.display_order}: {self.option_text_en[:40]}"
    
    def get_option_text(self, language='en'):
        """Get option text in specified language."""
        return getattr(self, f'option_text_{language}', self.option_text_en)


class CareerRole(models.Model):
    """
    IT career roles with attributes for matching algorithm.
    Multi-language support for names and descriptions.
    """
    
    ROLE_CATEGORIES = [
        ('development', _('Software Development')),
        ('data', _('Data & Analytics')),
        ('design', _('Design & UX')),
        ('infrastructure', _('Infrastructure & DevOps')),
        ('security', _('Security')),
        ('management', _('Management & Product')),
        ('other', _('Other')),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner_friendly', _('Beginner Friendly')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    ]
    
    role_id = models.AutoField(
        primary_key=True
    )
    role_name = models.CharField(
        _('role name (English)'),
        max_length=200,
        unique=True,
        help_text=_('Role name in English (e.g., "Frontend Developer").')
    )
    role_name_ru = models.CharField(
        _('role name (Russian)'),
        max_length=200,
        help_text=_('Role name in Russian.')
    )
    role_name_uz = models.CharField(
        _('role name (Uzbek)'),
        max_length=200,
        help_text=_('Role name in Uzbek.')
    )
    category = models.CharField(
        _('category'),
        max_length=50,
        choices=ROLE_CATEGORIES,
        default='development',
        help_text=_('Role category.')
    )
    description_en = models.TextField(
        _('description (English)'),
        help_text=_('Role description in English.')
    )
    description_ru = models.TextField(
        _('description (Russian)'),
        help_text=_('Role description in Russian.')
    )
    description_uz = models.TextField(
        _('description (Uzbek)'),
        help_text=_('Role description in Uzbek.')
    )
    average_salary_uzb = models.DecimalField(
        _('average salary (UZS)'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Average salary in Uzbekistan (UZS).')
    )
    difficulty_level = models.CharField(
        _('difficulty level'),
        max_length=30,
        choices=DIFFICULTY_LEVELS,
        default='intermediate',
        help_text=_('Entry difficulty for beginners.')
    )
    demand_score = models.IntegerField(
        _('demand score'),
        default=5,
        help_text=_('Market demand score (1-10).')
    )
    work_alone_score = models.IntegerField(
        _('work alone score'),
        default=5,
        help_text=_('How much solo work (1-10).')
    )
    work_team_score = models.IntegerField(
        _('work team score'),
        default=5,
        help_text=_('How much team work (1-10).')
    )
    creative_score = models.IntegerField(
        _('creative score'),
        default=5,
        help_text=_('How creative the role is (1-10).')
    )
    analytical_score = models.IntegerField(
        _('analytical score'),
        default=5,
        help_text=_('How analytical the role is (1-10).')
    )
    remote_friendly = models.BooleanField(
        _('remote friendly'),
        default=True,
        help_text=_('Whether role allows remote work.')
    )
    typical_learning_months = models.IntegerField(
        _('typical learning time (months)'),
        default=6,
        help_text=_('Typical time to become job-ready (months).')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('career role')
        verbose_name_plural = _('career roles')
        ordering = ['role_name']
        db_table = 'career_roles'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['demand_score']),
        ]
    
    def __str__(self):
        return self.role_name
    
    def get_role_name(self, language='en'):
        """Get role name in specified language."""
        return getattr(self, f'role_name_{language}', self.role_name)
    
    def get_description(self, language='en'):
        """Get description in specified language."""
        return getattr(self, f'description_{language}', self.description_en)


class RoleMatchingRule(models.Model):
    """
    Matching rules that connect question options to career roles.
    Used by recommendation algorithm.
    """
    
    MATCH_TYPES = [
        ('positive', _('Positive Match')),
        ('negative', _('Negative Match')),
        ('required', _('Required/Critical')),
    ]
    
    rule_id = models.AutoField(
        primary_key=True
    )
    role = models.ForeignKey(
        CareerRole,
        on_delete=models.CASCADE,
        related_name='matching_rules',
        verbose_name=_('role')
    )
    question_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        related_name='matching_rules',
        verbose_name=_('question option')
    )
    match_weight = models.IntegerField(
        _('match weight'),
        default=5,
        help_text=_('Importance of this match (1-10).')
    )
    match_type = models.CharField(
        _('match type'),
        max_length=20,
        choices=MATCH_TYPES,
        default='positive',
        help_text=_('Type of match.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('role matching rule')
        verbose_name_plural = _('role matching rules')
        ordering = ['role', '-match_weight']
        db_table = 'role_matching_rules'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['question_option']),
        ]
    
    def __str__(self):
        return f"{self.role.role_name} ← {self.question_option.option_value} ({self.match_weight})"


class UserCareerAssessment(models.Model):
    """
    User career assessment results and recommendations.
    """
    
    assessment_id = models.AutoField(
        primary_key=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='career_assessments',
        verbose_name=_('user')
    )
    assessment_data = models.JSONField(
        _('assessment data'),
        help_text=_('Complete assessment answers as JSON.')
    )
    recommended_roles = models.JSONField(
        _('recommended roles'),
        help_text=_('AI-recommended roles with scores.')
    )
    selected_role = models.ForeignKey(
        CareerRole,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='selected_by_users',
        verbose_name=_('selected role'),
        help_text=_('Role user finally selected.')
    )
    completed_at = models.DateTimeField(
        _('completed at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('user career assessment')
        verbose_name_plural = _('user career assessments')
        ordering = ['-completed_at']
        db_table = 'user_career_assessments'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['completed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Assessment {self.assessment_id}"


class AssessmentAnswer(models.Model):
    """
    Individual answers for each question in an assessment.
    """
    
    answer_id = models.AutoField(
        primary_key=True
    )
    assessment = models.ForeignKey(
        UserCareerAssessment,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('assessment')
    )
    question = models.ForeignKey(
        CareerQuestion,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name=_('question')
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        related_name='user_selections',
        verbose_name=_('selected option'),
        blank=True,
        null=True,
        help_text=_('Selected option (for single choice).')
    )
    selected_options = models.ManyToManyField(
        QuestionOption,
        related_name='multi_selections',
        blank=True,
        verbose_name=_('selected options'),
        help_text=_('Multiple selected options (for multiple choice).')
    )
    answer_text = models.TextField(
        _('answer text'),
        blank=True,
        null=True,
        help_text=_('Text answer for open-ended questions.')
    )
    answered_at = models.DateTimeField(
        _('answered at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('assessment answer')
        verbose_name_plural = _('assessment answers')
        ordering = ['assessment', 'question__sequence_order']
        db_table = 'assessment_answers'
        unique_together = [['assessment', 'question']]
        indexes = [
            models.Index(fields=['assessment']),
            models.Index(fields=['question']),
        ]
    
    def __str__(self):
        return f"{self.assessment.user.email} - Q{self.question.sequence_order}"