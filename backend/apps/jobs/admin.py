"""
Jobs App - Admin Interface
===========================
apps/jobs/admin.py

Admin interfaces for:
- JobPosting
- JobPostingTranslation
- JobSkill
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from .models import JobPosting, JobPostingTranslation, JobSkill


# ==================== INLINES ====================

class JobSkillInline(admin.TabularInline):
    """Inline editor for job skills."""
    model = JobSkill
    extra = 1
    autocomplete_fields = ['skill']
    fields = ['skill', 'importance']
    verbose_name = _('Required Skill')
    verbose_name_plural = _('Required Skills')


class JobPostingTranslationInline(admin.StackedInline):
    """Inline editor for job translations."""
    model = JobPostingTranslation
    extra = 0
    fields = [
        'language_code',
        'job_title',
        'job_category',
        'job_description',
        'translated_by',
        'translation_quality',
    ]
    classes = ['collapse']
    verbose_name = _('Translation')
    verbose_name_plural = _('Translations')


# ==================== JOB POSTING ADMIN ====================

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    """Admin interface for job postings."""
    
    list_display = [
        'job_title',
        'company_name',
        'original_language',
        'experience_required',
        'salary_display',
        'location',
        'skill_count',
        'translation_status',
        'is_active',
        'posted_date',
    ]
    
    list_filter = [
        'is_active',
        'original_language',
        'experience_required',
        'employment_type',
        'is_remote',
        'posted_date',
        'source',
    ]
    
    search_fields = [
        'job_title',
        'company_name',
        'job_description',
        'external_job_id',
        'location',
    ]
    
    readonly_fields = [
        'job_id',
        'external_job_id',
        'source',
        'job_url_link',
        'scraped_at',
        'updated_at',
    ]
    
    date_hierarchy = 'posted_date'
    
    inlines = [JobSkillInline, JobPostingTranslationInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'job_id',
                'external_job_id',
                'source',
                'original_language',
            )
        }),
        (_('Job Details'), {
            'fields': (
                'job_title',
                'company_name',
                'job_category',
                'experience_required',
                'employment_type',
            )
        }),
        (_('Description & Content'), {
            'fields': (
                'job_description',
            ),
            'classes': ('collapse',)
        }),
        (_('Salary'), {
            'fields': (
                'salary_min',
                'salary_max',
                'salary_currency',
            )
        }),
        (_('Location'), {
            'fields': (
                'location',
                'is_remote',
            )
        }),
        (_('Dates'), {
            'fields': (
                'posted_date',
                'deadline_date',
            )
        }),
        (_('External Link'), {
            'fields': ('job_url_link',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Metadata'), {
            'fields': ('scraped_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_active',
        'mark_inactive',
        'extract_sections',
        'create_english_translation',
    ]
    
    def salary_display(self, obj):
        """Display formatted salary range."""
        if not obj.salary_min and not obj.salary_max:
            return format_html('<span style="color: gray;">—</span>')
        
        if obj.salary_min and obj.salary_max:
            return format_html(
                '<span style="color: #28a745;">{} – {} {}</span>',
                f'{obj.salary_min:,.0f}',
                f'{obj.salary_max:,.0f}',
                obj.salary_currency
            )
        elif obj.salary_min:
            return format_html(
                '<span style="color: #28a745;">From {} {}</span>',
                f'{obj.salary_min:,.0f}',
                obj.salary_currency
            )
        else:
            return format_html(
                '<span style="color: #28a745;">Up to {} {}</span>',
                f'{obj.salary_max:,.0f}',
                obj.salary_currency
            )
    salary_display.short_description = _('Salary')
    
    def skill_count(self, obj):
        """Count of required skills."""
        count = obj.job_skills.count()
        if count == 0:
            return format_html('<span style="color: red;">0 skills</span>')
        
        core_count = obj.job_skills.filter(importance='core').count()
        secondary_count = obj.job_skills.filter(importance='secondary').count()
        
        return format_html(
            '<b>{}</b> skills <span style="color: #666;">({} core, {} nice-to-have)</span>',
            count, core_count, secondary_count
        )
    skill_count.short_description = _('Skills')
    
    def translation_status(self, obj):
        """Show translation availability."""
        translations = obj.translations.all()
        if not translations:
            return format_html('<span style="color: gray;">No translations</span>')
        
        langs = []
        for t in translations:
            color = '#28a745' if t.translation_quality == 'verified' else '#ffc107'
            langs.append(f'<span style="color: {color};">{t.language_code.upper()}</span>')
        
        return format_html(' '.join(langs))
    translation_status.short_description = _('Translations')
    
    def job_url_link(self, obj):
        """Clickable job URL."""
        if obj.job_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: #007bff;">🔗 View Original Job</a>',
                obj.job_url
            )
        return '—'
    job_url_link.short_description = _('Job URL')
    
    def mark_active(self, request, queryset):
        """Mark jobs as active."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f'{updated} jobs marked as active'),
            level='success'
        )
    mark_active.short_description = _("✅ Mark selected as active")
    
    def mark_inactive(self, request, queryset):
        """Mark jobs as inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _(f'{updated} jobs marked as inactive'),
            level='warning'
        )
    mark_inactive.short_description = _("❌ Mark selected as inactive")
    
    def extract_sections(self, request, queryset):
        """Extract requirements/responsibilities using AI."""
        count = queryset.filter(requirements='').count()
        self.message_user(
            request,
            _(f'{count} jobs need section extraction. Feature coming soon!'),
            level='info'
        )
    extract_sections.short_description = _("🤖 Extract sections (AI)")
    
    def create_english_translation(self, request, queryset):
        """Create English translations."""
        russian_jobs = queryset.filter(original_language='ru').exclude(
            translations__language_code='en'
        ).count()
        
        uzbek_jobs = queryset.filter(original_language='uz').exclude(
            translations__language_code='en'
        ).count()
        
        self.message_user(
            request,
            _(f'{russian_jobs + uzbek_jobs} jobs need English translation. Feature coming soon!'),
            level='info'
        )
    create_english_translation.short_description = _("🌐 Create English translations")
    
    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs.select_related().prefetch_related(
            'translations',
            'job_skills',
            'job_skills__skill'
        )


# ==================== JOB TRANSLATION ADMIN ====================

@admin.register(JobPostingTranslation)
class JobPostingTranslationAdmin(admin.ModelAdmin):
    """Admin interface for job translations."""
    
    list_display = [
        'job_posting',
        'language_code',
        'translated_by',
        'translation_quality',
        'created_at',
    ]
    
    list_filter = [
        'language_code',
        'translated_by',
        'translation_quality',
        'created_at',
    ]
    
    search_fields = [
        'job_posting__job_title',
        'job_title',
        'job_posting__external_job_id',
        'job_posting__company_name',
    ]
    
    readonly_fields = [
        'translation_id',
        'created_at',
        'updated_at',
    ]
    
    autocomplete_fields = ['job_posting']
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Translation Info'), {
            'fields': (
                'translation_id',
                'job_posting',
                'language_code',
            )
        }),
        (_('Translated Content'), {
            'fields': (
                'job_title',
                'job_category',
                'job_description',
            )
        }),
        (_('Quality & Source'), {
            'fields': (
                'translated_by',
                'translation_quality',
            )
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_reviewed', 'mark_verified']
    
    def mark_reviewed(self, request, queryset):
        """Mark translations as reviewed."""
        updated = queryset.update(translation_quality='reviewed')
        self.message_user(
            request,
            _(f'{updated} translations marked as reviewed'),
            level='success'
        )
    mark_reviewed.short_description = _("✓ Mark as reviewed")
    
    def mark_verified(self, request, queryset):
        """Mark translations as verified."""
        updated = queryset.update(translation_quality='verified')
        self.message_user(
            request,
            _(f'{updated} translations marked as verified'),
            level='success'
        )
    mark_verified.short_description = _("✓✓ Mark as verified")
    
    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs.select_related('job_posting')


# ==================== JOB SKILL ADMIN ====================

@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    """Admin interface for job skills."""
    
    list_display = [
        'job_posting',
        'skill_link',
        'importance',
        'created_at',
    ]
    
    list_filter = [
        'importance',
        'skill__category',
        'created_at',
    ]
    
    search_fields = [
        'job_posting__job_title',
        'job_posting__company_name',
        'skill__canonical_key',
        'skill__aliases__alias_text',
    ]
    
    readonly_fields = [
        'job_skill_id',
        'created_at',
    ]
    
    autocomplete_fields = ['job_posting', 'skill']
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Job & Skill'), {
            'fields': (
                'job_skill_id',
                'job_posting',
                'skill',
            )
        }),
        (_('Importance'), {
            'fields': ('importance',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_core', 'mark_secondary']
    
    def skill_link(self, obj):
        """Link to skill with category."""
        url = f'/admin/skills/skill/{obj.skill.skill_id}/change/'
        return format_html(
            '<a href="{}">{}</a> <span style="color: #666;">({})</span>',
            url, obj.skill.canonical_key, obj.skill.get_category_display()
        )
    skill_link.short_description = _('Skill')
    
    def mark_core(self, request, queryset):
        """Mark skills as core/required."""
        updated = queryset.update(importance='core')
        self.message_user(
            request,
            _(f'{updated} skills marked as core'),
            level='success'
        )
    mark_core.short_description = _("⭐ Mark as core/required")
    
    def mark_secondary(self, request, queryset):
        """Mark skills as secondary/nice-to-have."""
        updated = queryset.update(importance='secondary')
        self.message_user(
            request,
            _(f'{updated} skills marked as secondary'),
            level='info'
        )
    mark_secondary.short_description = _("○ Mark as secondary")
    
    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs.select_related('job_posting', 'skill')