"""
Admin configuration for career models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Role, RoleRequiredSkill, UserRecommendedRole,
    SkillGapAnalysis, MissingSkill
)


class RoleRequiredSkillInline(admin.TabularInline):
    """Inline for role required skills"""
    model = RoleRequiredSkill
    extra = 1
    fields = ['skill', 'importance', 'minimum_level']
    autocomplete_fields = ['skill']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin for roles"""
    list_display = [
        'title', 'category', 'demand_score_display',
        'growth_potential_display', 'salary_range', 'required_skills_count'
    ]
    list_filter = ['category', 'demand_score', 'growth_potential']
    search_fields = ['title', 'description']
    readonly_fields = ['demand_score']
    inlines = [RoleRequiredSkillInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'description')
        }),
        ('Salary Range', {
            'fields': ('average_salary_min', 'average_salary_max')
        }),
        ('Metrics', {
            'fields': ('demand_score', 'growth_potential')
        }),
    )
    
    def demand_score_display(self, obj):
        if obj.demand_score >= 70:
            color = 'green'
        elif obj.demand_score >= 40:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            f"{obj.demand_score:.1f}"
        )
    demand_score_display.short_description = 'Demand'
    
    def growth_potential_display(self, obj):
        if obj.growth_potential >= 70:
            color = 'green'
        elif obj.growth_potential >= 40:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            f"{obj.growth_potential:.1f}"
        )
    growth_potential_display.short_description = 'Growth'
    
    def salary_range(self, obj):
        if obj.average_salary_min and obj.average_salary_max:
            return f"{obj.average_salary_min:,.0f} - {obj.average_salary_max:,.0f}"
        return "Not specified"
    salary_range.short_description = 'Salary Range'
    
    def required_skills_count(self, obj):
        return obj.role_required_skills.count()
    required_skills_count.short_description = 'Skills Required'


@admin.register(RoleRequiredSkill)
class RoleRequiredSkillAdmin(admin.ModelAdmin):
    """Admin for role required skills"""
    list_display = ['role', 'skill', 'importance', 'minimum_level']
    list_filter = ['importance', 'minimum_level']
    search_fields = ['role__title', 'skill__name']
    autocomplete_fields = ['role', 'skill']


class MissingSkillInline(admin.TabularInline):
    """Inline for missing skills"""
    model = MissingSkill
    extra = 0
    fields = ['skill', 'priority', 'required_level', 'current_level', 'estimated_learning_weeks']
    readonly_fields = ['skill', 'priority', 'required_level', 'current_level']
    can_delete = False


@admin.register(UserRecommendedRole)
class UserRecommendedRoleAdmin(admin.ModelAdmin):
    """Admin for user recommended roles"""
    list_display = [
        'user', 'role', 'match_percentage_display',
        'readiness_score_display', 'missing_skills_count',
        'recommendation_date', 'is_active'
    ]
    list_filter = ['is_active', 'recommendation_date', 'role']
    search_fields = ['user__email', 'role__title']
    readonly_fields = ['recommendation_date']
    
    def match_percentage_display(self, obj):
        return f"{obj.match_percentage:.1f}%"
    match_percentage_display.short_description = 'Match'
    
    def readiness_score_display(self, obj):
        if obj.readiness_score >= 80:
            color = 'green'
        elif obj.readiness_score >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.readiness_score
        )
    readiness_score_display.short_description = 'Readiness'


@admin.register(SkillGapAnalysis)
class SkillGapAnalysisAdmin(admin.ModelAdmin):
    """Admin for skill gap analysis"""
    list_display = [
        'user', 'role', 'overall_match_percentage',
        'readiness_level', 'estimated_learning_time_weeks',
        'analysis_date'
    ]
    list_filter = ['readiness_level', 'analysis_date']
    search_fields = ['user__email', 'role__title']
    readonly_fields = ['analysis_date']
    inlines = [MissingSkillInline]


@admin.register(MissingSkill)
class MissingSkillAdmin(admin.ModelAdmin):
    """Admin for missing skills"""
    list_display = [
        'gap_analysis', 'skill', 'priority',
        'required_level', 'current_level',
        'estimated_learning_weeks'
    ]
    list_filter = ['priority', 'required_level']
    search_fields = ['skill__name', 'gap_analysis__user__email']