"""
Skills App Serializers
======================
Serializers for skill gap analysis API endpoints.
"""

from rest_framework import serializers
from .models import Skill, SkillGap, MarketTrend, UserSkill


# ==================== SKILL SERIALIZERS ====================

class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""

    class Meta:
        model = Skill
        fields = [
            'skill_id',
            'name_en',
            'name_ru',
            'name_uz',
            'category',
            'is_verified',
        ]
        read_only_fields = ['skill_id', 'is_verified']


class SkillMinimalSerializer(serializers.ModelSerializer):
    """Minimal skill info for nested responses."""

    class Meta:
        model = Skill
        fields = ['skill_id', 'name_en', 'name_ru', 'name_uz', 'category']


# ==================== MARKET TREND SERIALIZERS ====================

class MarketTrendSerializer(serializers.ModelSerializer):
    """Serializer for MarketTrend model."""

    skill_id = serializers.IntegerField(source='skill.skill_id')
    skill_name = serializers.CharField(source='skill.name_en')
    skill_name_ru = serializers.CharField(source='skill.name_ru')
    skill_name_uz = serializers.CharField(source='skill.name_uz')
    category = serializers.CharField(source='skill.category')
    avg_salary = serializers.SerializerMethodField()

    class Meta:
        model = MarketTrend
        fields = [
            'skill_id',
            'skill_name',
            'skill_name_ru',
            'skill_name_uz',
            'category',
            'demand_score',
            'job_count',
            'growth_rate',
            'avg_salary',
            'calculated_at',
        ]

    def get_avg_salary(self, obj):
        return float(obj.avg_salary) if obj.avg_salary else None


class MarketDataSerializer(serializers.Serializer):
    """Market data for a skill."""

    demand_score = serializers.FloatField(allow_null=True)
    job_count = serializers.IntegerField(allow_null=True)
    growth_rate = serializers.FloatField(allow_null=True)
    avg_salary = serializers.FloatField(allow_null=True)


# ==================== SKILL GAP SERIALIZERS ====================

class SkillGapSerializer(serializers.ModelSerializer):
    """Serializer for SkillGap model."""

    skill_name = serializers.CharField(source='skill.name_en', read_only=True)
    skill_name_ru = serializers.CharField(source='skill.name_ru', read_only=True)
    skill_name_uz = serializers.CharField(source='skill.name_uz', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)
    priority = serializers.CharField(source='demand_priority')

    class Meta:
        model = SkillGap
        fields = [
            'gap_id',
            'skill_id',
            'skill_name',
            'skill_name_ru',
            'skill_name_uz',
            'category',
            'importance',
            'priority',
            'status',
            'identified_at',
            'updated_at',
        ]
        read_only_fields = ['gap_id', 'identified_at', 'updated_at']


class SkillGapWithMarketDataSerializer(SkillGapSerializer):
    """SkillGap with market trend data."""

    demand_score = serializers.FloatField(read_only=True, default=0)
    job_count = serializers.IntegerField(read_only=True, default=0)
    growth_rate = serializers.FloatField(read_only=True, default=0)

    class Meta(SkillGapSerializer.Meta):
        fields = SkillGapSerializer.Meta.fields + [
            'demand_score',
            'job_count',
            'growth_rate',
        ]


class SkillGapDetailSerializer(serializers.ModelSerializer):
    """Detailed SkillGap serializer with nested skill and market data."""

    skill = SkillMinimalSerializer(read_only=True)
    priority = serializers.CharField(source='demand_priority')
    market_data = serializers.SerializerMethodField()

    class Meta:
        model = SkillGap
        fields = [
            'gap_id',
            'skill',
            'importance',
            'priority',
            'status',
            'identified_at',
            'updated_at',
            'market_data',
        ]

    def get_market_data(self, obj):
        trend = MarketTrend.objects.filter(
            skill_id=obj.skill_id,
            period='30d'
        ).first()

        if not trend:
            return None

        return {
            'demand_score': trend.demand_score,
            'job_count': trend.job_count,
            'growth_rate': trend.growth_rate,
            'avg_salary': float(trend.avg_salary) if trend.avg_salary else None,
        }


# ==================== REQUEST SERIALIZERS ====================

class AnalyzeGapRequestSerializer(serializers.Serializer):
    """Request serializer for gap analysis endpoint."""

    target_role = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        help_text="Target job role for analysis"
    )
    period = serializers.ChoiceField(
        choices=['7d', '30d', '90d', '1y'],
        default='30d',
        help_text="Market trends period"
    )
    language = serializers.ChoiceField(
        choices=['en', 'ru', 'uz'],
        default='en',
        help_text="Response language"
    )


class UpdateGapStatusRequestSerializer(serializers.Serializer):
    """Request serializer for updating gap status."""

    status = serializers.ChoiceField(
        choices=['pending', 'learning', 'completed', 'skipped'],
        help_text="New status for the skill gap"
    )


# ==================== RESPONSE SERIALIZERS ====================

class MissingSkillSerializer(serializers.Serializer):
    """Serializer for missing skill in gap analysis."""

    gap_id = serializers.IntegerField()
    skill_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    category = serializers.CharField()
    importance = serializers.CharField()
    priority = serializers.CharField()
    demand_score = serializers.FloatField()
    reason = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    created = serializers.BooleanField()


class AnalyzeGapResponseSerializer(serializers.Serializer):
    """Response serializer for gap analysis endpoint."""

    success = serializers.BooleanField()
    target_role = serializers.CharField(required=False)
    user_skills = serializers.ListField(child=serializers.CharField())
    missing_skills = MissingSkillSerializer(many=True, required=False)
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    analysis_summary = serializers.CharField(required=False, allow_blank=True)
    period = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class GapStatusCountsSerializer(serializers.Serializer):
    """Counts of gaps by status."""

    pending = serializers.IntegerField()
    learning = serializers.IntegerField()
    completed = serializers.IntegerField()
    skipped = serializers.IntegerField()


class UserGapsResponseSerializer(serializers.Serializer):
    """Response serializer for user gaps list."""

    gaps = SkillGapWithMarketDataSerializer(many=True)
    total = serializers.IntegerField()
    by_status = GapStatusCountsSerializer()


class UpdateGapStatusResponseSerializer(serializers.Serializer):
    """Response serializer for gap status update."""

    gap_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    old_status = serializers.CharField()
    new_status = serializers.CharField()
    updated = serializers.BooleanField()


class MarketTrendsResponseSerializer(serializers.Serializer):
    """Response serializer for market trends list."""

    trends = MarketTrendSerializer(many=True)
    total = serializers.IntegerField()
    period = serializers.CharField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()


class SkillCategorySerializer(serializers.Serializer):
    """Serializer for skill category."""

    code = serializers.CharField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class SkillCategoriesResponseSerializer(serializers.Serializer):
    """Response serializer for categories list."""

    categories = SkillCategorySerializer(many=True)
