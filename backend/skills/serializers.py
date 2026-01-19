"""
Serializers for Skills API
"""
from rest_framework import serializers
from skills.models import Skill, SkillLevel, UserSkill


class SkillLevelSerializer(serializers.ModelSerializer):
    """Serializer for skill levels"""
    
    class Meta:
        model = SkillLevel
        fields = ['id', 'name', 'description', 'level_order']


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for skills"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Skill
        fields = [
            'id', 'name', 'category', 'category_display',
            'description', 'popularity_score', 'created_at'
        ]
        read_only_fields = ['popularity_score', 'created_at']


class SkillDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single skill"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    users_count = serializers.SerializerMethodField()
    jobs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Skill
        fields = [
            'id', 'name', 'category', 'category_display',
            'description', 'popularity_score', 'created_at',
            'users_count', 'jobs_count'
        ]
        read_only_fields = ['popularity_score', 'created_at']
    
    def get_users_count(self, obj):
        """Count users who have this skill"""
        return obj.user_skills.filter(status='learned').count()
    
    def get_jobs_count(self, obj):
        """Count jobs requiring this skill"""
        return obj.job_skills.count()


class UserSkillSerializer(serializers.ModelSerializer):
    """Serializer for user skills"""
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.IntegerField(write_only=True)
    level = SkillLevelSerializer(read_only=True)
    level_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    learning_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSkill
        fields = [
            'id', 'skill', 'skill_id', 'level', 'level_id',
            'status', 'status_display', 'self_assessed',
            'date_added', 'date_marked_learned', 'proof_url',
            'learning_duration'
        ]
        read_only_fields = ['date_added', 'date_marked_learned']
    
    def get_learning_duration(self, obj):
        """Get human-readable learning duration"""
        return obj.get_learning_duration_display()


class AddUserSkillSerializer(serializers.Serializer):
    """Serializer for adding a skill to user"""
    skill_id = serializers.IntegerField(required=True)
    level_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['not_started', 'in_progress', 'learned'],
        default='not_started'
    )
    proof_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_skill_id(self, value):
        """Validate that skill exists"""
        if not Skill.objects.filter(id=value).exists():
            raise serializers.ValidationError("Skill not found")
        return value
    
    def validate_level_id(self, value):
        """Validate that level exists"""
        if value and not SkillLevel.objects.filter(id=value).exists():
            raise serializers.ValidationError("Skill level not found")
        return value


class UpdateUserSkillSerializer(serializers.Serializer):
    """Serializer for updating user skill"""
    level_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['not_started', 'in_progress', 'learned'],
        required=False
    )
    proof_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    
    def validate_level_id(self, value):
        """Validate that level exists"""
        if value and not SkillLevel.objects.filter(id=value).exists():
            raise serializers.ValidationError("Skill level not found")
        return value


class MarkSkillLearnedSerializer(serializers.Serializer):
    """Serializer for marking skill as learned"""
    level_id = serializers.IntegerField(required=False, allow_null=True)
    proof_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)


class SkillSearchSerializer(serializers.Serializer):
    """Serializer for skill search parameters"""
    query = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=[choice[0] for choice in Skill.CATEGORY_CHOICES],
        required=False
    )
    min_popularity = serializers.FloatField(required=False, min_value=0, max_value=100)
    ordering = serializers.ChoiceField(
        choices=['name', '-name', 'popularity_score', '-popularity_score', 'created_at', '-created_at'],
        required=False,
        default='-popularity_score'
    )


class SkillStatisticsSerializer(serializers.Serializer):
    """Serializer for skill statistics"""
    total_skills = serializers.IntegerField()
    skills_by_category = serializers.DictField()
    top_skills = serializers.ListField()
    user_skill_count = serializers.IntegerField()
    user_learned_count = serializers.IntegerField()
    user_in_progress_count = serializers.IntegerField()