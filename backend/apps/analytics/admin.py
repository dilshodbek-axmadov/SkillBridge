"""
Analytics App Admin
===================
Admin configuration for analytics models.
"""

from django.contrib import admin
from django.utils.html import format_html

from apps.analytics.models import (
    DashboardSnapshot,
    SkillDemandSnapshot,
    JobCategorySnapshot,
    SalarySnapshot,
    SkillTrendHistory,
)


@admin.register(DashboardSnapshot)
class DashboardSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'snapshot_date',
        'total_active_jobs',
        'jobs_posted_last_7d',
        'jobs_posted_last_30d',
        'total_companies',
        'skills_in_demand',
        'remote_jobs_display',
        'created_at',
    ]
    list_filter = ['snapshot_date']
    ordering = ['-snapshot_date']
    readonly_fields = [
        'snapshot_id', 'snapshot_date', 'created_at',
        'experience_distribution',
    ]

    def remote_jobs_display(self, obj):
        return f"{obj.remote_jobs_percentage:.1f}%"
    remote_jobs_display.short_description = 'Remote %'


@admin.register(SkillDemandSnapshot)
class SkillDemandSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'demand_rank',
        'skill',
        'job_count',
        'demand_score_display',
        'change_display',
        'avg_salary_display',
        'period',
        'snapshot_date',
    ]
    list_filter = ['period', 'snapshot_date', 'skill__category']
    search_fields = ['skill__name_en', 'skill__name_ru']
    ordering = ['demand_rank']
    raw_id_fields = ['skill']

    def demand_score_display(self, obj):
        score = obj.demand_score
        if score >= 80:
            color = 'green'
        elif score >= 50:
            color = 'orange'
        else:
            color = 'gray'

        formatted_score = f"{score:.1f}"
        return format_html(
            '<span style="color: {};"></span>',
            color, formatted_score
        )
    demand_score_display.short_description = 'Score'

    def change_display(self, obj):
        if obj.demand_change_30d is None:
            return '-'
        change = obj.demand_change_30d
        if change > 0:
            return format_html('<span style="color: green;">+{:.1f}%</span>', change)
        elif change < 0:
            return format_html('<span style="color: red;">{:.1f}%</span>', change)
        return '0%'
    change_display.short_description = 'Change (30d)'

    def avg_salary_display(self, obj):
        if obj.avg_salary_with_skill:
            return f"{obj.avg_salary_with_skill:,.0f}"
        return '-'
    avg_salary_display.short_description = 'Avg Salary'


@admin.register(JobCategorySnapshot)
class JobCategorySnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'category_name',
        'job_count',
        'change_display',
        'avg_salary_range',
        'snapshot_date',
    ]
    list_filter = ['snapshot_date']
    search_fields = ['category_name']
    ordering = ['-job_count']

    def change_display(self, obj):
        if obj.job_count_change_7d is None:
            return '-'
        change = obj.job_count_change_7d
        if change > 0:
            return format_html('<span style="color: green;">+{:.1f}%</span>', change)
        elif change < 0:
            return format_html('<span style="color: red;">{:.1f}%</span>', change)
        return '0%'
    change_display.short_description = 'Change (7d)'

    def avg_salary_range(self, obj):
        if obj.avg_salary_min and obj.avg_salary_max:
            return f"{obj.avg_salary_min:,.0f} - {obj.avg_salary_max:,.0f}"
        return '-'
    avg_salary_range.short_description = 'Salary Range'


@admin.register(SalarySnapshot)
class SalarySnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'job_title_normalized',
        'job_count',
        'salary_range',
        'salary_avg_display',
        'experience_level',
        'currency',
        'snapshot_date',
    ]
    list_filter = ['experience_level', 'snapshot_date', 'currency']
    search_fields = ['job_title_normalized']
    ordering = ['-salary_avg']

    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min:,.0f} - {obj.salary_max:,.0f}"
        return '-'
    salary_range.short_description = 'Range'

    def salary_avg_display(self, obj):
        if obj.salary_avg:
            return f"{obj.salary_avg:,.0f}"
        return '-'
    salary_avg_display.short_description = 'Average'


@admin.register(SkillTrendHistory)
class SkillTrendHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'skill',
        'week_start',
        'job_count',
        'demand_score',
    ]
    list_filter = ['week_start', 'skill__category']
    search_fields = ['skill__name_en']
    ordering = ['-week_start', '-job_count']
    raw_id_fields = ['skill']
