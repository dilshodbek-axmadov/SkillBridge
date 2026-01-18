"""
Serializers for user authentication and profile
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from users.models import UserProfile, UserInterest
from career.models import Role

User = get_user_model()


class UserInterestSerializer(serializers.ModelSerializer):
    """Serializer for user interests"""
    interest_area_display = serializers.CharField(source='get_interest_area_display', read_only=True)
    
    class Meta:
        model = UserInterest
        fields = ['id', 'interest_area', 'interest_area_display', 'priority_level']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)
    preferred_work_type_display = serializers.CharField(source='get_preferred_work_type_display', read_only=True)
    availability_status_display = serializers.CharField(source='get_availability_status_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'current_role', 'experience_level', 'experience_level_display',
            'preferred_work_type', 'preferred_work_type_display',
            'availability_status', 'availability_status_display',
            'bio', 'linkedin_url', 'github_url', 'portfolio_url', 'updated_at', 'career_preferences'
        ]
        read_only_fields = ['updated_at', 'career_preferences']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    userprofile = UserProfileSerializer(read_only=True)
    user_interests = UserInterestSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    it_knowledge_level_display = serializers.CharField(source='get_it_knowledge_level_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'location', 'onboarding_method', 'it_knowledge_level', 'it_knowledge_level_display'
            'profile_completion_percentage', 'registration_date',
            'userprofile', 'user_interests'
        ]
        read_only_fields = ['registration_date', 'profile_completion_percentage']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'phone']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Create user profile automatically
        UserProfile.objects.create(user=user)
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password')
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating extended user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'current_role', 'experience_level', 'preferred_work_type',
            'availability_status', 'bio', 'linkedin_url', 'github_url', 'portfolio_url'
        ]


class CareerDiscoveryQuestionSerializer(serializers.Serializer):
    """Serializer for career discovery questions"""
    id = serializers.CharField()
    step = serializers.IntegerField()
    question = serializers.CharField()
    type = serializers.CharField()
    required = serializers.BooleanField()
    options = serializers.ListField()


class CareerDiscoveryResponseSerializer(serializers.Serializer):
    """Serializer for career discovery responses"""
    responses = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dict of question_id -> answer_value"
    )
    
    def validate_responses(self, value):
        """Validate that all required questions are answered"""
        from users.career_discovery import CAREER_DISCOVERY_QUESTIONS
        
        required_questions = [
            q['id'] for q in CAREER_DISCOVERY_QUESTIONS 
            if q.get('required', False) and q['id'] != 'knowledge_check'
        ]
        
        for required_q in required_questions:
            if required_q not in value:
                raise serializers.ValidationError(
                    f"Required question '{required_q}' not answered"
                )
        
        return value


class CareerRecommendationSerializer(serializers.Serializer):
    """Serializer for career recommendations"""
    role_id = serializers.IntegerField(allow_null=True)
    role_title = serializers.CharField()
    role_description = serializers.CharField()
    match_score = serializers.FloatField()
    demand_score = serializers.FloatField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)


# Onboarding serializers
class OnboardingStep1Serializer(serializers.Serializer):
    """Step 1: Basic info (already collected in registration)"""
    pass  # This step is already done during registration


class OnboardingStep2Serializer(serializers.Serializer):
    """Step 2: Professional background"""
    current_role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    experience_level = serializers.ChoiceField(
        choices=['junior', 'mid', 'senior'],
        required=True
    )
    preferred_work_type = serializers.ChoiceField(
        choices=['remote', 'onsite', 'hybrid'],
        required=True
    )
    availability_status = serializers.ChoiceField(
        choices=['available', 'employed', 'not_looking'],
        required=True
    )


class OnboardingStep3Serializer(serializers.Serializer):
    """Step 3: Career interests"""
    interests = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        help_text="List of interests with priority: [{'interest_area': 'web_dev', 'priority_level': 1}, ...]"
    )
    
    def validate_interests(self, value):
        """Validate interest areas"""
        valid_areas = dict(UserInterest.INTEREST_AREAS).keys()
        
        for interest in value:
            if 'interest_area' not in interest or 'priority_level' not in interest:
                raise serializers.ValidationError(
                    "Each interest must have 'interest_area' and 'priority_level'"
                )
            
            if interest['interest_area'] not in valid_areas:
                raise serializers.ValidationError(
                    f"Invalid interest area: {interest['interest_area']}"
                )
            
            try:
                priority = int(interest['priority_level'])
                if priority < 1:
                    raise ValueError
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "priority_level must be a positive integer"
                )
        
        return value


class OnboardingStep4Serializer(serializers.Serializer):
    """Step 4: Current skills"""
    skills = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of skills: [{'skill_name': 'Python', 'level': 'intermediate'}, ...]"
    )
    
    def validate_skills(self, value):
        """Validate skills"""
        valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        
        for skill_data in value:
            if 'skill_name' not in skill_data or 'level' not in skill_data:
                raise serializers.ValidationError(
                    "Each skill must have 'skill_name' and 'level'"
                )
            
            if skill_data['level'].lower() not in valid_levels:
                raise serializers.ValidationError(
                    f"Invalid skill level: {skill_data['level']}. "
                    f"Must be one of: {', '.join(valid_levels)}"
                )
        
        return value


class OnboardingStep5Serializer(serializers.Serializer):
    """Step 5: Career goals"""
    target_role_id = serializers.IntegerField(required=True)
    
    def validate_target_role_id(self, value):
        """Validate that role exists"""
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid role ID")
        return value


class CompleteOnboardingSerializer(serializers.Serializer):
    """Complete onboarding data - all steps at once"""
    
    # Step 2: Professional background
    current_role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    experience_level = serializers.ChoiceField(
        choices=['junior', 'mid', 'senior'],
        required=True
    )
    preferred_work_type = serializers.ChoiceField(
        choices=['remote', 'onsite', 'hybrid'],
        required=True
    )
    availability_status = serializers.ChoiceField(
        choices=['available', 'employed', 'not_looking'],
        required=True
    )
    
    # Step 3: Career interests
    interests = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of interests: [{'interest_area': 'web_dev', 'priority_level': 1}, ...]"
    )
    
    # Step 4: Current skills
    skills = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of skills: [{'skill_name': 'Python', 'level': 'intermediate'}, ...]"
    )
    
    # Step 5: Career goals
    target_role_id = serializers.IntegerField(required=True)
    
    def validate_interests(self, value):
        """Validate interest areas"""
        valid_areas = dict(UserInterest.INTEREST_AREAS).keys()
        
        for interest in value:
            if 'interest_area' not in interest or 'priority_level' not in interest:
                raise serializers.ValidationError(
                    "Each interest must have 'interest_area' and 'priority_level'"
                )
            
            if interest['interest_area'] not in valid_areas:
                raise serializers.ValidationError(
                    f"Invalid interest area: {interest['interest_area']}"
                )
        
        return value
    
    def validate_skills(self, value):
        """Validate skills"""
        valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        
        for skill_data in value:
            if 'skill_name' not in skill_data or 'level' not in skill_data:
                raise serializers.ValidationError(
                    "Each skill must have 'skill_name' and 'level'"
                )
            
            if skill_data['level'].lower() not in valid_levels:
                raise serializers.ValidationError(
                    f"Invalid skill level: {skill_data['level']}"
                )
        
        return value
    
    def validate_target_role_id(self, value):
        """Validate that role exists"""
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid role ID")
        return value