"""
Skills App Admin Configuration
===============================
Django admin interface for Skill, SkillMapping, UserSkill, and SkillGap models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import Skill, SkillMapping, UserSkill, SkillGap


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """
    Admin interface for Skill model.
    """
    
    list_display = [
        'skill_name',
        'category',
        'is_verified',
        'mapping_count',
        'user_count',
        'created_at',
    ]
    
    list_filter = [
        'category',
        'is_verified',
        'created_at',
    ]
    
    search_fields = [
        'skill_name',
        'description',
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('skill_name', 'category', 'description')
        }),
        (_('Translations'), {
            'fields': ('translations',),
            'description': _('JSON format: {"ru": "Русский", "uz": "O\'zbek"}')
        }),
        (_('Verification'), {
            'fields': ('is_verified',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['skill_name']
    
    actions = ['mark_as_verified', 'mark_as_unverified']
    
    def mapping_count(self, obj):
        """Count of skill mappings."""
        return obj.mappings.count()
    mapping_count.short_description = _('Mappings')
    
    def user_count(self, obj):
        """Count of users with this skill."""
        return obj.user_skills.count()
    user_count.short_description = _('Users')
    
    def mark_as_verified(self, request, queryset):
        """Mark selected skills as verified."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, _(f'{updated} skill(s) marked as verified.'))
    mark_as_verified.short_description = _('Mark as verified')
    
    def mark_as_unverified(self, request, queryset):
        """Mark selected skills as unverified."""
        updated = queryset.update(is_verified=False)
        self.message_user(request, _(f'{updated} skill(s) marked as unverified.'))
    mark_as_unverified.short_description = _('Mark as unverified')


@admin.register(SkillMapping)
class SkillMappingAdmin(admin.ModelAdmin):
    """
    Admin interface for SkillMapping model.
    """
    
    list_display = [
        'original_text',
        'normalized_skill',
        'language',
        'source',
        'confidence_score',
        'created_at',
    ]
    
    list_filter = [
        'language',
        'source',
        'created_at',
    ]
    
    search_fields = [
        'original_text',
        'normalized_skill__skill_name',
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Mapping Information'), {
            'fields': ('original_text', 'normalized_skill')
        }),
        (_('Source Details'), {
            'fields': ('language', 'source', 'confidence_score')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-created_at']
    
    autocomplete_fields = ['normalized_skill']
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('normalized_skill')


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSkill model.
    """
    
    list_display = [
        'user_email',
        'skill_name',
        'proficiency_level',
        'years_of_experience',
        'source',
        'is_primary',
        'added_at',
    ]
    
    list_filter = [
        'proficiency_level',
        'source',
        'is_primary',
        'added_at',
    ]
    
    search_fields = [
        'user__email',
        'user__username',
        'skill__skill_name',
    ]
    
    readonly_fields = ['added_at', 'updated_at']
    
    fieldsets = (
        (_('User & Skill'), {
            'fields': ('user', 'skill')
        }),
        (_('Proficiency'), {
            'fields': (
                'proficiency_level',
                'years_of_experience',
                'is_primary',
            )
        }),
        (_('Source'), {
            'fields': ('source',)
        }),
        (_('Timestamps'), {
            'fields': ('added_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-added_at']
    
    autocomplete_fields = ['user', 'skill']
    
    actions = ['mark_as_primary', 'mark_as_secondary']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def skill_name(self, obj):
        """Display skill name."""
        return obj.skill.skill_name
    skill_name.short_description = _('Skill')
    skill_name.admin_order_field = 'skill__skill_name'
    
    def mark_as_primary(self, request, queryset):
        """Mark selected skills as primary."""
        updated = queryset.update(is_primary=True)
        self.message_user(request, _(f'{updated} skill(s) marked as primary.'))
    mark_as_primary.short_description = _('Mark as primary skill')
    
    def mark_as_secondary(self, request, queryset):
        """Mark selected skills as secondary."""
        updated = queryset.update(is_primary=False)
        self.message_user(request, _(f'{updated} skill(s) marked as secondary.'))
    mark_as_secondary.short_description = _('Mark as secondary skill')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'skill')


@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    """
    Admin interface for SkillGap model.
    """
    
    list_display = [
        'user_email',
        'skill_name',
        'importance',
        'demand_priority',
        'status',
        'target_proficiency',
        'estimated_learning_hours',
        'identified_at',
    ]
    
    list_filter = [
        'importance',
        'demand_priority',
        'status',
        'target_proficiency',
        'identified_at',
    ]
    
    search_fields = [
        'user__email',
        'user__username',
        'skill__skill_name',
    ]
    
    readonly_fields = ['identified_at', 'updated_at']
    
    fieldsets = (
        (_('User & Skill'), {
            'fields': ('user', 'skill')
        }),
        (_('Gap Details'), {
            'fields': (
                'importance',
                'demand_priority',
                'status',
                'target_proficiency',
                'estimated_learning_hours',
            )
        }),
        (_('Timestamps'), {
            'fields': ('identified_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-importance', '-demand_priority', '-identified_at']
    
    autocomplete_fields = ['user', 'skill']
    
    actions = ['mark_as_completed', 'mark_as_learning', 'mark_as_pending']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def skill_name(self, obj):
        """Display skill name."""
        return obj.skill.skill_name
    skill_name.short_description = _('Skill')
    skill_name.admin_order_field = 'skill__skill_name'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected gaps as completed and add to user skills."""
        count = 0
        for gap in queryset:
            gap.mark_as_completed()
            count += 1
        self.message_user(
            request,
            _(f'{count} skill gap(s) marked as completed and added to user skills.')
        )
    mark_as_completed.short_description = _('Mark as completed')
    
    def mark_as_learning(self, request, queryset):
        """Mark selected gaps as currently learning."""
        updated = queryset.update(status='learning')
        self.message_user(request, _(f'{updated} skill gap(s) marked as learning.'))
    mark_as_learning.short_description = _('Mark as learning')
    
    def mark_as_pending(self, request, queryset):
        """Mark selected gaps as pending."""
        updated = queryset.update(status='pending')
        self.message_user(request, _(f'{updated} skill gap(s) marked as pending.'))
    mark_as_pending.short_description = _('Mark as pending')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'skill')