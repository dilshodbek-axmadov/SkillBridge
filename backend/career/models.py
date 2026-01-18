from django.db import models
from django.conf import settings
from skills.models import SkillLevel, Skill
from jobs.models import JobCategory

class Role(models.Model):
    """
    IT roles/positions (Backend Developer, Frontend Developer, etc.)
    """
    title = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='roles'
    )
    description = models.TextField()
    average_salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    average_salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    demand_score = models.FloatField(
        default=0.0,
        help_text="How in-demand this role is (0-100)"
    )
    growth_potential = models.FloatField(
        default=0.0,
        help_text="Career growth potential (0-100)"
    )
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['-demand_score', 'title']
    
    def __str__(self):
        return self.title
    
    def get_required_skills(self):
        """Get all required skills for this role"""
        return self.role_required_skills.select_related('skill')
    
    def calculate_demand_score(self):
        """Calculate demand based on job postings"""
        from jobs.models import JobPosting
        from django.db.models import Q
        
        # Count jobs that match this role title
        job_count = JobPosting.objects.filter(
            Q(title__icontains=self.title) | 
            Q(description_text__icontains=self.title),
            is_active=True
        ).count()
        
        # Simple scoring: 1 job = 5 points, cap at 100
        self.demand_score = min(job_count * 5, 100)
        self.save(update_fields=['demand_score'])
        return self.demand_score
    

class RoleRequiredSkill(models.Model):
    """
    Skills required for each role
    """
    IMPORTANCE_CHOICES = [
        ('critical', 'Critical'),
        ('important', 'Important'),
        ('nice_to_have', 'Nice to Have'),
    ]
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_required_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='role_requirements'
    )
    importance = models.CharField(
        max_length=20,
        choices=IMPORTANCE_CHOICES,
        default='important'
    )
    minimum_level = models.ForeignKey(
        SkillLevel,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_requirements'
    )
    
    class Meta:
        db_table = 'role_required_skills'
        verbose_name = 'Role Required Skill'
        verbose_name_plural = 'Role Required Skills'
        unique_together = ['role', 'skill']
        ordering = ['importance', 'skill__name']
    
    def __str__(self):
        return f"{self.role.title} - {self.skill.name} ({self.importance})"


class UserRecommendedRole(models.Model):
    """
    Roles recommended to users based on their skills
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommended_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_recommendations'
    )
    match_percentage = models.FloatField(
        help_text="How well user's skills match this role (0-100)"
    )
    readiness_score = models.FloatField(
        help_text="How ready user is for this role (0-100)"
    )
    missing_skills_count = models.IntegerField(
        default=0,
        help_text="Number of skills user is missing"
    )
    recommendation_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_recommended_roles'
        verbose_name = 'User Recommended Role'
        verbose_name_plural = 'User Recommended Roles'
        ordering = ['-match_percentage', '-readiness_score']
        unique_together = ['user', 'role']
    
    def __str__(self):
        return f"{self.user.email} - {self.role.title} ({self.match_percentage:.1f}%)"


class SkillGapAnalysis(models.Model):
    """
    Analysis of skill gaps between user and target role
    """
    READINESS_CHOICES = [
        ('not_ready', 'Not Ready'),
        ('partially_ready', 'Partially Ready'),
        ('job_ready', 'Job Ready'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_gap_analyses'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='gap_analyses'
    )
    analysis_date = models.DateTimeField(auto_now_add=True)
    overall_match_percentage = models.FloatField()
    readiness_level = models.CharField(
        max_length=20,
        choices=READINESS_CHOICES
    )
    estimated_learning_time_weeks = models.IntegerField(
        help_text="Estimated weeks to become job-ready"
    )
    
    class Meta:
        db_table = 'skill_gap_analysis'
        verbose_name = 'Skill Gap Analysis'
        verbose_name_plural = 'Skill Gap Analyses'
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.role.title} ({self.analysis_date.date()})"


class MissingSkill(models.Model):
    """
    Individual skills missing from user's profile for a role
    """
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    gap_analysis = models.ForeignKey(
        SkillGapAnalysis,
        on_delete=models.CASCADE,
        related_name='missing_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='identified_gaps'
    )
    required_level = models.ForeignKey(
        SkillLevel,
        on_delete=models.SET_NULL,
        null=True,
        related_name='required_for_gaps'
    )
    current_level = models.ForeignKey(
        SkillLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_in_gaps'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    estimated_learning_weeks = models.IntegerField(
        default=4,
        help_text="Estimated weeks to learn this skill"
    )
    
    class Meta:
        db_table = 'missing_skills'
        verbose_name = 'Missing Skill'
        verbose_name_plural = 'Missing Skills'
        ordering = ['priority', 'skill__name']
    
    def __str__(self):
        return f"{self.skill.name} (Priority: {self.priority})"