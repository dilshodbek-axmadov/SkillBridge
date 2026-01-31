"""
Interests App Admin
===================
backend/apps/interests/admin.py

Admin interface for managing interests and user interests.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Interest, UserInterest
from django.utils.translation import gettext_lazy as _


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    """Admin interface for Interest model."""
    
    list_display = [
        'interest_id',
        'name_en',
        'name_ru',
        'name_uz',
        'category',
        'user_count',
        'created_at'
    ]
    
    list_filter = [
        'category',
        'created_at'
    ]
    
    search_fields = [
        'name_en',
        'name_ru',
        'name_uz'
    ]
    
    ordering = ['category', 'name_en']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('category',)
        }),
        (_('Multilingual Names'), {
            'fields': ('name_en', 'name_ru', 'name_uz'),
            'description': _('Interest names in different languages. AI auto-translates based on input.')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def user_count(self, obj):
        """Count of users who have this interest."""
        count = obj.user_interests.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return count
    
    user_count.short_description = _('Users')
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch."""
        return super().get_queryset(request).prefetch_related('user_interests')


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    """Admin interface for UserInterest model."""
    
    list_display = [
        'user_interest_id',
        'user_link',
        'interest_name',
        'interest_category',
        'added_at'
    ]
    
    list_filter = [
        'interest__category',
        'added_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'interest__name_en',
        'interest__name_ru',
        'interest__name_uz'
    ]
    
    raw_id_fields = ['user', 'interest']
    
    ordering = ['-added_at']
    
    readonly_fields = ['added_at']
    
    def user_link(self, obj):
        """Link to user admin."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    
    user_link.short_description = _('User')
    user_link.admin_order_field = 'user__username'
    
    def interest_name(self, obj):
        """Display interest name."""
        return obj.interest.name_en
    
    interest_name.short_description = _('Interest')
    interest_name.admin_order_field = 'interest__name_en'
    
    def interest_category(self, obj):
        """Display interest category with color."""
        category = obj.interest.category
        colors = {
            'tech': '#0066cc',
            'design': '#ff6600',
            'management': '#009933',
            'business': '#cc0066',
            'creative': '#9933cc'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(category, '#000000'),
            obj.interest.get_category_display()
        )
    
    interest_category.short_description = _('Category')
    interest_category.admin_order_field = 'interest__category'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'interest')