"""
Users App Models
================
Models for user authentication and profile management.

Tables:
- User (extends Django's AbstractUser)
- UserProfile
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Handles authentication and basic user information.
    """

    class UserType(models.TextChoices):
        DEVELOPER = 'developer', _('Developer')
        RECRUITER = 'recruiter', _('Recruiter')

    class RecruiterPlan(models.TextChoices):
        FREE = 'free', _('Free')
        PRO = 'pro', _('Pro')

    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. Enter a valid email address.')
    )
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Optional. User phone number.')
    )
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=2,
        choices=[
            ('en', _('English')),
            ('ru', _('Russian')),
            ('uz', _('Uzbek')),
        ],
        default='en',
        help_text=_('User preferred interface language.')
    )
    user_type = models.CharField(
        _('user type'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.DEVELOPER,
        db_index=True,
        help_text=_('Developer (talent) or recruiter (employer) account; set at registration.'),
    )
    recruiter_plan = models.CharField(
        _('recruiter plan'),
        max_length=10,
        choices=RecruiterPlan.choices,
        default=RecruiterPlan.FREE,
        help_text=_('Subscription tier for recruiter accounts; ignored for developers.'),
    )
    profile_completed = models.BooleanField(
        _('profile completed'),
        default=False,
        help_text=_('Whether user has completed initial profile setup.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    last_login = models.DateTimeField(
        _('last login'),
        blank=True,
        null=True
    )
    
    # Use email as username for login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        db_table = 'users'
        indexes = [
            models.Index(fields=['user_type', '-created_at']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_developer(self) -> bool:
        return self.user_type == self.UserType.DEVELOPER

    @property
    def is_recruiter_account(self) -> bool:
        return self.user_type == self.UserType.RECRUITER

    @property
    def is_recruiter_pro(self) -> bool:
        return self.is_recruiter_account and self.recruiter_plan == self.RecruiterPlan.PRO


class UserProfile(models.Model):
    """
    Extended user profile information.
    Stores career-related information and preferences.
    """
    
    EXPERIENCE_LEVELS = [
        ('beginner', _('Beginner')),
        ('junior', _('Junior')),
        ('mid', _('Mid-level')),
        ('senior', _('Senior')),
        ('lead', _('Lead/Principal')),
    ]
    
    PROFILE_SOURCES = [
        ('manual', _('Manual Entry')),
        ('cv_upload', _('CV Upload')),
        ('assessment', _('Career Assessment')),
    ]
    
    profile_id = models.AutoField(
        primary_key=True
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user')
    )
    current_job_position = models.CharField(
        _('current job position'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('User current job title or position.')
    )
    desired_role = models.CharField(
        _('desired role'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Target career role user wants to achieve.')
    )
    experience_level = models.CharField(
        _('experience level'),
        max_length=20,
        choices=EXPERIENCE_LEVELS,
        default='beginner',
        help_text=_('User current experience level in IT.')
    )
    cv_file_path = models.FileField(
        _('CV file'),
        upload_to='cvs/%Y/%m/',
        blank=True,
        null=True,
        help_text=_('Uploaded CV file (PDF or DOCX).')
    )
    profile_source = models.CharField(
        _('profile source'),
        max_length=20,
        choices=PROFILE_SOURCES,
        default='manual',
        help_text=_('How the profile was created.')
    )
    bio = models.TextField(
        _('bio'),
        blank=True,
        null=True,
        help_text=_('User biography or summary.')
    )
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pics/%Y/%m/',
        blank=True,
        null=True
    )
    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('User city or region.')
    )
    github_url = models.URLField(
        _('GitHub URL'),
        blank=True,
        null=True
    )
    linkedin_url = models.URLField(
        _('LinkedIn URL'),
        blank=True,
        null=True
    )
    portfolio_url = models.URLField(
        _('Portfolio URL'),
        blank=True,
        null=True
    )
    # —— Developer: visibility in recruiter search ——
    open_to_recruiters = models.BooleanField(
        _('open to recruiters'),
        default=True,
        help_text=_(
            'If true, this developer profile may appear in recruiter search (subject to product rules).'
        ),
    )
    # —— Recruiter: organization (optional; developers leave blank) ——
    company_name = models.CharField(
        _('company name'),
        max_length=255,
        blank=True,
        help_text=_('Employer or agency name; used for recruiter accounts.'),
    )
    company_website = models.URLField(
        _('company website'),
        blank=True,
        null=True,
    )
    company_description = models.TextField(
        _('company description'),
        blank=True,
        help_text=_('Short company overview for candidate-facing pages.'),
    )
    recruiter_title = models.CharField(
        _('recruiter title at company'),
        max_length=200,
        blank=True,
        help_text=_('e.g. HR Business Partner, Technical Recruiter.'),
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
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        db_table = 'user_profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - Profile"
    
    @property
    def is_complete(self):
        """Check if profile has minimum required information."""
        return bool(
            self.current_job_position or self.desired_role
        ) and self.user.profile_completed


class UserActivity(models.Model):
    """Append-only log of user-visible actions for dashboard activity feeds."""

    class ActivityType(models.TextChoices):
        ACCOUNT_CREATED = 'account_created', _('Account created')
        PROFILE_SETUP = 'profile_setup', _('Profile set up')
        CV_UPLOADED = 'cv_uploaded', _('CV uploaded')
        SKILL_ADDED = 'skill_added', _('Skill added')
        SKILLS_BULK_ADDED = 'skills_bulk_added', _('Skills bulk added')
        SKILL_REMOVED = 'skill_removed', _('Skill removed')
        GAP_ANALYZED = 'gap_analyzed', _('Skill gap analyzed')
        GAP_STATUS = 'gap_status', _('Skill gap updated')
        GAPS_CLEARED = 'gaps_cleared', _('Skill gaps cleared')
        ROADMAP_CREATED = 'roadmap_created', _('Learning roadmap created')
        ROADMAP_PROGRESS = 'roadmap_progress', _('Roadmap progress')

    activity_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('user'),
    )
    activity_type = models.CharField(
        _('activity type'),
        max_length=32,
        choices=ActivityType.choices,
    )
    description = models.CharField(_('description'), max_length=500)
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    link_path = models.CharField(_('link path'), max_length=200, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user_id} {self.activity_type} @ {self.created_at}'