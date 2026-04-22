"""
User App Serializers 2

Serializers for profile and skill management
"""

from rest_framework import serializers
from django.db import transaction

from .models import User, UserProfile
from apps.skills.models import Skill, UserSkill


class SkillListSerializer(serializers.ModelSerializer):
    """Simple skill serializer for listing available skills."""
    
    class Meta:
        model = Skill
        fields = ['skill_id', 'name_en', 'name_ru', 'name_uz', 'category', 'normalized_key']


class UserSkillSerializer(serializers.ModelSerializer):
    """User skill with details."""
    
    skill = SkillListSerializer(read_only=True)
    skill_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserSkill
        fields = [
            'user_skill_id',
            'skill',
            'skill_id',
            'proficiency_level',
            'years_of_experience',
            'source',
            'is_primary',
            'added_at',
            'updated_at'
        ]
        read_only_fields = ['user_skill_id', 'added_at', 'updated_at']


class AddUserSkillSerializer(serializers.Serializer):
    """Add a single skill to user profile."""
    
    skill_id = serializers.IntegerField(required=True)
    proficiency_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        default='beginner'
    )
    years_of_experience = serializers.FloatField(default=0.0, min_value=0.0)
    is_primary = serializers.BooleanField(default=False)
    
    def validate_skill_id(self, value):
        """Check if skill exists."""
        if not Skill.objects.filter(skill_id=value).exists():
            raise serializers.ValidationError("Skill does not exist")
        return value


class UpdateUserSkillSerializer(serializers.Serializer):
    """Update user skill proficiency/experience."""
    
    proficiency_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        required=False
    )
    years_of_experience = serializers.FloatField(required=False, min_value=0.0)
    is_primary = serializers.BooleanField(required=False)


class BulkAddSkillsSerializer(serializers.Serializer):
    """Add multiple skills at once (for initial profile setup)."""
    
    skills = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text="List of skills: [{'skill_id': 1, 'proficiency_level': 'beginner', 'years_of_experience': 0.0}]"
    )
    
    def validate_skills(self, skills_list):
        """Validate each skill in the list."""
        validated_skills = []
        
        for skill_data in skills_list:
            # Check required fields
            if 'skill_id' not in skill_data:
                raise serializers.ValidationError("Each skill must have 'skill_id'")
            
            skill_id = skill_data['skill_id']
            
            # Check if skill exists
            if not Skill.objects.filter(skill_id=skill_id).exists():
                raise serializers.ValidationError(f"Skill ID {skill_id} does not exist")
            
            # Set defaults
            validated_skill = {
                'skill_id': skill_id,
                'proficiency_level': skill_data.get('proficiency_level', 'beginner'),
                'years_of_experience': skill_data.get('years_of_experience', 0.0),
                'is_primary': skill_data.get('is_primary', False)
            }
            
            # Validate proficiency level
            if validated_skill['proficiency_level'] not in ['beginner', 'intermediate', 'advanced', 'expert']:
                raise serializers.ValidationError(f"Invalid proficiency level: {validated_skill['proficiency_level']}")
            
            validated_skills.append(validated_skill)
        
        return validated_skills


class StepByStepProfileSerializer(serializers.Serializer):
    """
    Complete step-by-step profile creation.
    
    Expected data:
    {
        "current_job_position": "Frontend Developer",
        "desired_role": "Full-Stack Developer",
        "experience_level": "mid",
        "skills": [
            {"skill_id": 1, "proficiency_level": "intermediate", "years_of_experience": 2.0},
            {"skill_id": 5, "proficiency_level": "beginner", "years_of_experience": 0.5}
        ],
        "bio": "Optional bio text"
    }
    """

    # Step 1: Current job position (optional - user might be a student)
    current_job_position = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default='',
        help_text="Current job position"
    )

    # Step 1: Desired role (required - drives gap analysis and roadmap)
    desired_role = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Target career role user wants to achieve"
    )
    
    # Step 2: Experience level
    experience_level = serializers.ChoiceField(
        choices=['beginner', 'junior', 'mid', 'senior', 'lead'],
        required=True
    )
    
    # Step 3: Skills
    skills = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        required=True,
        help_text="At least 1 skill required"
    )
    
    # Optional bio
    bio = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    
    def validate_skills(self, skills_list):
        """Validate skills list."""
        if not skills_list:
            raise serializers.ValidationError("At least one skill is required")
        
        validated_skills = []
        
        for skill_data in skills_list:
            if 'skill_id' not in skill_data:
                raise serializers.ValidationError("Each skill must have 'skill_id'")
            
            skill_id = skill_data['skill_id']
            
            # Check if skill exists
            if not Skill.objects.filter(skill_id=skill_id).exists():
                raise serializers.ValidationError(f"Skill ID {skill_id} does not exist")
            
            validated_skill = {
                'skill_id': skill_id,
                'proficiency_level': skill_data.get('proficiency_level', 'beginner'),
                'years_of_experience': skill_data.get('years_of_experience', 0.0),
                'is_primary': skill_data.get('is_primary', False)
            }
            
            validated_skills.append(validated_skill)
        
        return validated_skills
    
    @transaction.atomic
    def create_profile(self, user):
        """
        Create complete user profile from validated data.
        
        Returns:
            {
                'profile': UserProfile,
                'skills_added': int
            }
        """
        validated_data = self.validated_data
        
        # Update profile
        profile = user.profile
        profile.current_job_position = validated_data.get('current_job_position', '')
        profile.desired_role = validated_data['desired_role']
        profile.experience_level = validated_data['experience_level']
        profile.bio = validated_data.get('bio', '')
        profile.profile_source = 'manual'
        profile.save()
        
        # Add skills
        skills_added = 0
        for skill_data in validated_data['skills']:
            user_skill, created = UserSkill.objects.update_or_create(
                user=user,
                skill_id=skill_data['skill_id'],
                defaults={
                    'proficiency_level': skill_data['proficiency_level'],
                    'years_of_experience': skill_data['years_of_experience'],
                    'is_primary': skill_data['is_primary'],
                    'source': 'manual'
                }
            )
            if created:
                skills_added += 1
        
        # Mark profile as completed
        user.profile_completed = True
        user.save()
        
        return {
            'profile': profile,
            'skills_added': skills_added,
        }


class UserProfileSummarySerializer(serializers.ModelSerializer):
    """Complete user profile summary."""
    
    skills = UserSkillSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'current_job_position',
            'desired_role',
            'experience_level',
            'bio',
            'profile_source',
            'skills',
        ]