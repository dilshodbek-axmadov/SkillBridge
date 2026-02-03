"""
Career Serializers
==================
backend/apps/career/serializers.py
"""

from rest_framework import serializers
from .models import ITRole, AssessmentQuestion, UserAssessment, CareerRecommendation


class ITRoleSerializer(serializers.ModelSerializer):
    """Serialize IT roles."""
    
    class Meta:
        model = ITRole
        fields = [
            'id', 'name', 'description',
            'difficulty_level', 'avg_salary_uzs', 'job_demand',
            'created_at'
        ]


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    """Serialize assessment questions."""
    
    class Meta:
        model = AssessmentQuestion
        fields = [
            'id', 'category', 'question_text', 'question_type',
            'options', 'order'
        ]


class SubmitAssessmentSerializer(serializers.Serializer):
    """
    Validate assessment submission.
    
    Expected:
    {
        "responses": {
            "1": 0,  // question_id: option_index
            "2": 2,
            "3": 1,
            ...
        }
    }
    """
    
    responses = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
        help_text="Question ID -> Selected option index"
    )
    
    def validate_responses(self, responses):
        """Validate responses format."""
        if not responses:
            raise serializers.ValidationError("Responses cannot be empty")
        
        # Convert string keys to integers
        try:
            return {int(k): int(v) for k, v in responses.items()}
        except ValueError:
            raise serializers.ValidationError("Invalid response format")


class UserAssessmentSerializer(serializers.ModelSerializer):
    """Serialize user assessment."""
    
    class Meta:
        model = UserAssessment
        fields = [
            'id', 'responses', 'completed', 'completed_at',
            'problem_solving_score', 'creativity_score',
            'data_analysis_score', 'technical_depth_score',
            'communication_score', 'visual_design_score',
            'created_at'
        ]
        read_only_fields = ['created_at', 'completed_at']


class CareerRecommendationSerializer(serializers.ModelSerializer):
    """Serialize career recommendations."""
    
    role = ITRoleSerializer(read_only=True)
    
    class Meta:
        model = CareerRecommendation
        fields = [
            'id', 'role', 'match_score', 'rank', 'reasoning',
            'user_selected', 'user_viewed', 'created_at'
        ]
        read_only_fields = ['created_at']


class SelectRoleSerializer(serializers.Serializer):
    """
    Select a recommended role.
    
    Expected:
    {
        "recommendation_id": 123
    }
    """
    
    recommendation_id = serializers.IntegerField(required=True)