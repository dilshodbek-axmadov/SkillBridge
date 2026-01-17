# skills/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Skill, SkillLevel, UserSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin configuration for Skill model"""
    
    list_display = [
        'name', 'category', 'popularity_score_display', 
        'user_count', 'job_count', 'created_at'
    ]
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'popularity_score']
    ordering = ['-popularity_score', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Metrics', {
            'fields': ('popularity_score', 'created_at')
        }),
    )
    
    def popularity_score_display(self, obj):
        """Display popularity score with color coding"""
        if obj.popularity_score >= 70:
            color = 'green'
        elif obj.popularity_score >= 40:
            color = 'orange'
        else:
            color = 'red'

        score_formatted = f"{obj.popularity_score:.1f}"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;"></span>',
            color,
            score_formatted
        )

    popularity_score_display.short_description = 'Popularity'
    
    def user_count(self, obj):
        """Count how many users have this skill"""
        return obj.user_skills.filter(status='learned').count()
    user_count.short_description = 'Users'
    
    def job_count(self, obj):
        """Count how many jobs require this skill"""
        try:
            return obj.job_skills.count()
        except:
            return 0
    job_count.short_description = 'Jobs'
    
    actions = ['update_popularity_scores']
    
    def update_popularity_scores(self, request, queryset):
        """Batch update popularity scores"""
        updated = 0
        for skill in queryset:
            skill.update_popularity_score()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully updated popularity scores for {updated} skills.'
        )
    update_popularity_scores.short_description = 'Update popularity scores'


@admin.register(SkillLevel)
class SkillLevelAdmin(admin.ModelAdmin):
    """Admin configuration for SkillLevel model"""
    
    list_display = ['name', 'level_order', 'description']
    ordering = ['level_order']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'level_order', 'description')
        }),
    )


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    """Admin configuration for UserSkill model"""
    
    list_display = [
        'user_email', 'skill_name', 'level', 'status_display',
        'learning_duration', 'date_added', 'proof_link'
    ]
    list_filter = ['status', 'level', 'self_assessed', 'date_added']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'skill__name'
    ]
    readonly_fields = ['date_added', 'date_marked_learned', 'learning_duration_display']
    ordering = ['-date_added']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('user', 'skill', 'level')
        }),
        ('Status', {
            'fields': ('status', 'self_assessed')
        }),
        ('Proof', {
            'fields': ('proof_url',)
        }),
        ('Timestamps', {
            'fields': ('date_added', 'date_marked_learned', 'learning_duration_display')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def skill_name(self, obj):
        return obj.skill.name
    skill_name.short_description = 'Skill'
    skill_name.admin_order_field = 'skill__name'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'not_started': 'gray',
            'in_progress': 'orange',
            'learned': 'green',
        }
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def learning_duration(self, obj):
        """Display learning duration"""
        return obj.get_learning_duration_display()
    learning_duration.short_description = 'Duration'
    
    def learning_duration_display(self, obj):
        """For readonly field in detail view"""
        days = obj.get_learning_duration()
        return f"{days} days ({obj.get_learning_duration_display()})"
    learning_duration_display.short_description = 'Learning Duration'
    
    def proof_link(self, obj):
        """Display proof URL as clickable link"""
        if obj.proof_url:
            return format_html(
                '<a href="{}" target="_blank">View</a>',
                obj.proof_url
            )
        return '-'
    proof_link.short_description = 'Proof'
    
    actions = ['mark_as_learned', 'mark_in_progress']
    
    def mark_as_learned(self, request, queryset):
        """Batch mark skills as learned"""
        updated = 0
        for user_skill in queryset:
            user_skill.mark_as_learned()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully marked {updated} skills as learned.'
        )
    mark_as_learned.short_description = 'Mark selected as learned'
    
    def mark_in_progress(self, request, queryset):
        """Batch mark skills as in progress"""
        updated = queryset.update(status='in_progress')
        
        self.message_user(
            request,
            f'Successfully marked {updated} skills as in progress.'
        )
    mark_in_progress.short_description = 'Mark selected as in progress'