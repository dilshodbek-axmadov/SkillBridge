# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, UserInterest


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""
    
    list_display = [
        'email', 'first_name', 'last_name', 'location', 
        'onboarding_method', 'profile_completion_percentage', 
        'is_active', 'registration_date'
    ]
    list_filter = [
        'is_active', 'is_staff', 'onboarding_method', 
        'registration_date', 'location'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-registration_date']
    readonly_fields = ['registration_date', 'last_login', 'profile_completion_percentage']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'location')
        }),
        ('Onboarding', {
            'fields': ('onboarding_method', 'profile_completion_percentage')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('registration_date', 'last_login')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


class UserInterestInline(admin.TabularInline):
    """Inline admin for user interests"""
    model = UserInterest
    extra = 1
    fields = ['interest_area', 'priority_level']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile"""
    
    list_display = [
        'user', 'current_role', 'experience_level', 
        'preferred_work_type', 'availability_status', 'updated_at'
    ]
    list_filter = ['experience_level', 'preferred_work_type', 'availability_status']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'current_role']
    readonly_fields = ['updated_at']
    inlines = [UserInterestInline]
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('current_role', 'experience_level', 'preferred_work_type', 'availability_status')
        }),
        ('Bio', {
            'fields': ('bio',)
        }),
        ('Links', {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Metadata', {
            'fields': ('updated_at',)
        }),
    )


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    """Admin configuration for UserInterest"""
    
    list_display = ['user', 'interest_area', 'priority_level']
    list_filter = ['interest_area', 'priority_level']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['user', 'priority_level']