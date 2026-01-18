"""
Admin configuration for learning models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    LearningRoadmap, RoadmapItem, 
    LearningResource, RoadmapResource
)


class RoadmapItemInline(admin.TabularInline):
    """Inline for roadmap items"""
    model = RoadmapItem
    extra = 1
    fields = ['sequence_order', 'skill', 'status', 'priority', 'estimated_duration_weeks']
    autocomplete_fields = ['skill']
    ordering = ['sequence_order']


@admin.register(LearningRoadmap)
class LearningRoadmapAdmin(admin.ModelAdmin):
    """Admin for learning roadmaps"""
    list_display = [
        'user', 'role', 'completion_display',
        'is_active', 'total_items', 'completed_items',
        'created_date', 'last_updated'
    ]
    list_filter = ['is_active', 'created_date', 'role']
    search_fields = ['user__email', 'role__title']
    readonly_fields = ['created_date', 'last_updated', 'completion_percentage']
    inlines = [RoadmapItemInline]
    
    fieldsets = (
        ('Roadmap Info', {
            'fields': ('user', 'role', 'is_active')
        }),
        ('Progress', {
            'fields': ('completion_percentage', 'estimated_completion_date')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'last_updated')
        }),
    )
    
    def completion_display(self, obj):
        """Display completion percentage with color and progress bar"""
        percentage = obj.completion_percentage
        
        if percentage >= 80:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        elif percentage >= 20:
            color = '#FFA500'
        else:
            color = 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 5px;">'
            '<div style="width: {}%; background-color: {}; padding: 2px 5px; border-radius: 5px; color: white; font-weight: bold; text-align: center;">'
            '{:.0f}%'
            '</div></div>',
            percentage,
            color,
            percentage
        )
    completion_display.short_description = 'Completion'
    
    def total_items(self, obj):
        return obj.roadmap_items.count()
    total_items.short_description = 'Total Skills'
    
    def completed_items(self, obj):
        return obj.roadmap_items.filter(status='completed').count()
    completed_items.short_description = 'Completed'
    
    actions = ['update_completion_percentage']
    
    def update_completion_percentage(self, request, queryset):
        """Update completion percentage for selected roadmaps"""
        updated = 0
        for roadmap in queryset:
            roadmap.update_completion_percentage()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully updated {updated} roadmap(s).'
        )
    update_completion_percentage.short_description = 'Update completion percentage'


class RoadmapResourceInline(admin.TabularInline):
    """Inline for roadmap resources"""
    model = RoadmapResource
    extra = 1
    fields = ['resource', 'is_recommended']
    autocomplete_fields = ['resource']


@admin.register(RoadmapItem)
class RoadmapItemAdmin(admin.ModelAdmin):
    """Admin for roadmap items"""
    list_display = [
        'roadmap_user', 'skill', 'sequence_order',
        'status_display', 'priority', 'estimated_duration_weeks',
        'started_date', 'completed_date'
    ]
    list_filter = ['status', 'priority', 'roadmap__role']
    search_fields = ['roadmap__user__email', 'skill__name']
    readonly_fields = ['started_date', 'completed_date']
    inlines = [RoadmapResourceInline]
    
    fieldsets = (
        ('Roadmap & Skill', {
            'fields': ('roadmap', 'skill', 'sequence_order')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'estimated_duration_weeks')
        }),
        ('Dates', {
            'fields': ('started_date', 'completed_date')
        }),
    )
    
    def roadmap_user(self, obj):
        return obj.roadmap.user.email
    roadmap_user.short_description = 'User'
    roadmap_user.admin_order_field = 'roadmap__user__email'
    
    def status_display(self, obj):
        """Display status with color"""
        colors = {
            'pending': 'gray',
            'in_progress': 'orange',
            'completed': 'green',
            'skipped': 'red',
        }
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    actions = ['mark_in_progress', 'mark_completed']
    
    def mark_in_progress(self, request, queryset):
        """Mark selected items as in progress"""
        updated = 0
        for item in queryset:
            item.mark_in_progress()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully marked {updated} item(s) as in progress.'
        )
    mark_in_progress.short_description = 'Mark as in progress'
    
    def mark_completed(self, request, queryset):
        """Mark selected items as completed"""
        updated = 0
        for item in queryset:
            item.mark_completed()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully marked {updated} item(s) as completed.'
        )
    mark_completed.short_description = 'Mark as completed'


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    """Admin for learning resources"""
    list_display = [
        'title', 'skill', 'resource_type', 'platform',
        'is_free_display', 'duration_hours', 'rating_display',
        'language'
    ]
    list_filter = ['resource_type', 'is_free', 'platform', 'language']
    search_fields = ['title', 'skill__name', 'platform', 'description']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('skill', 'title', 'resource_type', 'platform')
        }),
        ('Details', {
            'fields': ('url', 'description', 'language')
        }),
        ('Metrics', {
            'fields': ('is_free', 'duration_hours', 'rating')
        }),
    )
    
    def is_free_display(self, obj):
        if obj.is_free:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Free</span>'
            )
        return format_html(
            '<span style="color: orange;">$ Paid</span>'
        )
    is_free_display.short_description = 'Cost'
    is_free_display.admin_order_field = 'is_free'
    
    def rating_display(self, obj):
        if obj.rating:
            stars = '★' * int(obj.rating) + '☆' * (5 - int(obj.rating))
            return format_html(
                '<span style="color: #FFD700; font-size: 16px;">{}</span> <span>({:.1f})</span>',
                stars,
                obj.rating
            )
        return '-'
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'


@admin.register(RoadmapResource)
class RoadmapResourceAdmin(admin.ModelAdmin):
    """Admin for roadmap resources"""
    list_display = [
        'roadmap_user', 'skill', 'resource_title',
        'resource_type', 'is_recommended'
    ]
    list_filter = ['is_recommended', 'resource__resource_type']
    search_fields = [
        'roadmap_item__roadmap__user__email',
        'roadmap_item__skill__name',
        'resource__title'
    ]
    autocomplete_fields = ['roadmap_item', 'resource']
    
    def roadmap_user(self, obj):
        return obj.roadmap_item.roadmap.user.email
    roadmap_user.short_description = 'User'
    
    def skill(self, obj):
        return obj.roadmap_item.skill.name
    skill.short_description = 'Skill'
    
    def resource_title(self, obj):
        return obj.resource.title
    resource_title.short_description = 'Resource'
    
    def resource_type(self, obj):
        return obj.resource.get_resource_type_display()
    resource_type.short_description = 'Type'