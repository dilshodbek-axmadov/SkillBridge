# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from .managers import CustomUserManager


class User(AbstractUser):
    """
    Custom User model with email as the primary identifier
    """
    ONBOARDING_CHOICES = [
        ('questionnaire', 'Questionnaire'),
        ('cv_upload', 'CV Upload'),
    ]
    
    username = None  # Remove username field
    email = models.EmailField('email address', unique=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    location = models.CharField(max_length=200, blank=True, null=True)
    onboarding_method = models.CharField(
        max_length=20,
        choices=ONBOARDING_CHOICES,
        blank=True,
        null=True
    )
    profile_completion_percentage = models.IntegerField(default=0)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['registration_date']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Returns the user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def update_profile_completion(self):
        """
        Calculates and updates profile completion percentage
        """
        total_fields = 10
        completed_fields = 0
        
        # Check basic fields
        if self.first_name:
            completed_fields += 1
        if self.last_name:
            completed_fields += 1
        if self.phone:
            completed_fields += 1
        if self.location:
            completed_fields += 1
        if self.onboarding_method:
            completed_fields += 1
            
        # Check if profile exists
        if hasattr(self, 'userprofile'):
            profile = self.userprofile
            if profile.current_role:
                completed_fields += 1
            if profile.experience_level:
                completed_fields += 1
            if profile.bio:
                completed_fields += 1
            if profile.linkedin_url or profile.github_url or profile.portfolio_url:
                completed_fields += 1
                
        # Check if user has skills
        if self.user_skills.exists():
            completed_fields += 1
            
        self.profile_completion_percentage = int((completed_fields / total_fields) * 100)
        self.save(update_fields=['profile_completion_percentage'])
        return self.profile_completion_percentage


class UserProfile(models.Model):
    """
    Extended profile information for users
    """
    EXPERIENCE_LEVELS = [
        ('junior', 'Junior'),
        ('mid', 'Mid-level'),
        ('senior', 'Senior'),
    ]
    
    WORK_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('employed', 'Currently Employed'),
        ('not_looking', 'Not Looking'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile'
    )
    current_role = models.CharField(max_length=100, blank=True, null=True)
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS,
        blank=True,
        null=True
    )
    preferred_work_type = models.CharField(
        max_length=20,
        choices=WORK_TYPE_CHOICES,
        blank=True,
        null=True
    )
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='available'
    )
    bio = models.TextField(blank=True, null=True)
    linkedin_url = models.URLField(max_length=255, blank=True, null=True)
    github_url = models.URLField(max_length=255, blank=True, null=True)
    portfolio_url = models.URLField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
    
    def save(self, *args, **kwargs):
        """Override save to update user's profile completion"""
        super().save(*args, **kwargs)
        self.user.update_profile_completion()


class UserInterest(models.Model):
    """
    Tracks user's areas of interest in IT
    """
    INTEREST_AREAS = [
        ('web_dev', 'Web Development'),
        ('mobile_dev', 'Mobile Development'),
        ('data_science', 'Data Science'),
        ('machine_learning', 'Machine Learning'),
        ('devops', 'DevOps'),
        ('cloud', 'Cloud Computing'),
        ('cybersecurity', 'Cybersecurity'),
        ('game_dev', 'Game Development'),
        ('blockchain', 'Blockchain'),
        ('ui_ux', 'UI/UX Design'),
        ('qa_testing', 'QA/Testing'),
        ('embedded', 'Embedded Systems'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_interests'
    )
    interest_area = models.CharField(max_length=50, choices=INTEREST_AREAS)
    priority_level = models.IntegerField(
        default=1,
        help_text="1 = highest priority, 5 = lowest priority"
    )
    
    class Meta:
        db_table = 'user_interests'
        verbose_name = 'User Interest'
        verbose_name_plural = 'User Interests'
        ordering = ['priority_level', 'interest_area']
        unique_together = ['user', 'interest_area']
        indexes = [
            models.Index(fields=['user', 'priority_level']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_interest_area_display()}"