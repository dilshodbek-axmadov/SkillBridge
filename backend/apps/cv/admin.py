"""
CV App Admin
============
backend/apps/cv/admin.py

Admin interface for managing CVs and CV sections.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import CV, CVSection
from django.utils.translation import gettext_lazy as _


class CVSectionInline(admin.TabularInline):
    """Inline for CV sections."""
    model = CVSection
    extra = 0
    fields = ['section_type', 'display_order', 'is_visible']
    ordering = ['display_order']
    
    def has_add_permission(self, request, obj=None):
        """Allow adding sections."""
        return True


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    """Admin interface for CV model."""
    
    list_display = [
        'cv_id',
        'user_link',
        'title',
        'template_badge',
        'language_badge',
        'is_default_icon',
        'section_count',
        'updated_at',
        'created_at'
    ]
    
    list_filter = [
        'template_type',
        'language_code',
        'is_default',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'title'
    ]
    
    raw_id_fields = ['user']
    
    ordering = ['-updated_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'title')
        }),
        (_('Settings'), {
            'fields': ('template_type', 'language_code', 'is_default')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [CVSectionInline]
    
    def user_link(self, obj):
        """Link to user admin."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    
    user_link.short_description = _('User')
    user_link.admin_order_field = 'user__username'
    
    def template_badge(self, obj):
        """Display template type with badge."""
        colors = {
            'modern': '#007bff',
            'classic': '#6c757d',
            'creative': '#9933cc',
            'minimalist': '#28a745',
            'professional': '#17a2b8'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.template_type, '#6c757d'),
            obj.get_template_type_display()
        )
    
    template_badge.short_description = _('Template')
    template_badge.admin_order_field = 'template_type'
    
    def language_badge(self, obj):
        """Display language with flag emoji."""
        flags = {
            'en': '🇬🇧',
            'ru': '🇷🇺',
            'uz': '🇺🇿'
        }
        return format_html(
            '{} {}',
            flags.get(obj.language_code, ''),
            obj.get_language_code_display()
        )
    
    language_badge.short_description = _('Language')
    language_badge.admin_order_field = 'language_code'
    
    def is_default_icon(self, obj):
        """Display default status as icon."""
        if obj.is_default:
            return format_html('⭐')
        return format_html('—')
    
    is_default_icon.short_description = _('Default')
    is_default_icon.admin_order_field = 'is_default'
    
    def section_count(self, obj):
        """Count of CV sections."""
        count = obj.cv_sections.count()
        visible = obj.cv_sections.filter(is_visible=True).count()
        return format_html(
            '<span title="{} visible">{} / {}</span>',
            visible,
            visible,
            count
        )
    
    section_count.short_description = _('Sections')
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user').annotate(
            section_count=Count('cv_sections')
        )


@admin.register(CVSection)
class CVSectionAdmin(admin.ModelAdmin):
    """Admin interface for CVSection model."""
    
    list_display = [
        'section_id',
        'cv_title',
        'user_link',
        'section_type_badge',
        'display_order',
        'is_visible_icon',
        'content_preview'
    ]
    
    list_filter = [
        'section_type',
        'is_visible',
        'cv__template_type',
        'cv__language_code'
    ]
    
    search_fields = [
        'cv__title',
        'cv__user__username'
    ]
    
    raw_id_fields = ['cv']
    
    ordering = ['cv', 'display_order']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('cv', 'section_type')
        }),
        (_('Content'), {
            'fields': ('content',),
            'description': _('Section content in JSON format. See model docstring for examples.')
        }),
        (_('Display Settings'), {
            'fields': ('display_order', 'is_visible')
        }),
    )
    
    def cv_title(self, obj):
        """Display CV title."""
        return obj.cv.title
    
    cv_title.short_description = _('CV')
    cv_title.admin_order_field = 'cv__title'
    
    def user_link(self, obj):
        """Link to user admin."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.cv.user.id,
            obj.cv.user.username
        )
    
    user_link.short_description = _('User')
    user_link.admin_order_field = 'cv__user__username'
    
    def section_type_badge(self, obj):
        """Display section type with color."""
        colors = {
            'summary': '#007bff',
            'experience': '#28a745',
            'education': '#17a2b8',
            'skills': '#ffc107',
            'projects': '#9933cc',
            'certifications': '#fd7e14',
            'languages': '#20c997',
            'awards': '#e83e8c'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.section_type, '#6c757d'),
            obj.get_section_type_display()
        )
    
    section_type_badge.short_description = _('Section')
    section_type_badge.admin_order_field = 'section_type'
    
    def is_visible_icon(self, obj):
        """Display visibility status."""
        if obj.is_visible:
            return format_html('✅ Visible')
        return format_html('❌ Hidden')
    
    is_visible_icon.short_description = _('Visibility')
    is_visible_icon.admin_order_field = 'is_visible'
    
    def content_preview(self, obj):
        """Show preview of JSON content."""
        import json
        content_str = json.dumps(obj.content, ensure_ascii=False)
        if len(content_str) > 100:
            preview = content_str[:100] + '...'
        else:
            preview = content_str
        
        return format_html(
            '<code style="font-size: 11px;">{}</code>',
            preview
        )
    
    content_preview.short_description = _('Content Preview')
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('cv', 'cv__user')