"""
Career Assessment Models
========================
backend/apps/career/models.py
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ITRole(models.Model):
    """IT career roles."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Category weights (0-10) for matching
    problem_solving_weight = models.IntegerField(default=5)
    creativity_weight = models.IntegerField(default=5)
    data_analysis_weight = models.IntegerField(default=5)
    technical_depth_weight = models.IntegerField(default=5)
    communication_weight = models.IntegerField(default=5)
    visual_design_weight = models.IntegerField(default=5)
    
    # Work style
    independent_work = models.BooleanField(default=False)
    collaborative_work = models.BooleanField(default=True)
    fast_paced = models.BooleanField(default=True)
    
    # Difficulty
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner Friendly'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='beginner'
    )
    
    # Market info
    avg_salary_uzs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    job_demand = models.CharField(
        max_length=20,
        choices=[('very_high', 'Very High'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='medium'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AssessmentQuestion(models.Model):
    """Assessment questions."""
    
    category = models.CharField(
        max_length=50,
        choices=[
            ('interests', 'Interests'),
            ('aptitudes', 'Aptitudes'),
            ('work_style', 'Work Style'),
            ('learning', 'Learning'),
            ('goals', 'Goals')
        ]
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=[('multiple_choice', 'Multiple Choice'), ('rating', 'Rating')],
        default='multiple_choice'
    )
    
    # Options with category scores
    # Format: [{'text': '...', 'scores': {'problem_solving': 8, 'creativity': 3}}]
    options = models.JSONField(default=list)
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.category}: {self.question_text[:50]}"


class UserAssessment(models.Model):
    """User's assessment."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='career_assessment')
    
    # Responses: {question_id: selected_option_index}
    responses = models.JSONField(default=dict)
    
    # Calculated scores (0-10)
    problem_solving_score = models.FloatField(default=0.0)
    creativity_score = models.FloatField(default=0.0)
    data_analysis_score = models.FloatField(default=0.0)
    technical_depth_score = models.FloatField(default=0.0)
    communication_score = models.FloatField(default=0.0)
    visual_design_score = models.FloatField(default=0.0)
    
    # Work style (from answers)
    prefers_independent = models.BooleanField(null=True, blank=True)
    prefers_collaborative = models.BooleanField(null=True, blank=True)
    prefers_fast_paced = models.BooleanField(null=True, blank=True)
    
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Assessment: {self.user.email}"


class CareerRecommendation(models.Model):
    """Career recommendations."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_recommendations')
    role = models.ForeignKey(ITRole, on_delete=models.CASCADE)
    
    match_score = models.FloatField(help_text="0-100")
    rank = models.IntegerField(help_text="1=top")
    reasoning = models.TextField(blank=True, help_text="AI-generated")
    
    user_selected = models.BooleanField(default=False)
    user_viewed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['user', 'rank']
        unique_together = ['user', 'role']
    
    def __str__(self):
        return f"{self.user.email} → {self.role.name} ({self.match_score:.0f}%)"