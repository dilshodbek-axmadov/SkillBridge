"""
Serializers for staff / in-app admin API (IsAdminUser).
"""

from rest_framework import serializers

from .models import User


class StaffUserListSerializer(serializers.ModelSerializer):
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
            'user_type',
            'recruiter_plan',
            'profile_completed',
            'is_active',
            'is_staff',
            'is_superuser',
            'created_at',
            'last_login',
        ]
        read_only_fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'user_type',
            'recruiter_plan',
            'profile_completed',
            'is_active',
            'is_staff',
            'is_superuser',
            'created_at',
            'last_login',
        ]


class StaffUserUpdateSerializer(serializers.Serializer):
    recruiter_plan = serializers.ChoiceField(choices=User.RecruiterPlan.choices, required=False)
    user_type = serializers.ChoiceField(choices=User.UserType.choices, required=False)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
