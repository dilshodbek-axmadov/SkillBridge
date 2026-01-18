"""
Admin configuration for CVs models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserCV, CVSection, WorkExperience, Education,
    Project, ProjectSkill, UploadedCV, CVExtractionLog
)


class CVSectionInline(admin.TabularInline):
    """Inline for CV sections"""
    model = CVSection
    extra = 1
    fields = ['section_type', 'display_order']
    ordering = ['display_order']


@admin.register(UserCV)
class UserCVAdmin(admin.ModelAdmin):
    """Admin for user CVs"""
    list_display = [
        'user', 'template_type', 'is_primary_display',
        'sections_count', 'created_date', 'last_updated'
    ]
    list_filter = ['template_type', 'is_primary', 'created_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_date', 'last_updated']
    inlines = [CVSectionInline]
    
    fieldsets = (
        ('CV Info', {
            'fields': ('user', 'template_type', 'is_primary')
        }),
        ('File', {
            'fields': ('file_path',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'last_updated')
        }),
    )
    
    def is_primary_display(self, obj):
        if obj.is_primary:
            return format_html(
                '<span style="color: green; font-weight: bold;">★ Primary</span>'
            )
        return format_html(
            '<span style="color: gray;">○</span>'
        )
    is_primary_display.short_description = 'Primary'
    is_primary_display.admin_order_field = 'is_primary'
    
    def sections_count(self, obj):
        return obj.cv_sections.count()
    sections_count.short_description = 'Sections'
    
    actions = ['set_as_primary']
    
    def set_as_primary(self, request, queryset):
        """Set selected CVs as primary"""
        for cv in queryset:
            cv.set_as_primary()
        
        self.message_user(
            request,
            f'Successfully set {queryset.count()} CV(s) as primary.'
        )
    set_as_primary.short_description = 'Set as primary CV'


@admin.register(CVSection)
class CVSectionAdmin(admin.ModelAdmin):
    """Admin for CV sections"""
    list_display = ['cv_user', 'section_type', 'display_order']
    list_filter = ['section_type']
    search_fields = ['cv__user__email']
    
    def cv_user(self, obj):
        return obj.cv.user.email
    cv_user.short_description = 'User'


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    """Admin for work experience"""
    list_display = [
        'user', 'position_title', 'company_name',
        'duration_display', 'is_current', 'location'
    ]
    list_filter = ['is_current', 'start_date']
    search_fields = [
        'user__email', 'position_title', 'company_name', 'description'
    ]
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Position Info', {
            'fields': ('company_name', 'position_title', 'location')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date', 'is_current')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    def duration_display(self, obj):
        return obj.get_duration()
    duration_display.short_description = 'Duration'


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    """Admin for education"""
    list_display = [
        'user', 'degree', 'field_of_study',
        'institution_name', 'grade', 'year_range'
    ]
    list_filter = ['degree', 'start_date']
    search_fields = [
        'user__email', 'institution_name', 'field_of_study', 'degree'
    ]
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Education Info', {
            'fields': ('institution_name', 'degree', 'field_of_study', 'grade')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    def year_range(self, obj):
        start_year = obj.start_date.year
        end_year = obj.end_date.year if obj.end_date else 'Present'
        return f"{start_year} - {end_year}"
    year_range.short_description = 'Years'


class ProjectSkillInline(admin.TabularInline):
    """Inline for project skills"""
    model = ProjectSkill
    extra = 1
    autocomplete_fields = ['skill']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for projects"""
    list_display = [
        'user', 'title', 'year_range',
        'has_demo', 'has_github', 'skills_count'
    ]
    list_filter = ['start_date']
    search_fields = ['user__email', 'title', 'description']
    date_hierarchy = 'start_date'
    inlines = [ProjectSkillInline]
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Project Info', {
            'fields': ('title', 'description', 'technologies_used')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date')
        }),
        ('Links', {
            'fields': ('project_url', 'github_url')
        }),
    )
    
    def year_range(self, obj):
        start_year = obj.start_date.year
        end_year = obj.end_date.year if obj.end_date else 'Present'
        return f"{start_year} - {end_year}"
    year_range.short_description = 'Period'
    
    def has_demo(self, obj):
        if obj.project_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: green;">● Demo</a>',
                obj.project_url
            )
        return format_html('<span style="color: gray;">○</span>')
    has_demo.short_description = 'Demo'
    
    def has_github(self, obj):
        if obj.github_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: green;">● GitHub</a>',
                obj.github_url
            )
        return format_html('<span style="color: gray;">○</span>')
    has_github.short_description = 'GitHub'
    
    def skills_count(self, obj):
        return obj.project_skills.count()
    skills_count.short_description = 'Skills'


