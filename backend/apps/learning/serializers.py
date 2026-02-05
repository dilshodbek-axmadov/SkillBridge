"""
Learning App Serializers
========================
Serializers for learning roadmaps, roadmap items, and resources.
"""

from rest_framework import serializers
from apps.learning.models import (
    LearningRoadmap,
    RoadmapItem,
    LearningResource,
    UserLearningProgress
)
from apps.skills.models import Skill


# Skill Serializers

class SkillMinimalSerializer(serializers.ModelSerializer):
    """Minimal skill serializer for nested use."""

    class Meta:
        model = Skill
        fields = ['skill_id', 'name_en', 'name_ru', 'name_uz', 'category']


# Roadmap Item Serializers

class RoadmapItemSerializer(serializers.ModelSerializer):
    """Roadmap item serializer with skill details."""

    skill = SkillMinimalSerializer(read_only=True)
    skill_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RoadmapItem
        fields = [
            'item_id',
            'skill',
            'skill_id',
            'sequence_order',
            'estimated_duration_hours',
            'priority',
            'status',
            'notes',
            'started_at',
            'completed_at',
            'created_at',
        ]
        read_only_fields = ['item_id', 'started_at', 'completed_at', 'created_at']


class RoadmapItemDetailSerializer(serializers.ModelSerializer):
    """Detailed roadmap item serializer."""

    skill = SkillMinimalSerializer(read_only=True)
    prerequisites = serializers.SerializerMethodField()

    class Meta:
        model = RoadmapItem
        fields = [
            'item_id',
            'skill',
            'sequence_order',
            'estimated_duration_hours',
            'priority',
            'status',
            'notes',
            'prerequisites',
            'started_at',
            'completed_at',
            'created_at',
        ]

    def get_prerequisites(self, obj):
        """Get prerequisite items."""
        prereqs = obj.prerequisites.select_related('skill')
        return [
            {
                'item_id': p.item_id,
                'skill_name': p.skill.name_en,
                'status': p.status,
            }
            for p in prereqs
        ]


# Roadmap Serializers

class LearningRoadmapSerializer(serializers.ModelSerializer):
    """Learning roadmap serializer with basic info."""

    items_count = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = LearningRoadmap
        fields = [
            'roadmap_id',
            'title',
            'target_role',
            'description',
            'total_estimated_hours',
            'completion_percentage',
            'is_active',
            'generated_by_ai',
            'items_count',
            'stats',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'roadmap_id',
            'completion_percentage',
            'generated_by_ai',
            'created_at',
            'updated_at',
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_stats(self, obj):
        items = obj.items.all()
        total = items.count()
        completed = items.filter(status='completed').count()
        in_progress = items.filter(status='in_progress').count()
        skipped = items.filter(status='skipped').count()

        return {
            'total_items': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': total - completed - in_progress - skipped,
            'skipped': skipped,
        }


class LearningRoadmapDetailSerializer(serializers.ModelSerializer):
    """Detailed learning roadmap serializer with items."""

    items = RoadmapItemSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = LearningRoadmap
        fields = [
            'roadmap_id',
            'title',
            'target_role',
            'description',
            'total_estimated_hours',
            'completion_percentage',
            'is_active',
            'generated_by_ai',
            'stats',
            'items',
            'created_at',
            'updated_at',
        ]

    def get_stats(self, obj):
        items = obj.items.all()
        total = items.count()
        completed = items.filter(status='completed').count()
        in_progress = items.filter(status='in_progress').count()
        skipped = items.filter(status='skipped').count()

        return {
            'total_items': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': total - completed - in_progress - skipped,
            'skipped': skipped,
        }


# Request Serializers

class GenerateRoadmapRequestSerializer(serializers.Serializer):
    """Request serializer for roadmap generation."""

    target_role = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Target career role. Uses user's desired_role if not provided."
    )
    language = serializers.ChoiceField(
        choices=['en', 'ru', 'uz'],
        default='en',
        help_text="Response language for AI-generated content."
    )
    max_skills = serializers.IntegerField(
        required=False,
        default=15,
        min_value=5,
        max_value=30,
        help_text="Maximum number of skills to include in roadmap."
    )


class UpdateItemStatusRequestSerializer(serializers.Serializer):
    """Request serializer for updating roadmap item status."""

    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed', 'skipped'],
        help_text="New status for the roadmap item."
    )

# Response Serializers

class GenerateRoadmapResponseSerializer(serializers.Serializer):
    """Response serializer for roadmap generation."""

    success = serializers.BooleanField()
    roadmap_id = serializers.IntegerField(required=False)
    title = serializers.CharField(required=False)
    target_role = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    total_estimated_hours = serializers.IntegerField(required=False)
    items_count = serializers.IntegerField(required=False)
    items = serializers.ListField(required=False)
    error = serializers.CharField(required=False)


class UpdateItemStatusResponseSerializer(serializers.Serializer):
    """Response serializer for item status update."""

    item_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    old_status = serializers.CharField()
    new_status = serializers.CharField()
    roadmap_id = serializers.IntegerField()
    roadmap_completion = serializers.FloatField()
    updated = serializers.BooleanField()


class RoadmapStatsSerializer(serializers.Serializer):
    """Serializer for roadmap statistics."""

    total_items = serializers.IntegerField()
    completed = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    pending = serializers.IntegerField()
    skipped = serializers.IntegerField(required=False, default=0)


# Learning Resource Serializers

class LearningResourceSerializer(serializers.ModelSerializer):
    """Learning resource serializer."""

    skill = SkillMinimalSerializer(read_only=True)

    class Meta:
        model = LearningResource
        fields = [
            'resource_id',
            'skill',
            'resource_type',
            'title',
            'url',
            'author',
            'platform',
            'description',
            'rating',
            'difficulty_level',
            'estimated_duration',
            'is_free',
            'language',
            'is_verified',
            'created_at',
        ]


class UserLearningProgressSerializer(serializers.ModelSerializer):
    """User learning progress serializer."""

    resource = LearningResourceSerializer(read_only=True)

    class Meta:
        model = UserLearningProgress
        fields = [
            'progress_id',
            'resource',
            'status',
            'progress_percentage',
            'time_spent_hours',
            'notes',
            'rating',
            'started_at',
            'completed_at',
            'updated_at',
        ]


# Resource Request Serializers

class StartResourceRequestSerializer(serializers.Serializer):
    """Request serializer for starting a resource."""
    pass  # No additional fields needed, resource_id comes from URL


class UpdateProgressRequestSerializer(serializers.Serializer):
    """Request serializer for updating resource progress."""

    progress_percentage = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        help_text="Progress percentage (0-100)."
    )
    status = serializers.ChoiceField(
        choices=['started', 'in_progress', 'completed', 'abandoned'],
        required=False,
        help_text="Learning status."
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="User notes about the resource."
    )
    rating = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        help_text="User rating (1-5)."
    )
    time_spent_hours = serializers.FloatField(
        required=False,
        min_value=0,
        help_text="Time spent on this resource in hours."
    )


class GetResourcesRequestSerializer(serializers.Serializer):
    """Query params serializer for getting skill resources."""

    language = serializers.ChoiceField(
        choices=['en', 'ru', 'uz'],
        default='en',
        required=False,
        help_text="Preferred content language."
    )
    generate_if_missing = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Generate AI recommendations if no resources exist."
    )
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        required=False,
        help_text="Maximum number of resources to return."
    )
