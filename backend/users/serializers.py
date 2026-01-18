"""
Serializers for user authentication and profile
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from users.models import UserProfile, UserInterest

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
            'bio', 'linkedin_url', 'github_url', 'portfolio_url', 'updated_at'
        ]
        read_only_fields = ['updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    userprofile = UserProfileSerializer(read_only=True)
    user_interests = UserInterestSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'location', 'onboarding_method',
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
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'phone', 'location']
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
        fields = ['first_name', 'last_name', 'phone', 'location']


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating extended user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'current_role', 'experience_level', 'preferred_work_type',
            'availability_status', 'bio', 'linkedin_url', 'github_url', 'portfolio_url'
        ]