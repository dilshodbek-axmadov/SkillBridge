"""
Jobs App Admin Configuration
=============================
Django admin interface for JobPosting, JobSkill, and MarketTrend models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import JobPosting, JobSkill, MarketTrend


class JobSkillInline(admin.TabularInline):
    """
    Inline admin for JobSkill to show required skills in JobPosting admin.
    """
    model = JobSkill
    extra = 1
    autocomplete_fields = ['skill']
    fields = ['skill', 'importance', 'years_required']


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    """
    Admin interface for JobPosting model.
    """
    
    list_display = [
        'job_title',
        'company_name',
        'job_category',
        'experience_required',
        'location',
        'salary_display',
        'is_active',
        'is_remote',
        'posted_date',
        'source',
    ]
    
    list_filter = [
        'is_active',
        'is_remote',
        'job_category',
        'experience_required',
        'employment_type',
        'source',
        'posted_date',
        'scraped_at',
    ]
    
    search_fields = [
        'job_title',
        'company_name',
        'job_category',
        'location',
        'job_description',
        'external_job_id',
    ]
    
    readonly_fields = ['scraped_at', 'updated_at', 'job_url_link']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'external_job_id',
                'job_title',
                'company_name',
                'job_category',
            )
        }),
        (_('Job Details'), {
            'fields': (
                'experience_required',
                'employment_type',
                'location',
                'is_remote',
            )
        }),
        (_('Salary Information'), {
            'fields': (
                'salary_min',
                'salary_max',
                'salary_currency',
            )
        }),
        (_('Description'), {
            'fields': (
                'job_description',
                'requirements',
                'responsibilities',
                'benefits',
            )
        }),
        (_('Dates & Status'), {
            'fields': (
                'posted_date',
                'deadline_date',
                'is_active',
            )
        }),
        (_('Source'), {
            'fields': (
                'source',
                'job_url',
                'job_url_link',
            )
        }),
        (_('Timestamps'), {
            'fields': ('scraped_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-posted_date', '-scraped_at']
    
    inlines = [JobSkillInline]
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    date_hierarchy = 'posted_date'
    
    def salary_display(self, obj):
        """Display salary range."""
        return obj.salary_range
    salary_display.short_description = _('Salary')
    
    def job_url_link(self, obj):
        """Display clickable job URL."""
        if obj.job_url:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.job_url,
                _('View Job Posting')
            )
        return '-'
    job_url_link.short_description = _('Job URL')
    
    def mark_as_active(self, request, queryset):
        """Mark selected jobs as active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} job(s) marked as active.'))
    mark_as_active.short_description = _('Mark as active')
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected jobs as inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} job(s) marked as inactive.'))
    mark_as_inactive.short_description = _('Mark as inactive')


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    """
    Admin interface for JobSkill model.
    """
    
    list_display = [
        'job_title',
        'company_name',
        'skill_name',
        'importance',
        'years_required',
        'extracted_at',
    ]
    
    list_filter = [
        'importance',
        'extracted_at',
    ]
    
    search_fields = [
        'job__job_title',
        'job__company_name',
        'skill__skill_name',
    ]
    
    readonly_fields = ['extracted_at']
    
    fieldsets = (
        (_('Job & Skill'), {
            'fields': ('job', 'skill')
        }),
        (_('Requirement Details'), {
            'fields': (
                'importance',
                'years_required',
            )
        }),
        (_('Metadata'), {
            'fields': ('extracted_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-extracted_at']
    
    autocomplete_fields = ['job', 'skill']
    
    def job_title(self, obj):
        """Display job title."""
        return obj.job.job_title
    job_title.short_description = _('Job Title')
    job_title.admin_order_field = 'job__job_title'
    
    def company_name(self, obj):
        """Display company name."""
        return obj.job.company_name
    company_name.short_description = _('Company')
    company_name.admin_order_field = 'job__company_name'
    
    def skill_name(self, obj):
        """Display skill name."""
        return obj.skill.skill_name
    skill_name.short_description = _('Skill')
    skill_name.admin_order_field = 'skill__skill_name'
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('job', 'skill')


@admin.register(MarketTrend)
class MarketTrendAdmin(admin.ModelAdmin):
    """
    Admin interface for MarketTrend model.
    """
    
    list_display = [
        'job_category',
        'skill_name',
        'demand_score',
        'job_count',
        'average_salary_display',
        'growth_rate_display',
        'period_display',
        'created_at',
    ]
    
    list_filter = [
        'job_category',
        'analysis_period_start',
        'analysis_period_end',
        'created_at',
    ]
    
    search_fields = [
        'job_category',
        'skill__skill_name',
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Category & Skill'), {
            'fields': ('job_category', 'skill')
        }),
        (_('Trend Metrics'), {
            'fields': (
                'demand_score',
                'job_count',
                'growth_rate',
            )
        }),
        (_('Salary Information'), {
            'fields': (
                'average_salary',
                'salary_currency',
            )
        }),
        (_('Analysis Period'), {
            'fields': (
                'analysis_period_start',
                'analysis_period_end',
            )
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-demand_score', '-created_at']
    
    autocomplete_fields = ['skill']
    
    date_hierarchy = 'analysis_period_start'
    
    def skill_name(self, obj):
        """Display skill name."""
        return obj.skill.skill_name if obj.skill else '-'
    skill_name.short_description = _('Skill')
    skill_name.admin_order_field = 'skill__skill_name'
    
    def average_salary_display(self, obj):
        """Display average salary with currency."""
        if obj.average_salary:
            return f"{obj.average_salary:,.0f} {obj.salary_currency}"
        return '-'
    average_salary_display.short_description = _('Avg Salary')
    
    def growth_rate_display(self, obj):
        """Display growth rate with formatting."""
        if obj.growth_rate > 0:
            return format_html(
                '<span style="color: green;">▲ {:.1f}%</span>',
                obj.growth_rate
            )
        elif obj.growth_rate < 0:
            return format_html(
                '<span style="color: red;">▼ {:.1f}%</span>',
                abs(obj.growth_rate)
            )
        return '0%'
    growth_rate_display.short_description = _('Growth')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('skill')
