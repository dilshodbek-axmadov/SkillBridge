"""
Learning App Admin Configuration
=================================
Django admin interface for LearningRoadmap, RoadmapItem, LearningResource, and UserLearningProgress models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import LearningRoadmap, RoadmapItem, LearningResource, UserLearningProgress


class RoadmapItemInline(admin.TabularInline):
    """
    Inline admin for RoadmapItem to show items in LearningRoadmap admin.
    """
    model = RoadmapItem
    extra = 1
    autocomplete_fields = ['skill']
    fields = ['skill', 'sequence_order', 'priority', 'status', 'estimated_duration_hours']
    ordering = ['sequence_order']


@admin.register(LearningRoadmap)
class LearningRoadmapAdmin(admin.ModelAdmin):
    """
    Admin interface for LearningRoadmap model.
    """
    
    list_display = [
        'title',
        'user_email',
        'target_role',
        'completion_display',
        'total_estimated_hours',
        'is_active',
        'generated_by_ai',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'generated_by_ai',
        'target_role',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'user__email',
        'user__username',
        'target_role',
        'description',
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'completion_percentage']
    
    fieldsets = (
        (_('User & Target'), {
            'fields': ('user', 'title', 'target_role')
        }),
        (_('Details'), {
            'fields': ('description', 'total_estimated_hours')
        }),
        (_('Status'), {
            'fields': ('is_active', 'completion_percentage', 'generated_by_ai')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-created_at']
    
    inlines = [RoadmapItemInline]
    
    autocomplete_fields = ['user']
    
    actions = ['mark_as_active', 'mark_as_inactive', 'recalculate_completion']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def completion_display(self, obj):
        """Display completion percentage with progress bar."""
        percentage = obj.completion_percentage
        color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:3px;">'
            '<div style="width:{}px; background-color:{}; height:20px; border-radius:3px; text-align:center; color:white;">{:.0f}%</div>'
            '</div>',
            percentage,
            color,
            percentage
        )
    completion_display.short_description = _('Completion')
    
    def mark_as_active(self, request, queryset):
        """Mark selected roadmaps as active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} roadmap(s) marked as active.'))
    mark_as_active.short_description = _('Mark as active')
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected roadmaps as inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} roadmap(s) marked as inactive.'))
    mark_as_inactive.short_description = _('Mark as inactive')
    
    def recalculate_completion(self, request, queryset):
        """Recalculate completion percentage for selected roadmaps."""
        for roadmap in queryset:
            roadmap.update_completion_percentage()
        self.message_user(request, _(f'Recalculated completion for {queryset.count()} roadmap(s).'))
    recalculate_completion.short_description = _('Recalculate completion')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


