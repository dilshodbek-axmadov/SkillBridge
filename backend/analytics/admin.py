"""
Admin configuration for analytics models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import MarketTrend, SkillCombination


@admin.register(MarketTrend)
class MarketTrendAdmin(admin.ModelAdmin):
    """Admin for market trends"""
    list_display = [
        'skill', 'period_display', 'demand_count',
        'trend_direction_display', 'average_salary_display'
    ]
    list_filter = ['trend_direction', 'year', 'month']
    search_fields = ['skill__name']
    date_hierarchy = None
    
    fieldsets = (
        ('Skill & Period', {
            'fields': ('skill', 'month', 'year')
        }),
        ('Metrics', {
            'fields': ('demand_count', 'average_salary', 'trend_direction')
        }),
    )
    
    def period_display(self, obj):
        return obj.get_period_display()
    period_display.short_description = 'Period'
    period_display.admin_order_field = 'year'
    
    def trend_direction_display(self, obj):
        """Display trend with arrow and color"""
        icons = {
            'rising': ('↗', 'green', '📈'),
            'stable': ('→', 'gray', '➡️'),
            'declining': ('↘', 'red', '📉'),
        }
        
        arrow, color, emoji = icons.get(obj.trend_direction, ('?', 'black', ''))
        
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 18px;">{}</span> '
            '<span style="color: {};">{}</span>',
            color,
            emoji,
            color,
            obj.get_trend_direction_display()
        )
    trend_direction_display.short_description = 'Trend'
    trend_direction_display.admin_order_field = 'trend_direction'
    
    def average_salary_display(self, obj):
        if obj.average_salary:
            salary_formatted = f"{obj.average_salary:,.0f}"
            return format_html(
                '<span style="color: green; font-weight: bold;"></span>',
                salary_formatted
            )
        return '-'
    average_salary_display.short_description = 'Avg Salary'
    average_salary_display.admin_order_field = 'average_salary'
    
    actions = ['calculate_trends_for_current_month']
    
    def calculate_trends_for_current_month(self, request, queryset):
        """Calculate trends for selected skills for current month"""
        from datetime import date
        from skills.models import Skill
        
        today = date.today()
        month = today.month
        year = today.year
        
        skills = Skill.objects.filter(
            id__in=queryset.values_list('skill_id', flat=True).distinct()
        )
        
        updated = 0
        for skill in skills:
            MarketTrend.calculate_for_skill(skill, month, year)
            updated += 1
        
        self.message_user(
            request,
            f'Successfully calculated trends for {updated} skill(s) for {month}/{year}.'
        )
    calculate_trends_for_current_month.short_description = 'Calculate trends for current month'


@admin.register(SkillCombination)
class SkillCombinationAdmin(admin.ModelAdmin):
    """Admin for skill combinations"""
    list_display = [
        'skill_combination_display', 'co_occurrence_count',
        'correlation_display', 'strength_display'
    ]
    list_filter = ['co_occurrence_count']
    search_fields = ['skill_1__name', 'skill_2__name']
    autocomplete_fields = ['skill_1', 'skill_2']
    
    fieldsets = (
        ('Skills', {
            'fields': ('skill_1', 'skill_2')
        }),
        ('Metrics', {
            'fields': ('co_occurrence_count', 'correlation_score')
        }),
    )
    
    def skill_combination_display(self, obj):
        """Display skill combination with visual separator"""
        return format_html(
            '<span style="font-weight: bold;">{}</span> '
            '<span style="color: gray;">+</span> '
            '<span style="font-weight: bold;">{}</span>',
            obj.skill_1.name,
            obj.skill_2.name
        )
    skill_combination_display.short_description = 'Skill Combination'
    
    def correlation_display(self, obj):
        """Display correlation as percentage with color"""
        percentage = obj.correlation_score * 100
        
        if percentage >= 50:
            color = 'green'
        elif percentage >= 25:
            color = 'orange'
        else:
            color = 'gray'
        
        percentage_formatted = f"{obj.correlation_score:,.1f}%"
        return format_html(
            '<span style="color: {}; font-weight: bold;"></span>',
            color,
            percentage_formatted
        )
    correlation_display.short_description = 'Correlation'
    correlation_display.admin_order_field = 'correlation_score'
    
    def strength_display(self, obj):
        """Display combination strength as visual bar"""
        max_count = 50  # Assume max is 50 for visualization
        percentage = min((obj.co_occurrence_count / max_count) * 100, 100)
        
        if percentage >= 70:
            color = 'green'
        elif percentage >= 40:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 5px;">'
            '<div style="width: {}%; background-color: {}; padding: 2px 5px; border-radius: 5px; color: white; font-weight: bold; text-align: center; min-width: 30px;">'
            '{}'
            '</div></div>',
            percentage,
            color,
            obj.co_occurrence_count
        )
    strength_display.short_description = 'Strength'
    
    actions = ['recalculate_combinations']
    
    def recalculate_combinations(self, request, queryset):
        """Recalculate all skill combinations"""
        count = SkillCombination.calculate_combinations()
        
        self.message_user(
            request,
            f'Successfully calculated {count} skill combinations.'
        )
    recalculate_combinations.short_description = 'Recalculate all skill combinations'