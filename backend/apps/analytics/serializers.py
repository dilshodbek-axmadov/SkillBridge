"""
Analytics App Serializers
=========================
Serializers for dashboard analytics data.
"""

from rest_framework import serializers
from apps.analytics.models import (
    DashboardSnapshot,
    SkillDemandSnapshot,
    JobCategorySnapshot,
    SalarySnapshot,
    SkillTrendHistory,
)


class DashboardSnapshotSerializer(serializers.ModelSerializer):
    """Dashboard snapshot serializer."""

    class Meta:
        model = DashboardSnapshot
        fields = [
            'snapshot_id',
            'total_active_jobs',
            'jobs_posted_last_7d',
            'jobs_posted_last_30d',
            'total_companies',
            'total_skills_tracked',
            'skills_in_demand',
            'avg_salary_min',
            'avg_salary_max',
            'median_salary',
            'remote_jobs_percentage',
            'experience_distribution',
            'snapshot_date',
            'created_at',
        ]


class SkillDemandSnapshotSerializer(serializers.ModelSerializer):
    """Skill demand snapshot serializer."""

    skill_name = serializers.CharField(source='skill.name_en', read_only=True)
    skill_name_ru = serializers.CharField(source='skill.name_ru', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = SkillDemandSnapshot
        fields = [
            'snapshot_id',
            'skill_id',
            'skill_name',
            'skill_name_ru',
            'category',
            'job_count',
            'demand_rank',
            'demand_score',
            'demand_change_7d',
            'demand_change_30d',
            'avg_salary_with_skill',
            'period',
            'snapshot_date',
        ]


class JobCategorySnapshotSerializer(serializers.ModelSerializer):
    """Job category snapshot serializer."""

    class Meta:
        model = JobCategorySnapshot
        fields = [
            'snapshot_id',
            'category_name',
            'job_count',
            'job_count_change_7d',
            'avg_salary_min',
            'avg_salary_max',
            'experience_breakdown',
            'top_skills',
            'snapshot_date',
        ]


class SalarySnapshotSerializer(serializers.ModelSerializer):
    """Salary snapshot serializer."""

    class Meta:
        model = SalarySnapshot
        fields = [
            'snapshot_id',
            'job_title_normalized',
            'job_count',
            'salary_min',
            'salary_max',
            'salary_avg',
            'salary_median',
            'salary_p25',
            'salary_p75',
            'currency',
            'experience_level',
            'snapshot_date',
        ]


class SkillTrendHistorySerializer(serializers.ModelSerializer):
    """Skill trend history serializer."""

    skill_name = serializers.CharField(source='skill.name_en', read_only=True)

    class Meta:
        model = SkillTrendHistory
        fields = [
            'history_id',
            'skill_id',
            'skill_name',
            'week_start',
            'job_count',
            'demand_score',
        ]


# Request serializers

class TrendingSkillsRequestSerializer(serializers.Serializer):
    """Query params for trending skills."""

    limit = serializers.IntegerField(default=20, min_value=5, max_value=100)
    period = serializers.ChoiceField(
        choices=['7d', '30d', '90d', 'all'],
        default='30d'
    )


class SalaryInsightsRequestSerializer(serializers.Serializer):
    """Query params for salary insights."""

    experience_level = serializers.ChoiceField(
        choices=['all', 'no_experience', 'junior', 'mid', 'senior'],
        default='all',
        required=False
    )
    limit = serializers.IntegerField(default=20, min_value=5, max_value=50)


class SkillTrendRequestSerializer(serializers.Serializer):
    """Query params for skill trend."""

    weeks = serializers.IntegerField(default=12, min_value=4, max_value=52)
