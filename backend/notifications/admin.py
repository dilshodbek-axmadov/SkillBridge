"""
Admin configuration for notifications models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import UserNotification, UserActivityLog, ScrapingLog


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    """Admin for user notifications"""
    list_display = [
        'id', 'user', 'notification_type',
        'title_preview', 'status_display', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification', {
            'fields': ('notification_type', 'title', 'message', 'link_url')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    def title_preview(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Title'
    
    def status_display(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color: gray;">✓ Read</span>'
            )
        return format_html(
            '<span style="color: green; font-weight: bold;">● Unread</span>'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_read'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = 0
        for notification in queryset.filter(is_read=False):
            notification.mark_as_read()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully marked {updated} notification(s) as read.'
        )
    mark_as_read.short_description = 'Mark as read'
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = 0
        for notification in queryset.filter(is_read=True):
            notification.mark_as_unread()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully marked {updated} notification(s) as unread.'
        )
    mark_as_unread.short_description = 'Mark as unread'


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Admin for user activity logs"""
    list_display = [
        'id', 'user', 'activity_type',
        'description_preview', 'timestamp', 'ip_address'
    ]
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['user__email', 'activity_description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Activity', {
            'fields': ('activity_type', 'activity_description', 'metadata')
        }),
        ('Details', {
            'fields': ('timestamp', 'ip_address')
        }),
    )
    
    def description_preview(self, obj):
        if obj.activity_description:
            return obj.activity_description[:60] + "..." if len(obj.activity_description) > 60 else obj.activity_description
        return '-'
    description_preview.short_description = 'Description'


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    """Admin for scraping logs"""
    list_display = [
        'id', 'platform_name', 'scrape_date',
        'jobs_scraped', 'jobs_added', 'jobs_updated',
        'status_display'
    ]
    list_filter = ['platform_name', 'status', 'scrape_date']
    search_fields = ['platform_name', 'error_message']
    readonly_fields = ['scrape_date']
    date_hierarchy = 'scrape_date'
    
    fieldsets = (
        ('Platform', {
            'fields': ('platform_name',)
        }),
        ('Statistics', {
            'fields': ('jobs_scraped', 'jobs_added', 'jobs_updated')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'scrape_date')
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'success': 'green',
            'failed': 'red',
            'partial': 'orange',
        }
        
        icons = {
            'success': '✓',
            'failed': '✗',
            'partial': '⚠',
        }
        
        color = colors.get(obj.status, 'black')
        icon = icons.get(obj.status, '?')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'