@admin.register(ProjectSkill)
class ProjectSkillAdmin(admin.ModelAdmin):
    """Admin for project skills"""
    list_display = ['project_title', 'skill_name', 'project_user']
    search_fields = ['project__title', 'skill__name', 'project__user__email']
    autocomplete_fields = ['project', 'skill']
    
    def project_title(self, obj):
        return obj.project.title
    project_title.short_description = 'Project'
    
    def skill_name(self, obj):
        return obj.skill.name
    skill_name.short_description = 'Skill'
    
    def project_user(self, obj):
        return obj.project.user.email
    project_user.short_description = 'User'


class CVExtractionLogInline(admin.TabularInline):
    """Inline for extraction logs"""
    model = CVExtractionLog
    extra = 0
    readonly_fields = ['extraction_date', 'skills_extracted_count', 'confidence_score']
    fields = ['extraction_date', 'skills_extracted_count', 'confidence_score']
    can_delete = False


@admin.register(UploadedCV)
class UploadedCVAdmin(admin.ModelAdmin):
    """Admin for uploaded CVs"""
    list_display = [
        'user', 'original_filename', 'file_type',
        'processing_status_display', 'skills_extracted',
        'upload_date'
    ]
    list_filter = ['processing_status', 'file_type', 'upload_date']
    search_fields = ['user__email', 'original_filename']
    readonly_fields = ['upload_date', 'processing_status']
    date_hierarchy = 'upload_date'
    inlines = [CVExtractionLogInline]
    
    fieldsets = (
        ('User & File', {
            'fields': ('user', 'original_filename', 'file_path', 'file_type')
        }),
        ('Processing', {
            'fields': ('processing_status', 'upload_date')
        }),
        ('Extracted Data', {
            'fields': ('extracted_data_json',)
        }),
    )
    
    def processing_status_display(self, obj):
        colors = {
            'pending': 'gray',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red',
        }
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            colors.get(obj.processing_status, 'black'),
            obj.get_processing_status_display()
        )
    processing_status_display.short_description = 'Status'
    processing_status_display.admin_order_field = 'processing_status'
    
    def skills_extracted(self, obj):
        logs = obj.extraction_logs.first()
        if logs:
            return logs.skills_extracted_count
        return 0
    skills_extracted.short_description = 'Skills Found'


@admin.register(CVExtractionLog)
class CVExtractionLogAdmin(admin.ModelAdmin):
    """Admin for extraction logs"""
    list_display = [
        'uploaded_cv_user', 'extraction_date',
        'skills_extracted_count', 'confidence_display'
    ]
    list_filter = ['extraction_date']
    search_fields = ['uploaded_cv__user__email', 'uploaded_cv__original_filename']
    readonly_fields = ['extraction_date']
    
    def uploaded_cv_user(self, obj):
        return obj.uploaded_cv.user.email
    uploaded_cv_user.short_description = 'User'
    
    def confidence_display(self, obj):
        if obj.confidence_score:
            percentage = obj.confidence_score * 100
            if percentage >= 80:
                color = 'green'
            elif percentage >= 50:
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color,
                percentage
            )
        return '-'
    confidence_display.short_description = 'Confidence'