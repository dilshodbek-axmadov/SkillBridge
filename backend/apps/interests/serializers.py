"""
Interests App Serializers
=========================
backend/apps/interests/serializers.py

Serializers for interest browsing and user interest management.
"""

from rest_framework import serializers
from .models import Interest, UserInterest


# ==================== INTEREST SERIALIZERS ====================

class InterestSerializer(serializers.ModelSerializer):
    """Full interest serializer."""

    class Meta:
        model = Interest
        fields = [
            'interest_id',
            'name_en',
            'name_ru',
            'name_uz',
            'category',
        ]
        read_only_fields = ['interest_id']


class InterestMinimalSerializer(serializers.ModelSerializer):
    """Minimal interest info for nested responses."""

    class Meta:
        model = Interest
        fields = ['interest_id', 'name_en', 'name_ru', 'name_uz', 'category']


# ==================== USER INTEREST SERIALIZERS ====================

class UserInterestSerializer(serializers.ModelSerializer):
    """User interest with nested interest details."""

    interest = InterestMinimalSerializer(read_only=True)

    class Meta:
        model = UserInterest
        fields = [
            'user_interest_id',
            'interest',
            'added_at',
        ]
        read_only_fields = ['user_interest_id', 'added_at']


class AddUserInterestSerializer(serializers.Serializer):
    """Request serializer for adding a single interest."""

    interest_id = serializers.IntegerField(
        help_text="ID of the interest to add"
    )

    def validate_interest_id(self, value):
        if not Interest.objects.filter(interest_id=value).exists():
            raise serializers.ValidationError("Interest not found.")
        return value


class BulkAddInterestsSerializer(serializers.Serializer):
    """Request serializer for adding multiple interests at once."""

    interest_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=20,
        help_text="List of interest IDs to add"
    )

    def validate_interest_ids(self, value):
        existing = set(
            Interest.objects.filter(interest_id__in=value)
            .values_list('interest_id', flat=True)
        )
        missing = set(value) - existing
        if missing:
            raise serializers.ValidationError(
                f"Interests not found: {list(missing)}"
            )
        return value


# ==================== RESPONSE SERIALIZERS ====================

class InterestCategorySerializer(serializers.Serializer):
    """Serializer for interest category."""

    code = serializers.CharField()
    name = serializers.CharField()
    count = serializers.IntegerField()
