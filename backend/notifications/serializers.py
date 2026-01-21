"""
Serializers for Notifications app
"""
from rest_framework import serializers
from .models import UserNotification, UserActivityLog


# ============== Notification Serializers ==============

class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer for listing notifications"""
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = UserNotification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'message', 'is_read', 'created_at', 'link_url', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at']

    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif diff < timedelta(days=30):
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            return obj.created_at.strftime("%B %d, %Y")


class NotificationDetailSerializer(serializers.ModelSerializer):
    """Serializer for notification details"""
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )

    class Meta:
        model = UserNotification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'message', 'is_read', 'created_at', 'link_url'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (admin/system use)"""
    class Meta:
        model = UserNotification
        fields = ['notification_type', 'title', 'message', 'link_url']


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )


class UnreadCountSerializer(serializers.Serializer):
    """Serializer for unread count response"""
    unread_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


# ============== Activity Log Serializers ==============

class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs"""
    activity_type_display = serializers.CharField(
        source='get_activity_type_display', read_only=True
    )

    class Meta:
        model = UserActivityLog
        fields = [
            'id', 'activity_type', 'activity_type_display',
            'activity_description', 'timestamp', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class ActivityLogCreateSerializer(serializers.Serializer):
    """Serializer for logging activities"""
    activity_type = serializers.ChoiceField(
        choices=UserActivityLog.ACTIVITY_TYPES
    )
    description = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)


class ActivitySummarySerializer(serializers.Serializer):
    """Serializer for activity summary"""
    activity_type = serializers.CharField()
    count = serializers.IntegerField()


# ============== Notification Settings Serializers ==============

class NotificationSettingsSerializer(serializers.Serializer):
    """Serializer for notification preferences"""
    email_notifications = serializers.BooleanField(default=True)
    job_match_alerts = serializers.BooleanField(default=True)
    skill_recommendations = serializers.BooleanField(default=True)
    roadmap_updates = serializers.BooleanField(default=True)
    market_trends = serializers.BooleanField(default=False)
    system_notifications = serializers.BooleanField(default=True)
