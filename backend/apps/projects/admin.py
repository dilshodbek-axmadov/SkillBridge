"""
Projects App Admin
==================
backend/apps/projects/admin.py

Admin interface for managing project ideas and user projects.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import ProjectIdea, ProjectSkill, UserProject
from django.utils.translation import gettext_lazy as _


class ProjectSkillInline(admin.TabularInline):
    """Inline for project skills."""
    model = ProjectSkill
    extra = 1
    raw_id_fields = ['skill']
    fields = ['skill', 'importance']


@admin.register(ProjectIdea)
class ProjectIdeaAdmin(admin.ModelAdmin):
    """Admin interface for ProjectIdea model."""
    
    list_display = [
        'project_id',
        'title',
        'created_by_email',
        'target_role',
        'difficulty_badge',
        'estimated_hours',
        'skill_count',
        'user_count',
        'created_at'
    ]
    
    list_filter = [
        'difficulty_level',
        'target_role',
        'created_at'
    ]
    
    raw_id_fields = ['created_by']
    
    search_fields = [
        'title',
        'description',
        'target_role'
    ]
    
    ordering = ['difficulty_level', 'title']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('created_by', 'title', 'target_role')
        }),
        (_('Details'), {
            'fields': ('description', 'difficulty_level', 'estimated_hours')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    inlines = [ProjectSkillInline]
    
    def created_by_email(self, obj):
        u = obj.created_by
        return u.email if u else '—'

    created_by_email.short_description = _('Owner')
    created_by_email.admin_order_field = 'created_by__email'

    def difficulty_badge(self, obj):
        """Display difficulty with color badge."""
        colors = {
            'beginner': '#28a745',
            'intermediate': '#ffc107',
            'advanced': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.difficulty_level, '#6c757d'),
            obj.get_difficulty_level_display()
        )
    
    difficulty_badge.short_description = _('Difficulty')
    difficulty_badge.admin_order_field = 'difficulty_level'
    
    def skill_count(self, obj):
        """Count of skills required."""
        return obj.project_skills.count()
    
    skill_count.short_description = _('Skills')
    
    def user_count(self, obj):
        """Count of users working on this project."""
        count = obj.user_projects.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return count
    
    user_count.short_description = _('Users')


@admin.register(ProjectSkill)
class ProjectSkillAdmin(admin.ModelAdmin):
    """Admin interface for ProjectSkill model."""
    
    list_display = [
        'project_skill_id',
        'project_title',
        'skill_name',
        'importance_badge',
    ]
    
    list_filter = [
        'importance',
        'project__difficulty_level'
    ]
    
    search_fields = [
        'project__title',
        'skill__name_en'
    ]
    
    raw_id_fields = ['project', 'skill']
    
    def project_title(self, obj):
        """Display project title."""
        return obj.project.title
    
    project_title.short_description = _('Project')
    project_title.admin_order_field = 'project__title'
    
    def skill_name(self, obj):
        """Display skill name."""
        return obj.skill.name_en
    
    skill_name.short_description = _('Skill')
    skill_name.admin_order_field = 'skill__name_en'
    
    def importance_badge(self, obj):
        """Display importance with badge."""
        colors = {
            'core': '#dc3545',
            'secondary': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.importance, '#6c757d'),
            obj.get_importance_display()
        )
    
    importance_badge.short_description = _('Importance')
    importance_badge.admin_order_field = 'importance'


@admin.register(UserProject)
class UserProjectAdmin(admin.ModelAdmin):
    """Admin interface for UserProject model."""
    
    list_display = [
        'user_project_id',
        'user_link',
        'project_title',
        'status_badge',
        'progress_bar',
        'has_github',
        'has_demo',
        'started_at',
        'completed_at'
    ]
    
    list_filter = [
        'status',
        'project__difficulty_level',
        'started_at',
        'completed_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'project__title'
    ]
    
    raw_id_fields = ['user', 'project']
    
    ordering = ['-started_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'project', 'status')
        }),
        (_('Links'), {
            'fields': ('github_url', 'live_demo_url')
        }),
        (_('Dates'), {
            'fields': ('started_at', 'completed_at')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = []
    
    def user_link(self, obj):
        """Link to user admin."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    
    user_link.short_description = _('User')
    user_link.admin_order_field = 'user__username'
    
    def project_title(self, obj):
        """Display project title."""
        return obj.project.title
    
    project_title.short_description = _('Project')
    project_title.admin_order_field = 'project__title'
    
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'planned': '#6c757d',
            'in_progress': '#ffc107',
            'completed': '#28a745'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'
    
    def progress_bar(self, obj):
        """Visual progress bar."""
        percentage = obj.completion_percentage()
        color = '#6c757d' if percentage == 0 else ('#ffc107' if percentage == 50 else '#28a745')
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 4px;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; '
            'padding: 2px 0; border-radius: 4px; font-size: 11px; font-weight: bold;">{}</div>'
            '</div>',
            percentage, color, f'{percentage}%'
        )
    
    progress_bar.short_description = _('Progress')
    
    def has_github(self, obj):
        """Check if GitHub URL exists."""
        if obj.github_url:
            return format_html('✅')
        return format_html('❌')
    
    has_github.short_description = _('GitHub')
    
    def has_demo(self, obj):
        """Check if demo URL exists."""
        if obj.live_demo_url:
            return format_html('✅')
        return format_html('❌')
    
    has_demo.short_description = _('Demo')
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'project')