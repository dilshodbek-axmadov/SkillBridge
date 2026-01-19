"""
Serializers for Learning app
"""
from rest_framework import serializers
from .models import (
    LearningRoadmap, RoadmapItem,
    LearningResource, RoadmapResource
)
from skills.models import Skill, UserSkill
from career.models import Role


class SkillBasicSerializer(serializers.ModelSerializer):
    """Basic skill info for nested serialization"""
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'difficulty_level']


class RoleBasicSerializer(serializers.ModelSerializer):
    """Basic role info for nested serialization"""
    class Meta:
        model = Role
        fields = ['id', 'title', 'category']


class LearningResourceSerializer(serializers.ModelSerializer):
    """Serializer for learning resources"""
    resource_type_display = serializers.CharField(
        source='get_resource_type_display',
        read_only=True
    )
    difficulty_display = serializers.CharField(
        source='get_difficulty_display',
        read_only=True
    )
    
    class Meta:
        model = LearningResource
        fields = [
            'id', 'title', 'description', 'resource_type',
            'resource_type_display', 'url', 'difficulty',
            'difficulty_display', 'estimated_duration_hours',
            'is_free', 'price', 'language', 'rating',
            'created_date', 'last_updated'
        ]
        read_only_fields = ['id', 'created_date', 'last_updated']


class RoadmapResourceSerializer(serializers.ModelSerializer):
    """Serializer for resources linked to roadmap items"""
    resource = LearningResourceSerializer(read_only=True)
    resource_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningResource.objects.all(),
        source='resource',
        write_only=True
    )
    
    class Meta:
        model = RoadmapResource
        fields = [
            'id', 'resource', 'resource_id',
            'is_recommended', 'added_date'
        ]
        read_only_fields = ['id', 'added_date']


class RoadmapItemSerializer(serializers.ModelSerializer):
    """Serializer for roadmap items"""
    skill = SkillBasicSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source='skill',
        write_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    resources = RoadmapResourceSerializer(
        source='roadmap_resources',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = RoadmapItem
        fields = [
            'id', 'roadmap', 'sequence_order', 'skill', 'skill_id',
            'status', 'status_display', 'priority', 'priority_display',
            'estimated_duration_weeks', 'actual_duration_weeks',
            'started_date', 'completed_date', 'notes',
            'resources', 'created_date', 'last_updated'
        ]
        read_only_fields = [
            'id', 'created_date', 'last_updated',
            'started_date', 'completed_date'
        ]
    
    def validate(self, data):
        """Validate roadmap item data"""
        if data.get('status') == 'completed' and not data.get('actual_duration_weeks'):
            raise serializers.ValidationError(
                "Actual duration is required when marking as completed"
            )
        return data


class RoadmapItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating roadmap item status"""
    class Meta:
        model = RoadmapItem
        fields = ['status', 'notes', 'actual_duration_weeks']
    
    def validate_status(self, value):
        """Validate status transitions"""
        instance = self.instance
        if instance:
            current_status = instance.status
            
            # Define valid transitions
            valid_transitions = {
                'pending': ['in_progress'],
                'in_progress': ['completed', 'pending'],
                'completed': []  # Can't change from completed
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Invalid status transition from {current_status} to {value}"
                )
        
        return value


class LearningRoadmapSerializer(serializers.ModelSerializer):
    """Serializer for learning roadmaps"""
    role = RoleBasicSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True
    )
    roadmap_items = RoadmapItemSerializer(many=True, read_only=True)
    
    # Computed fields
    total_items = serializers.SerializerMethodField()
    completed_items = serializers.SerializerMethodField()
    in_progress_items = serializers.SerializerMethodField()
    pending_items = serializers.SerializerMethodField()
    next_skill = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningRoadmap
        fields = [
            'id', 'user', 'role', 'role_id', 'created_date',
            'last_updated', 'is_active', 'completion_percentage',
            'estimated_completion_date', 'roadmap_items',
            'total_items', 'completed_items', 'in_progress_items',
            'pending_items', 'next_skill'
        ]
        read_only_fields = [
            'id', 'user', 'created_date', 'last_updated',
            'completion_percentage'
        ]
    
    def get_total_items(self, obj):
        """Get total number of roadmap items"""
        return obj.roadmap_items.count()
    
    def get_completed_items(self, obj):
        """Get number of completed items"""
        return obj.roadmap_items.filter(status='completed').count()
    
    def get_in_progress_items(self, obj):
        """Get number of in-progress items"""
        return obj.roadmap_items.filter(status='in_progress').count()
    
    def get_pending_items(self, obj):
        """Get number of pending items"""
        return obj.roadmap_items.filter(status='pending').count()
    
    def get_next_skill(self, obj):
        """Get the next skill to learn"""
        next_item = obj.get_next_skill()
        if next_item:
            return SkillBasicSerializer(next_item.skill).data
        return None


class LearningRoadmapListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for roadmap list view"""
    role = RoleBasicSerializer(read_only=True)
    total_items = serializers.SerializerMethodField()
    completed_items = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningRoadmap
        fields = [
            'id', 'role', 'is_active', 'completion_percentage',
            'total_items', 'completed_items', 'created_date',
            'last_updated', 'estimated_completion_date'
        ]
    
    def get_total_items(self, obj):
        return obj.roadmap_items.count()
    
    def get_completed_items(self, obj):
        return obj.roadmap_items.filter(status='completed').count()


class RoadmapProgressSerializer(serializers.Serializer):
    """Serializer for roadmap progress statistics"""
    roadmap_id = serializers.IntegerField()
    role_title = serializers.CharField()
    completion_percentage = serializers.FloatField()
    total_skills = serializers.IntegerField()
    completed_skills = serializers.IntegerField()
    in_progress_skills = serializers.IntegerField()
    pending_skills = serializers.IntegerField()
    total_estimated_weeks = serializers.IntegerField()
    weeks_completed = serializers.IntegerField()
    estimated_completion_date = serializers.DateField()
    is_on_track = serializers.BooleanField()


class SkillResourceRecommendationSerializer(serializers.Serializer):
    """Serializer for skill learning resource recommendations"""
    skill_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    recommended_resources = LearningResourceSerializer(many=True)
    total_resources = serializers.IntegerField()
    free_resources_count = serializers.IntegerField()
    paid_resources_count = serializers.IntegerField()