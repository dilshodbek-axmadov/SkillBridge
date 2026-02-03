"""
Career Admin
============
backend/apps/career/admin.py
"""

from django.contrib import admin
from .models import ITRole, AssessmentQuestion, UserAssessment, CareerRecommendation


@admin.register(ITRole)
class ITRoleAdmin(admin.ModelAdmin):
    """Admin for IT roles."""
    
    list_display = ['name', 'difficulty_level', 'job_demand', 'avg_salary_uzs', 'is_active']
    list_filter = ['difficulty_level', 'job_demand', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description')
        }),
        ('Category Weights (0-10)', {
            'fields': (
                'problem_solving_weight',
                'creativity_weight',
                'data_analysis_weight',
                'technical_depth_weight',
                'communication_weight',
                'visual_design_weight'
            )
        }),
        ('Work Style', {
            'fields': ('independent_work', 'collaborative_work', 'fast_paced')
        }),
        ('Market Info', {
            'fields': ('difficulty_level', 'avg_salary_uzs', 'job_demand')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    """Admin for assessment questions."""
    
    list_display = ['order', 'category', 'short_text', 'question_type', 'is_active']
    list_filter = ['category', 'question_type', 'is_active']
    search_fields = ['question_text']
    ordering = ['order']
    
    def short_text(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    short_text.short_description = 'Question'


@admin.register(UserAssessment)
class UserAssessmentAdmin(admin.ModelAdmin):
    """Admin for user assessments."""
    
    list_display = ['user', 'completed', 'completed_at', 'created_at']
    list_filter = ['completed', 'completed_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Scores', {
            'fields': (
                'problem_solving_score',
                'creativity_score',
                'data_analysis_score',
                'technical_depth_score',
                'communication_score',
                'visual_design_score'
            )
        }),
        ('Work Style', {
            'fields': ('prefers_independent', 'prefers_collaborative', 'prefers_fast_paced')
        }),
        ('Status', {
            'fields': ('completed', 'completed_at', 'created_at')
        })
    )


@admin.register(CareerRecommendation)
class CareerRecommendationAdmin(admin.ModelAdmin):
    """Admin for career recommendations."""
    
    list_display = ['user', 'role', 'rank', 'match_score', 'user_selected', 'created_at']
    list_filter = ['user_selected', 'role']
    search_fields = ['user__email', 'role__name']
    ordering = ['user', 'rank']
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Recommendation', {
            'fields': ('user', 'role', 'rank', 'match_score')
        }),
        ('Reasoning', {
            'fields': ('reasoning',)
        }),
        ('User Action', {
            'fields': ('user_selected', 'user_viewed')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        })
    )