"""
Users App Serializers 1

Serializers for user authentication
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, UserProfile, UserActivity
from apps.skills.models import Skill, UserSkill


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    user_type = serializers.ChoiceField(
        choices=User.UserType.choices,
        required=True,
        help_text='developer (talent) or recruiter (employer)',
    )

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'password',
            'password_confirm',
            'user_type',
            'first_name',
            'last_name',
            'phone',
            'preferred_language'
        ]
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
        }
    
    def validate(self, attrs):
        """Validate password match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        user_type = validated_data.pop('user_type', User.UserType.DEVELOPER)

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            preferred_language=validated_data.get('preferred_language', 'en'),
            user_type=user_type,
            recruiter_plan=User.RecruiterPlan.FREE,
        )
        
        # Create empty profile
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )
        
        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No user found with this email address."
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate password match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (read-only).
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'preferred_language',
            'user_type',
            'recruiter_plan',
            'profile_completed',
            'is_staff',
            'is_superuser',
            'created_at',
            'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'last_login', 'is_staff', 'is_superuser', 'user_type', 'recruiter_plan']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'profile_id',
            'user',
            'current_job_position',
            'desired_role',
            'experience_level',
            'cv_file_path',
            'profile_source',
            'bio',
            'profile_picture',
            'location',
            'github_url',
            'linkedin_url',
            'portfolio_url',
            'open_to_recruiters',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['profile_id', 'created_at', 'updated_at']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = UserProfile
        fields = [
            'current_job_position',
            'desired_role',
            'experience_level',
            'bio',
            'profile_picture',
            'location',
            'github_url',
            'linkedin_url',
            'portfolio_url',
            'open_to_recruiters',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password while logged in."""
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password': "Password fields didn't match."
            })
        return attrs


class CVUploadSerializer(serializers.Serializer):
    """
    Serializer for CV upload.
    """
    cv_file = serializers.FileField(required=True)
    
    def validate_cv_file(self, value):
        """Validate file type and size."""
        # Check file extension
        allowed_extensions = ['.pdf', '.docx', '.doc']
        file_ext = value.name.lower().split('.')[-1]
        
        if f'.{file_ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "File size must be under 5MB."
            )
        
        return value


class UserActivitySerializer(serializers.ModelSerializer):
    """Serialized row for activity feed APIs."""

    class Meta:
        model = UserActivity
        fields = [
            'activity_id',
            'activity_type',
            'description',
            'metadata',
            'link_path',
            'created_at',
        ]
        read_only_fields = fields
