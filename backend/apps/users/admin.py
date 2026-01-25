"""
Users App Admin Configuration
==============================
Django admin interface customization for User and UserProfile models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    """
    
    list_display = [
        'email',
        'username',
        'first_name',
        'last_name',
        'preferred_language',
        'profile_completed',
        'is_active',
        'is_staff',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'profile_completed',
        'preferred_language',
        'created_at',
    ]
    
    search_fields = [
        'email',
        'username',
        'first_name',
        'last_name',
        'phone',
    ]
    
    ordering = ['-created_at']
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Preferences'), {
            'fields': ('preferred_language', 'profile_completed')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'preferred_language',
            ),
        }),
    )
    
    # Custom actions
    actions = ['mark_profile_completed', 'mark_profile_incomplete']
    
    def mark_profile_completed(self, request, queryset):
        """Mark selected users' profiles as completed."""
        updated = queryset.update(profile_completed=True)
        self.message_user(
            request,
            _(f'{updated} user(s) marked as profile completed.')
        )
    mark_profile_completed.short_description = _('Mark profile as completed')
    
    def mark_profile_incomplete(self, request, queryset):
        """Mark selected users' profiles as incomplete."""
        updated = queryset.update(profile_completed=False)
        self.message_user(
            request,
            _(f'{updated} user(s) marked as profile incomplete.')
        )
    mark_profile_incomplete.short_description = _('Mark profile as incomplete')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Custom admin interface for UserProfile model.
    """
    
    list_display = [
        'user_email',
        'current_job_position',
        'desired_role',
        'experience_level',
        'profile_source',
        'location',
        'is_complete',
        'created_at',
    ]
    
    list_filter = [
        'experience_level',
        'profile_source',
        'created_at',
        'updated_at',
    ]
    
    search_fields = [
        'user__email',
        'user__username',
        'current_job_position',
        'desired_role',
        'location',
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'is_complete']
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Career Information'), {
            'fields': (
                'current_job_position',
                'desired_role',
                'experience_level',
                'bio',
            )
        }),
        (_('Profile Source'), {
            'fields': ('profile_source', 'cv_file_path')
        }),
        (_('Personal Information'), {
            'fields': (
                'location',
                'profile_picture',
            )
        }),
        (_('Social Links'), {
            'fields': (
                'github_url',
                'linkedin_url',
                'portfolio_url',
            ),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('is_complete', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-created_at']
    
    # Custom display methods
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _('User Email')
    user_email.admin_order_field = 'user__email'
    
    def is_complete(self, obj):
        """Display if profile is complete."""
        return obj.is_complete
    is_complete.short_description = _('Profile Complete')
    is_complete.boolean = True
    
    # Inline display for related user
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user')