"""
Serializers for Analytics API
"""
from rest_framework import serializers
from .models import MarketTrend, SkillCombination
from skills.models import Skill
from career.models import Role


class SkillBasicSerializer(serializers.ModelSerializer):
    """Basic skill info for nested serialization"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'category_display', 'popularity_score']


class RoleBasicSerializer(serializers.ModelSerializer):
    """Basic role info for nested serialization"""
    class Meta:
        model = Role
        fields = ['id', 'title', 'demand_score', 'growth_potential']


# ============== Market Trends Serializers ==============

class MarketTrendSerializer(serializers.ModelSerializer):
    """Serializer for market trend data"""
    skill = SkillBasicSerializer(read_only=True)
    trend_direction_display = serializers.CharField(source='get_trend_direction_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)

    class Meta:
        model = MarketTrend
        fields = [
            'id', 'skill', 'month', 'year', 'demand_count',
            'average_salary', 'trend_direction', 'trend_direction_display',
            'period_display'
        ]


class SkillTrendHistorySerializer(serializers.Serializer):
    """Serializer for skill trend history over time"""
    skill_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    skill_category = serializers.CharField()
    current_demand = serializers.IntegerField()
    current_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    trend_direction = serializers.CharField()
    growth_percentage = serializers.FloatField()
    history = MarketTrendSerializer(many=True)


class TrendComparisonSerializer(serializers.Serializer):
    """Serializer for comparing trends between skills"""
    skills = serializers.ListField(child=serializers.DictField())
    period_start = serializers.CharField()
    period_end = serializers.CharField()
    highest_growth_skill = serializers.DictField()
    highest_demand_skill = serializers.DictField()


# ============== Skill Demand Serializers ==============

class TopSkillSerializer(serializers.Serializer):
    """Serializer for top skills by demand"""
    skill_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    category = serializers.CharField()
    category_display = serializers.CharField()
    job_count = serializers.IntegerField()
    required_count = serializers.IntegerField()
    optional_count = serializers.IntegerField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    popularity_score = serializers.FloatField()
    trend_direction = serializers.CharField(allow_null=True)


class SkillDemandByCategorySerializer(serializers.Serializer):
    """Serializer for skill demand grouped by category"""
    category = serializers.CharField()
    category_display = serializers.CharField()
    total_jobs = serializers.IntegerField()
    skills_count = serializers.IntegerField()
    top_skills = TopSkillSerializer(many=True)
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)


# ============== Salary Serializers ==============

class SalaryTrendSerializer(serializers.Serializer):
    """Serializer for salary trends"""
    period = serializers.CharField()
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    job_count = serializers.IntegerField()


class SalaryBySkillSerializer(serializers.Serializer):
    """Serializer for salary data by skill"""
    skill_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    category = serializers.CharField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    median_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    job_count = serializers.IntegerField()
    salary_growth_percentage = serializers.FloatField(allow_null=True)


class SalaryByRoleSerializer(serializers.Serializer):
    """Serializer for salary data by role"""
    role_id = serializers.IntegerField()
    role_title = serializers.CharField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    job_count = serializers.IntegerField()
    demand_score = serializers.FloatField()


class SalaryByLocationSerializer(serializers.Serializer):
    """Serializer for salary data by location"""
    location = serializers.CharField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    job_count = serializers.IntegerField()


class SalaryByExperienceSerializer(serializers.Serializer):
    """Serializer for salary data by experience level"""
    experience_level = serializers.CharField()
    experience_display = serializers.CharField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    job_count = serializers.IntegerField()


# ============== Skill Combinations Serializers ==============

class SkillCombinationSerializer(serializers.ModelSerializer):
    """Serializer for skill combination data"""
    skill_1 = SkillBasicSerializer(read_only=True)
    skill_2 = SkillBasicSerializer(read_only=True)

    class Meta:
        model = SkillCombination
        fields = [
            'id', 'skill_1', 'skill_2',
            'co_occurrence_count', 'correlation_score'
        ]


class SkillStackSerializer(serializers.Serializer):
    """Serializer for common skill stacks/tech stacks"""
    stack_name = serializers.CharField()
    skills = SkillBasicSerializer(many=True)
    job_count = serializers.IntegerField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    growth_trend = serializers.CharField()


class RelatedSkillSerializer(serializers.Serializer):
    """Serializer for skills related to a specific skill"""
    skill = SkillBasicSerializer()
    co_occurrence_count = serializers.IntegerField()
    correlation_score = serializers.FloatField()
    combined_job_count = serializers.IntegerField()


# ============== Job Market Insights Serializers ==============

class JobMarketOverviewSerializer(serializers.Serializer):
    """Serializer for job market overview"""
    total_active_jobs = serializers.IntegerField()
    jobs_posted_this_month = serializers.IntegerField()
    jobs_posted_this_week = serializers.IntegerField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    remote_jobs_percentage = serializers.FloatField()
    hybrid_jobs_percentage = serializers.FloatField()
    onsite_jobs_percentage = serializers.FloatField()
    top_hiring_companies = serializers.ListField(child=serializers.DictField())
    top_locations = serializers.ListField(child=serializers.DictField())


class JobsByWorkTypeSerializer(serializers.Serializer):
    """Serializer for jobs by work type"""
    work_type = serializers.CharField()
    work_type_display = serializers.CharField()
    job_count = serializers.IntegerField()
    percentage = serializers.FloatField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)


class JobsByEmploymentTypeSerializer(serializers.Serializer):
    """Serializer for jobs by employment type"""
    employment_type = serializers.CharField()
    employment_type_display = serializers.CharField()
    job_count = serializers.IntegerField()
    percentage = serializers.FloatField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)


class CompanyInsightSerializer(serializers.Serializer):
    """Serializer for company hiring insights"""
    company_name = serializers.CharField()
    job_count = serializers.IntegerField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    top_skills = serializers.ListField(child=serializers.CharField())
    locations = serializers.ListField(child=serializers.CharField())


# ============== Dashboard Serializers ==============

class DashboardSummarySerializer(serializers.Serializer):
    """Main dashboard summary serializer"""
    # Market Overview
    total_jobs = serializers.IntegerField()
    total_skills = serializers.IntegerField()
    total_companies = serializers.IntegerField()
    average_market_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)

    # Trends
    market_growth_percentage = serializers.FloatField()
    new_jobs_this_week = serializers.IntegerField()
    trending_skills = TopSkillSerializer(many=True)

    # Top Data
    top_skills_by_demand = TopSkillSerializer(many=True)
    top_roles_by_demand = RoleBasicSerializer(many=True)
    top_paying_skills = SalaryBySkillSerializer(many=True)

    # Work Type Distribution
    work_type_distribution = JobsByWorkTypeSerializer(many=True)


class CareerComparisonSerializer(serializers.Serializer):
    """Serializer for comparing different career paths"""
    role_id = serializers.IntegerField()
    role_title = serializers.CharField()
    demand_score = serializers.FloatField()
    growth_potential = serializers.FloatField()
    average_salary_min = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    average_salary_max = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    job_count = serializers.IntegerField()
    required_skills_count = serializers.IntegerField()
    top_required_skills = SkillBasicSerializer(many=True)
    market_trend = serializers.CharField()


class SkillValueAnalysisSerializer(serializers.Serializer):
    """Serializer for analyzing the value of learning a skill"""
    skill = SkillBasicSerializer()
    current_job_count = serializers.IntegerField()
    salary_impact = serializers.DecimalField(max_digits=12, decimal_places=2)
    demand_trend = serializers.CharField()
    growth_percentage = serializers.FloatField()
    related_roles = RoleBasicSerializer(many=True)
    commonly_paired_with = SkillBasicSerializer(many=True)
    learning_priority_score = serializers.FloatField()
    recommendation = serializers.CharField()
