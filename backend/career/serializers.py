"""
Serializers for Career API
"""
from rest_framework import serializers
from career.models import (
    Role, RoleRequiredSkill, UserRecommendedRole,
    SkillGapAnalysis, MissingSkill
)
from skills.serializers import SkillSerializer, SkillLevelSerializer
from jobs.serializers import JobCategorySerializer


class RoleRequiredSkillSerializer(serializers.ModelSerializer):
    """Serializer for role required skills"""
    skill = SkillSerializer(read_only=True)
    minimum_level = SkillLevelSerializer(read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    
    class Meta:
        model = RoleRequiredSkill
        fields = ['id', 'skill', 'importance', 'importance_display', 'minimum_level']


class RoleListSerializer(serializers.ModelSerializer):
    """Serializer for role listing (compact)"""
    category = JobCategorySerializer(read_only=True)
    required_skills_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'title', 'category', 'demand_score', 'growth_potential',
            'average_salary_min', 'average_salary_max', 'required_skills_count'
        ]
    
    def get_required_skills_count(self, obj):
        return obj.role_required_skills.count()


class RoleDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed role view"""
    category = JobCategorySerializer(read_only=True)
    required_skills = RoleRequiredSkillSerializer(source='role_required_skills', many=True, read_only=True)
    critical_skills = serializers.SerializerMethodField()
    important_skills = serializers.SerializerMethodField()
    nice_to_have_skills = serializers.SerializerMethodField()
    total_required_skills = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'title', 'category', 'description',
            'average_salary_min', 'average_salary_max',
            'demand_score', 'growth_potential',
            'required_skills', 'critical_skills', 'important_skills',
            'nice_to_have_skills', 'total_required_skills'
        ]
    
    def get_critical_skills(self, obj):
        critical = obj.role_required_skills.filter(importance='critical')
        return RoleRequiredSkillSerializer(critical, many=True).data
    
    def get_important_skills(self, obj):
        important = obj.role_required_skills.filter(importance='important')
        return RoleRequiredSkillSerializer(important, many=True).data
    
    def get_nice_to_have_skills(self, obj):
        nice_to_have = obj.role_required_skills.filter(importance='nice_to_have')
        return RoleRequiredSkillSerializer(nice_to_have, many=True).data
    
    def get_total_required_skills(self, obj):
        return obj.role_required_skills.count()


class UserRecommendedRoleSerializer(serializers.ModelSerializer):
    """Serializer for user recommended roles"""
    role = RoleListSerializer(read_only=True)
    
    class Meta:
        model = UserRecommendedRole
        fields = [
            'id', 'role', 'match_percentage', 'readiness_score',
            'missing_skills_count', 'recommendation_date', 'is_active'
        ]


class MissingSkillSerializer(serializers.ModelSerializer):
    """Serializer for missing skills in gap analysis"""
    skill = SkillSerializer(read_only=True)
    required_level = SkillLevelSerializer(read_only=True)
    current_level = SkillLevelSerializer(read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = MissingSkill
        fields = [
            'id', 'skill', 'required_level', 'current_level',
            'priority', 'priority_display', 'estimated_learning_weeks'
        ]


class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for skill gap analysis"""
    role = RoleListSerializer(read_only=True)
    readiness_level_display = serializers.CharField(source='get_readiness_level_display', read_only=True)
    missing_skills = MissingSkillSerializer(many=True, read_only=True)
    high_priority_skills = serializers.SerializerMethodField()
    medium_priority_skills = serializers.SerializerMethodField()
    low_priority_skills = serializers.SerializerMethodField()
    
    class Meta:
        model = SkillGapAnalysis
        fields = [
            'id', 'role', 'analysis_date', 'overall_match_percentage',
            'readiness_level', 'readiness_level_display',
            'estimated_learning_time_weeks', 'missing_skills',
            'high_priority_skills', 'medium_priority_skills', 'low_priority_skills'
        ]
    
    def get_high_priority_skills(self, obj):
        high = obj.missing_skills.filter(priority='high')
        return MissingSkillSerializer(high, many=True).data
    
    def get_medium_priority_skills(self, obj):
        medium = obj.missing_skills.filter(priority='medium')
        return MissingSkillSerializer(medium, many=True).data
    
    def get_low_priority_skills(self, obj):
        low = obj.missing_skills.filter(priority='low')
        return MissingSkillSerializer(low, many=True).data


class PerformGapAnalysisSerializer(serializers.Serializer):
    """Serializer for performing gap analysis"""
    role_id = serializers.IntegerField(required=True)
    
    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Role not found")
        return value


class SelectTargetRoleSerializer(serializers.Serializer):
    """Serializer for selecting target role"""
    role_id = serializers.IntegerField(required=True)
    
    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Role not found")
        return value


class RoleRecommendationSerializer(serializers.Serializer):
    """Serializer for role recommendations"""
    role = RoleListSerializer()
    match_percentage = serializers.FloatField()
    score = serializers.FloatField()
    missing_skills_count = serializers.IntegerField()