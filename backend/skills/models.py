from django.db import models
from django.conf import settings
from django.utils import timezone

class Skill(models.Model):
    """ master skills table for all other tables """
    CATEGORY_CHOICES = [
        ('programming_language', 'Programming Language'),
        ('framework', 'Framework'),
        ('tool', 'Tool'),
        ('soft_skill', 'Soft Skill'),
        ('database', 'Database'),
        ('devops', 'DevOps'),
        ('cloud', 'Cloud Platform'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    popularity_score = models.FloatField(
        default=0.0,
        help_text="Calculated from job market demand (0-100)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'skills'
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
        ordering = ['-popularity_score', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['-popularity_score']),
        ]
    
    def __str__(self):
        return self.name
    
    def update_popularity_score(self):
        """
        Calculate popularity based on how many job postings require this skill
        Will be implemented after JobPosting model is created
        """
        from jobs.models import JobSkill
        
        total_jobs = JobSkill.objects.filter(skill=self).count()
        required_jobs = JobSkill.objects.filter(skill=self, is_required=True).count()
        
        # Calculate score: required jobs count more
        score = (required_jobs * 2) + total_jobs
        
        # Normalize to 0-100 scale (you can adjust this formula)
        max_score = 1000  # Assume 1000 is the max possible
        self.popularity_score = min((score / max_score) * 100, 100)
        self.save(update_fields=['popularity_score'])
        
        return self.popularity_score
    
    def get_related_skills(self, limit=5):
        """
        Get skills that commonly appear together with this skill
        Will be implemented after skill_combinations table
        """
        # This will use the skill_combinations model (Phase 3)
        pass


class SkillLevel(models.Model):
    """
    Proficiency levels for skills
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    level_order = models.IntegerField(
        unique=True,
        help_text="Order of skill level (1=Beginner, 2=Intermediate, etc.)"
    )
    
    class Meta:
        db_table = 'skill_levels'
        verbose_name = 'Skill Level'
        verbose_name_plural = 'Skill Levels'
        ordering = ['level_order']
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """
    Junction table tracking user's skills with learning status
    THIS IS YOUR SKILL TRACKING SYSTEM!
    """
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('learned', 'Learned'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_skills'
    )
    level = models.ForeignKey(
        SkillLevel,
        on_delete=models.SET_NULL,
        null=True,
        related_name='user_skills'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    self_assessed = models.BooleanField(
        default=True,
        help_text="True if user added this skill themselves, False if extracted from CV"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    date_marked_learned = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when user marked this skill as learned"
    )
    proof_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional certificate or project link"
    )
    
    class Meta:
        db_table = 'user_skills'
        verbose_name = 'User Skill'
        verbose_name_plural = 'User Skills'
        unique_together = ['user', 'skill']
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['skill', 'level']),
            models.Index(fields=['-date_added']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.skill.name} ({self.get_status_display()})"
    
    def mark_as_learned(self, level=None):
        """
        Mark this skill as learned
        This is called when user completes learning a skill
        IMPORTANT: This triggers automatic CV update!
        """
        self.status = 'learned'
        self.date_marked_learned = timezone.now()
        
        if level:
            self.level = level
        
        self.save(update_fields=['status', 'date_marked_learned', 'level'])
        
        # Update user's profile completion
        self.user.update_profile_completion()
        
        # Trigger CV update (will implement in Phase 5)
        # self.update_user_cv()
        
        return self
    
    def mark_in_progress(self):
        """Mark skill as currently being learned"""
        self.status = 'in_progress'
        self.save(update_fields=['status'])
        return self
    
    def get_learning_duration(self):
        """
        Calculate how long user has been learning this skill
        Returns number of days
        """
        if self.status == 'learned' and self.date_marked_learned:
            delta = self.date_marked_learned - self.date_added
            return delta.days
        elif self.status == 'in_progress':
            delta = timezone.now() - self.date_added
            return delta.days
        return 0
    
    def get_learning_duration_display(self):
        """Get human-readable learning duration"""
        days = self.get_learning_duration()
        
        if days == 0:
            return "Just started"
        elif days < 7:
            return f"{days} day{'s' if days != 1 else ''}"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''}"
        else:
            months = days // 30
            return f"{months} month{'s' if months != 1 else ''}"