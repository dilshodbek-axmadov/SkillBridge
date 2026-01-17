# jobs/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import JobCategory, JobPosting, JobSkill, JobPostingCategory


class JobSkillInline(admin.TabularInline):
    """Inline admin for job skills"""
    model = JobSkill
    extra = 1
    fields = ['skill', 'is_required', 'importance_level']
    autocomplete_fields = ['skill']


class JobPostingCategoryInline(admin.TabularInline):
    """Inline admin for job categories"""
    model = JobPostingCategory
    extra = 1
    fields = ['category']


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for JobCategory"""
    
    list_display = ['name', 'external_id', 'active_jobs_count', 'total_jobs_count']
    search_fields = ['name', 'description', 'external_id']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'external_id', 'description')
        }),
    )
    
    def active_jobs_count(self, obj):
        """Count of active jobs in this category"""
        count = obj.get_active_jobs_count()
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            count
        )
    active_jobs_count.short_description = 'Active Jobs'
    
    def total_jobs_count(self, obj):
        """Total count of jobs in this category"""
        return obj.job_posting_categories.count()
    total_jobs_count.short_description = 'Total Jobs'


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    """Admin configuration for JobPosting"""
    
    list_display = [
        'title', 'company_name', 'location', 'work_type',
        'salary_display', 'source_platform', 'status_display',
        'age_display', 'published_at'  # CHANGED: posted_date → published_at
    ]
    list_filter = [
        'is_active', 'archived', 'source_platform', 'work_type', 
        'employment_type', 'location', 'published_at', 'premium'  # CHANGED
    ]
    search_fields = [
        'title', 'company_name', 'description_text', 'location',
        'external_id'  # ADDED
    ]
    readonly_fields = [
        'scraped_date', 'last_updated', 'age_display', 
        'salary_range_display', 'external_id', 'created_at'  # ADDED external_id, created_at
    ]
    date_hierarchy = 'published_at'  # CHANGED: posted_date → published_at
    ordering = ['-published_at', '-scraped_date']  # CHANGED: posted_date → published_at
    
    inlines = [JobSkillInline, JobPostingCategoryInline]
    
    fieldsets = (
        ('External IDs', {
            'fields': ('external_id', 'company_id', 'area_id')
        }),
        ('Basic Information', {
            'fields': ('title', 'company_name', 'company_size', 'location')
        }),
        ('Job Type', {
            'fields': ('work_type', 'employment_type', 'experience_required')
        }),
        ('Salary', {
            'fields': (
                'salary_min', 'salary_max', 'salary_currency', 'salary_gross',
                'salary_range_display'
            )
        }),
        ('Source', {
            'fields': ('source_platform', 'posting_url', 'alternate_url')
        }),
        ('Description & Skills', {
            'fields': ('description_text', 'key_skills', 'professional_roles')
        }),
        ('Flags', {
            'fields': ('premium', 'has_test', 'response_letter_required')
        }),
        ('Status & Dates', {
            'fields': (
                'is_active', 'archived', 'published_at', 'created_at',
                'scraped_date', 'last_updated', 'age_display'
            )
        }),
    )
    
    def salary_display(self, obj):
        """Display formatted salary range"""
        return obj.get_salary_range()
    salary_display.short_description = 'Salary'
    
    def salary_range_display(self, obj):
        """For readonly field in detail view"""
        return obj.get_salary_range()
    salary_range_display.short_description = 'Salary Range'
    
    def status_display(self, obj):
        """Display active status with color"""
        if obj.archived:
            return format_html(
                '<span style="color: gray;">● Archived</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: red;">● Inactive</span>'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_active'
    
    def age_display(self, obj):
        """Display job age"""
        age = obj.get_age_in_days()
        if age is None:
            return '-'
        
        if age == 0:
            color = 'green'
            text = 'Today'
        elif age <= 7:
            color = 'green'
            text = f'{age} day{"s" if age != 1 else ""} ago'
        elif age <= 30:
            color = 'orange'
            text = f'{age} days ago'
        else:
            color = 'red'
            text = f'{age} days ago'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            text
        )
    age_display.short_description = 'Age'
    
    actions = ['mark_as_inactive', 'mark_as_active', 'mark_as_archived']
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected jobs as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully marked {updated} job(s) as inactive.'
        )
    mark_as_inactive.short_description = 'Mark as inactive'
    
    def mark_as_active(self, request, queryset):
        """Mark selected jobs as active"""
        updated = queryset.update(is_active=True, archived=False)
        self.message_user(
            request,
            f'Successfully marked {updated} job(s) as active.'
        )
    mark_as_active.short_description = 'Mark as active'
    
    def mark_as_archived(self, request, queryset):
        """Mark selected jobs as archived"""
        updated = queryset.update(archived=True, is_active=False)
        self.message_user(
            request,
            f'Successfully marked {updated} job(s) as archived.'
        )
    mark_as_archived.short_description = 'Mark as archived'


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    """Admin configuration for JobSkill"""
    
    list_display = [
        'job_title', 'skill_name', 'is_required_display',
        'importance_level', 'job_status'
    ]
    list_filter = ['is_required', 'importance_level', 'job_posting__is_active']
    search_fields = [
        'job_posting__title', 'job_posting__company_name',
        'skill__name', 'job_posting__external_id'
    ]
    autocomplete_fields = ['skill', 'job_posting']
    ordering = ['-job_posting__published_at']  # CHANGED: posted_date → published_at
    
    fieldsets = (
        ('Relationship', {
            'fields': ('job_posting', 'skill')
        }),
        ('Requirement Level', {
            'fields': ('is_required', 'importance_level')
        }),
    )
    
    def job_title(self, obj):
        return obj.job_posting.title
    job_title.short_description = 'Job'
    job_title.admin_order_field = 'job_posting__title'
    
    def skill_name(self, obj):
        return obj.skill.name
    skill_name.short_description = 'Skill'
    skill_name.admin_order_field = 'skill__name'
    
    def is_required_display(self, obj):
        """Display required status with icon"""
        if obj.is_required:
            return format_html(
                '<span style="color: red; font-weight: bold;">✓ Required</span>'
            )
        return format_html(
            '<span style="color: gray;">○ Optional</span>'
        )
    is_required_display.short_description = 'Required'
    is_required_display.admin_order_field = 'is_required'
    
    def job_status(self, obj):
        """Display if the job is still active"""
        if obj.job_posting.archived:
            return format_html('<span style="color: gray;">Archived</span>')
        elif obj.job_posting.is_active:
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: red;">Inactive</span>')
    job_status.short_description = 'Job Status'


@admin.register(JobPostingCategory)
class JobPostingCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for JobPostingCategory"""
    
    list_display = ['job_title', 'category_name', 'job_status']
    list_filter = ['category', 'job_posting__is_active', 'job_posting__archived']
    search_fields = ['job_posting__title', 'category__name', 'job_posting__external_id']
    ordering = ['-job_posting__published_at']  # CHANGED: posted_date → published_at
    
    fieldsets = (
        (None, {
            'fields': ('job_posting', 'category')
        }),
    )
    
    def job_title(self, obj):
        return obj.job_posting.title
    job_title.short_description = 'Job'
    job_title.admin_order_field = 'job_posting__title'
    
    def category_name(self, obj):
        return obj.category.name
    category_name.short_description = 'Category'
    category_name.admin_order_field = 'category__name'
    
    def job_status(self, obj):
        if obj.job_posting.archived:
            return format_html('<span style="color: gray;">Archived</span>')
        elif obj.job_posting.is_active:
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: red;">Inactive</span>')
    job_status.short_description = 'Status'