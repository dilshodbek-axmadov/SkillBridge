"""
Projects App Serializers
========================
Serializers for project ideas and user projects.
"""

from rest_framework import serializers
from apps.projects.models import ProjectIdea, ProjectSkill, UserProject
from apps.skills.models import Skill

# Skill Serializers

class SkillMinimalSerializer(serializers.ModelSerializer):
    """Minimal skill serializer for nested use."""

    class Meta:
        model = Skill
        fields = ['skill_id', 'name_en', 'name_ru', 'name_uz', 'category']


# Project Skill Serializers

class ProjectSkillSerializer(serializers.ModelSerializer):
    """Project skill with skill details."""

    skill = SkillMinimalSerializer(read_only=True)

    class Meta:
        model = ProjectSkill
        fields = ['project_skill_id', 'skill', 'importance']


# Project Idea Serializers

class ProjectIdeaSerializer(serializers.ModelSerializer):
    """Project idea serializer with skills."""

    core_skills = serializers.SerializerMethodField()
    secondary_skills = serializers.SerializerMethodField()

    class Meta:
        model = ProjectIdea
        fields = [
            'project_id',
            'title',
            'description',
            'target_role',
            'difficulty_level',
            'estimated_hours',
            'core_skills',
            'secondary_skills',
            'created_at',
        ]

    def get_core_skills(self, obj):
        return [ps.skill.name_en for ps in obj.project_skills.filter(importance='core')]

    def get_secondary_skills(self, obj):
        return [ps.skill.name_en for ps in obj.project_skills.filter(importance='secondary')]


class ProjectIdeaDetailSerializer(serializers.ModelSerializer):
    """Detailed project idea serializer with full skill info."""

    project_skills = ProjectSkillSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectIdea
        fields = [
            'project_id',
            'title',
            'description',
            'target_role',
            'difficulty_level',
            'estimated_hours',
            'project_skills',
            'created_at',
        ]


# User Project Serializers

class UserProjectSerializer(serializers.ModelSerializer):
    """User project serializer with project details."""

    project = ProjectIdeaSerializer(read_only=True)
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserProject
        fields = [
            'user_project_id',
            'project',
            'status',
            'github_url',
            'live_demo_url',
            'notes',
            'started_at',
            'completed_at',
            'completion_percentage',
        ]

    def get_completion_percentage(self, obj):
        return obj.completion_percentage()


# Request Serializers

class GenerateProjectsRequestSerializer(serializers.Serializer):
    """Request serializer for project generation."""

    target_role = serializers.CharField(
        max_length=100,
        help_text="Target career role for projects."
    )
    difficulty_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced'],
        default='beginner',
        help_text="Project difficulty level."
    )
    skill_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Optional list of skill IDs to focus on."
    )
    language = serializers.ChoiceField(
        choices=['en', 'ru', 'uz'],
        default='en',
        help_text="Response language."
    )
    count = serializers.IntegerField(
        default=3,
        min_value=1,
        max_value=5,
        help_text="Number of project ideas to generate."
    )


class StartProjectRequestSerializer(serializers.Serializer):
    """Request serializer for starting a project."""
    pass  # project_id comes from URL


class UpdateProjectStatusRequestSerializer(serializers.Serializer):
    """Request serializer for updating project status."""

    status = serializers.ChoiceField(
        choices=['planned', 'in_progress', 'completed'],
        help_text="New project status."
    )
    github_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="GitHub repository URL."
    )
    live_demo_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="Live demo URL."
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Personal notes about the project."
    )


class GetRoleProjectsRequestSerializer(serializers.Serializer):
    """Query params serializer for getting role projects."""

    difficulty_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced'],
        required=False,
        help_text="Filter by difficulty level."
    )
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        required=False,
        help_text="Maximum number of projects to return."
    )
