"""
Skills App Admin
==============================================
Admin interface for skill resolution workflow.

- Skill management with multilingual display
- Alias resolution interface
- Batch resolution actions
- Statistics and analytics
"""

from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.urls import reverse
from .models import Skill, SkillAlias, UserSkill, SkillGap, MarketTrend
from apps.jobs.models import  JobSkillExtraction


# ==================== SKILL ADMIN ====================

class SkillAliasInline(admin.TabularInline):
    """Show aliases for a skill."""
    model = SkillAlias
    extra = 0
    fields = ['alias_text', 'language_code', 'status', 'usage_count', 'source']
    readonly_fields = ['usage_count']
    can_delete = False


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """
    Admin interface for canonical skills.
    """
    
    list_display = [
        'skill_id',
        'name_en',
        'name_ru',
        'name_uz',
        'category',
        'alias_count',
        'resolved_count',
        'unresolved_count',
        'is_verified',
        'created_at',
    ]
    
    list_filter = [
        'category',
        'is_verified',
        'created_at',
    ]
    
    search_fields = [
        'name_en',
        'name_ru',
        'name_uz',
        'normalized_key',
    ]
    
    readonly_fields = [
        'skill_id',
        'normalized_key',
        'created_at',
        'updated_at',
        'alias_count',
        'resolved_count',
        'unresolved_count',
    ]
    
    fieldsets = [
        ('English Name (Required)', {
            'fields': ['name_en', 'normalized_key'],
        }),
        ('Translations', {
            'fields': ['name_ru', 'name_uz'],
        }),
        ('Classification', {
            'fields': ['category'],
        }),
        ('Quality Control', {
            'fields': ['is_verified', 'verification_notes'],
        }),
        ('Statistics', {
            'fields': ['alias_count', 'resolved_count', 'unresolved_count'],
            'classes': ['collapse'],
        }),
        ('Metadata', {
            'fields': ['skill_id', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
    
    inlines = [SkillAliasInline]
    
    actions = [
        'mark_as_verified',
        'mark_as_unverified',
    ]
    
    def alias_count(self, obj):
        """Total number of aliases."""
        count = obj.aliases.count()
        url = reverse('admin:skills_skillalias_changelist') + f'?skill__id__exact={obj.skill_id}'
        return format_html('<a href="{}">{}</a>', url, count)
    alias_count.short_description = 'Total Aliases'
    
    def resolved_count(self, obj):
        """Number of resolved aliases."""
        count = obj.aliases.filter(status='resolved').count()
        return count
    resolved_count.short_description = 'Resolved'
    
    def unresolved_count(self, obj):
        """Number of unresolved aliases."""
        count = obj.aliases.filter(status='unresolved').count()
        if count > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return count
    unresolved_count.short_description = 'Unresolved'
    
    def mark_as_verified(self, request, queryset):
        """Mark selected skills as verified."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} skill(s) marked as verified.')
    mark_as_verified.short_description = 'Mark as verified'
    
    def mark_as_unverified(self, request, queryset):
        """Mark selected skills as unverified."""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} skill(s) marked as unverified.')
    mark_as_unverified.short_description = 'Mark as unverified'


# ==================== SKILL ALIAS ADMIN ====================

@admin.register(SkillAlias)
class SkillAliasAdmin(admin.ModelAdmin):
    """
    Admin interface for skill aliases with resolution management.
    """
    
    list_display = [
        'alias_id',
        'alias_text',
        'language_code',
        'status_badge',
        'skill_link',
        'confidence',
        'usage_count',
        'source',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'language_code',
        'source',
        'created_at',
    ]
    
    search_fields = [
        'alias_text',
        'skill__name_en',
        'skill__name_ru',
    ]
    
    readonly_fields = [
        'alias_id',
        'usage_count',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = [
        ('Alias Information', {
            'fields': ['alias_text', 'language_code', 'source'],
        }),
        ('Resolution', {
            'fields': ['skill', 'status', 'confidence'],
        }),
        ('Statistics', {
            'fields': ['usage_count'],
        }),
        ('Metadata', {
            'fields': ['alias_id', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
    
    actions = [
        'mark_as_resolved',
        'mark_as_needs_review',
        'mark_as_rejected',
        'reset_to_unresolved',
    ]
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'resolved': 'green',
            'unresolved': 'orange',
            'rejected': 'red',
            'needs_review': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def skill_link(self, obj):
        """Link to canonical skill."""
        if obj.skill:
            url = reverse('admin:skills_skill_change', args=[obj.skill.skill_id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.skill.name_en
            )
        return format_html('<em style="color: gray;">Not resolved</em>')
    skill_link.short_description = 'Canonical Skill'
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected aliases as resolved (must have skill assigned)."""
        count = 0
        for alias in queryset:
            if alias.skill_id:
                alias.status = 'resolved'
                alias.save()
                count += 1
        
        self.message_user(request, f'{count} alias(es) marked as resolved.')
        
        skipped = queryset.count() - count
        if skipped > 0:
            self.message_user(
                request,
                f'{skipped} alias(es) skipped (no skill assigned).',
                level='warning'
            )
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def mark_as_needs_review(self, request, queryset):
        """Mark selected aliases as needing review."""
        updated = queryset.update(status='needs_review')
        self.message_user(request, f'{updated} alias(es) marked as needs review.')
    mark_as_needs_review.short_description = 'Mark as needs review'
    
    def mark_as_rejected(self, request, queryset):
        """Mark selected aliases as rejected."""
        updated = queryset.update(status='rejected', skill=None)
        self.message_user(request, f'{updated} alias(es) marked as rejected.')
    mark_as_rejected.short_description = 'Mark as rejected'
    
    def reset_to_unresolved(self, request, queryset):
        """Reset selected aliases to unresolved."""
        updated = queryset.update(status='unresolved', skill=None, confidence=None)
        self.message_user(request, f'{updated} alias(es) reset to unresolved.')
    reset_to_unresolved.short_description = 'Reset to unresolved'


# ==================== USER SKILL ADMIN ====================

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    """
    Admin interface for user skills.
    """
    
    list_display = [
        'user_skill_id',
        'user',
        'skill',
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
        'skill__name_en',
        'skill__name_ru',
    ]
    
    readonly_fields = [
        'user_skill_id',
        'added_at',
        'updated_at',
    ]
    
    fieldsets = [
        ('User & Skill', {
            'fields': ['user', 'skill'],
        }),
        ('Proficiency', {
            'fields': ['proficiency_level', 'years_of_experience'],
        }),
        ('Metadata', {
            'fields': ['source', 'is_primary', 'added_at', 'updated_at'],
        }),
    ]


# ==================== SKILL GAP ADMIN ====================

@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    """
    Admin interface for skill gaps.
    """
    
    list_display = [
        'gap_id',
        'user',
        'skill',
        'importance',
        'demand_priority',
        'status',
        'identified_at',
    ]
    
    list_filter = [
        'importance',
        'demand_priority',
        'status',
        'identified_at',
    ]
    
    search_fields = [
        'user__email',
        'skill__name_en',
        'skill__name_ru',
    ]
    
    readonly_fields = [
        'gap_id',
        'identified_at',
        'updated_at',
    ]
    
    fieldsets = [
        ('User & Skill', {
            'fields': ['user', 'skill'],
        }),
        ('Gap Analysis', {
            'fields': ['importance', 'demand_priority', 'status'],
        }),
        ('Metadata', {
            'fields': ['identified_at', 'updated_at'],
        }),
    ]


# ==================== JOB SKILL EXTRACTION ADMIN ====================

@admin.register(JobSkillExtraction)
class JobSkillExtractionAdmin(admin.ModelAdmin):
    """
    Admin interface for job-alias mappings.
    """
    
    list_display = [
        'extraction_id',
        'job_posting',
        'alias_text_display',
        'alias_status',
        'importance',
        'created_at',
    ]
    
    list_filter = [
        'importance',
        'created_at',
        'alias__status',
    ]
    
    search_fields = [
        'job_posting__job_title',
        'alias__alias_text',
    ]
    
    readonly_fields = [
        'extraction_id',
        'created_at',
    ]
    
    fieldsets = [
        ('Extraction', {
            'fields': ['job_posting', 'alias', 'importance'],
        }),
        ('Metadata', {
            'fields': ['extraction_id', 'created_at'],
        }),
    ]
    
    def alias_text_display(self, obj):
        """Display alias text with link."""
        url = reverse('admin:skills_skillalias_change', args=[obj.alias.alias_id])
        return format_html('<a href="{}">{}</a>', url, obj.alias.alias_text)
    alias_text_display.short_description = 'Alias Text'
    
    def alias_status(self, obj):
        """Display alias resolution status."""
        colors = {
            'resolved': 'green',
            'unresolved': 'orange',
            'rejected': 'red',
            'needs_review': 'blue',
        }
        color = colors.get(obj.alias.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.alias.get_status_display()
        )
    alias_status.short_description = 'Status'


# ==================== MARKET TREND ADMIN ====================

@admin.register(MarketTrend)
class MarketTrendAdmin(admin.ModelAdmin):
    """
    Admin interface for market trends.
    """

    list_display = [
        'trend_id',
        'skill',
        'period',
        'demand_score',
        'job_count',
        'growth_rate_display',
        'avg_salary',
        'calculated_at',
    ]

    list_filter = [
        'period',
        'calculated_at',
        'skill__category',
    ]

    search_fields = [
        'skill__name_en',
        'skill__name_ru',
    ]

    readonly_fields = [
        'trend_id',
        'calculated_at',
    ]

    fieldsets = [
        ('Skill & Period', {
            'fields': ['skill', 'period'],
        }),
        ('Metrics', {
            'fields': ['demand_score', 'job_count', 'growth_rate', 'avg_salary'],
        }),
        ('Metadata', {
            'fields': ['trend_id', 'calculated_at'],
            'classes': ['collapse'],
        }),
    ]

    def growth_rate_display(self, obj):
        """Display growth rate with color coding."""
        if obj.growth_rate is None:
            return format_html('<span style="color: gray;">N/A</span>')
        if obj.growth_rate > 0:
            return format_html(
                '<span style="color: green;">+{:.1f}%</span>',
                obj.growth_rate
            )
        elif obj.growth_rate < 0:
            return format_html(
                '<span style="color: red;">{:.1f}%</span>',
                obj.growth_rate
            )
        return f'{obj.growth_rate:.1f}%'
    growth_rate_display.short_description = 'Growth Rate'