@admin.register(RoadmapItem)
class RoadmapItemAdmin(admin.ModelAdmin):
    """
    Admin interface for RoadmapItem model.
    """
    
    list_display = [
        'roadmap_title',
        'sequence_order',
        'skill_name',
        'priority',
        'status',
        'estimated_duration_hours',
        'started_at',
        'completed_at',
    ]
    
    list_filter = [
        'priority',
        'status',
        'roadmap__is_active',
        'created_at',
    ]
    
    search_fields = [
        'roadmap__title',
        'roadmap__user__email',
        'skill__skill_name',
    ]
    
    readonly_fields = ['created_at', 'started_at', 'completed_at']
    
    fieldsets = (
        (_('Roadmap & Skill'), {
            'fields': ('roadmap', 'skill', 'sequence_order')
        }),
        (_('Details'), {
            'fields': (
                'priority',
                'estimated_duration_hours',
                'notes',
            )
        }),
        (_('Status'), {
            'fields': ('status', 'started_at', 'completed_at')
        }),
        (_('Prerequisites'), {
            'fields': ('prerequisites',),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['roadmap', 'sequence_order']
    
    autocomplete_fields = ['roadmap', 'skill']
    
    filter_horizontal = ['prerequisites']
    
    actions = ['mark_as_completed', 'mark_as_in_progress', 'mark_as_pending']
    
    def roadmap_title(self, obj):
        """Display roadmap title."""
        return obj.roadmap.title
    roadmap_title.short_description = _('Roadmap')
    roadmap_title.admin_order_field = 'roadmap__title'
    
    def skill_name(self, obj):
        """Display skill name."""
        return obj.skill.skill_name
    skill_name.short_description = _('Skill')
    skill_name.admin_order_field = 'skill__skill_name'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected items as completed."""
        count = 0
        for item in queryset:
            item.mark_as_completed()
            count += 1
        self.message_user(
            request,
            _(f'{count} item(s) marked as completed and added to user skills.')
        )
    mark_as_completed.short_description = _('Mark as completed')
    
    def mark_as_in_progress(self, request, queryset):
        """Mark selected items as in progress."""
        updated = queryset.update(status='in_progress')
        self.message_user(request, _(f'{updated} item(s) marked as in progress.'))
    mark_as_in_progress.short_description = _('Mark as in progress')
    
    def mark_as_pending(self, request, queryset):
        """Mark selected items as pending."""
        updated = queryset.update(status='pending')
        self.message_user(request, _(f'{updated} item(s) marked as pending.'))
    mark_as_pending.short_description = _('Mark as pending')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('roadmap', 'skill', 'roadmap__user')


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    """
    Admin interface for LearningResource model.
    """
    
    list_display = [
        'title',
        'skill_name',
        'resource_type',
        'platform',
        'difficulty_level',
        'rating_display',
        'is_free',
        'is_verified',
        'language',
    ]
    
    list_filter = [
        'resource_type',
        'difficulty_level',
        'is_free',
        'is_verified',
        'language',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'skill__skill_name',
        'author',
        'platform',
        'description',
    ]
    
    readonly_fields = ['created_at', 'url_link']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('skill', 'title', 'resource_type')
        }),
        (_('Details'), {
            'fields': (
                'author',
                'platform',
                'description',
                'url',
                'url_link',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'difficulty_level',
                'estimated_duration',
                'rating',
                'is_free',
                'language',
            )
        }),
        (_('Verification'), {
            'fields': ('is_verified',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-is_verified', '-rating', 'title']
    
    autocomplete_fields = ['skill']
    
    actions = ['mark_as_verified', 'mark_as_unverified']
    
    def skill_name(self, obj):
        """Display skill name."""
        return obj.skill.skill_name
    skill_name.short_description = _('Skill')
    skill_name.admin_order_field = 'skill__skill_name'
    
    def rating_display(self, obj):
        """Display rating with stars."""
        if obj.rating:
            stars = '⭐' * int(obj.rating)
            return f"{stars} ({obj.rating:.1f})"
        return '-'
    rating_display.short_description = _('Rating')
    
    def url_link(self, obj):
        """Display clickable URL."""
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.url,
                _('Open Resource')
            )
        return '-'
    url_link.short_description = _('Resource Link')
    
    def mark_as_verified(self, request, queryset):
        """Mark selected resources as verified."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, _(f'{updated} resource(s) marked as verified.'))
    mark_as_verified.short_description = _('Mark as verified')
    
    def mark_as_unverified(self, request, queryset):
        """Mark selected resources as unverified."""
        updated = queryset.update(is_verified=False)
        self.message_user(request, _(f'{updated} resource(s) marked as unverified.'))
    mark_as_unverified.short_description = _('Mark as unverified')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('skill')


@admin.register(UserLearningProgress)
class UserLearningProgressAdmin(admin.ModelAdmin):
    """
    Admin interface for UserLearningProgress model.
    """
    
    list_display = [
        'user_email',
        'resource_title',
        'status',
        'progress_bar',
        'time_spent_hours',
        'user_rating_display',
        'updated_at',
    ]
    
    list_filter = [
        'status',
        'started_at',
        'updated_at',
    ]
    
    search_fields = [
        'user__email',
        'user__username',
        'resource__title',
        'resource__skill__skill_name',
    ]
    
    readonly_fields = ['started_at', 'completed_at', 'updated_at']
    
    fieldsets = (
        (_('User & Resource'), {
            'fields': ('user', 'resource')
        }),
        (_('Progress'), {
            'fields': (
                'status',
                'progress_percentage',
                'time_spent_hours',
            )
        }),
        (_('Feedback'), {
            'fields': ('rating', 'notes')
        }),
        (_('Timestamps'), {
            'fields': ('started_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-updated_at']
    
    autocomplete_fields = ['user', 'resource']
    
    actions = ['mark_as_completed']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def resource_title(self, obj):
        """Display resource title."""
        return obj.resource.title
    resource_title.short_description = _('Resource')
    resource_title.admin_order_field = 'resource__title'
    
    def progress_bar(self, obj):
        """Display progress bar."""
        percentage = obj.progress_percentage
        color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:3px;">'
            '<div style="width:{}px; background-color:{}; height:20px; border-radius:3px; text-align:center; color:white;">{:.0f}%</div>'
            '</div>',
            percentage,
            color,
            percentage
        )
    progress_bar.short_description = _('Progress')
    
    def user_rating_display(self, obj):
        """Display user rating."""
        if obj.rating:
            return '⭐' * obj.rating
        return '-'
    user_rating_display.short_description = _('Rating')
    
    def mark_as_completed(self, request, queryset):
        """Mark selected progress as completed."""
        count = 0
        for progress in queryset:
            progress.mark_as_completed()
            count += 1
        self.message_user(request, _(f'{count} progress item(s) marked as completed.'))
    mark_as_completed.short_description = _('Mark as completed')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'resource', 'resource__skill')