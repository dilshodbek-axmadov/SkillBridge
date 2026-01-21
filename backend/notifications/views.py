"""
Views for Notifications app
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import UserNotification, UserActivityLog
from .serializers import (
    NotificationListSerializer, NotificationDetailSerializer,
    MarkAsReadSerializer, UnreadCountSerializer,
    ActivityLogSerializer, ActivityLogCreateSerializer, ActivitySummarySerializer
)


# ============== Notification ViewSet ==============

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications

    Endpoints:
    - GET /api/notifications/ - List user's notifications
    - GET /api/notifications/{id}/ - Get notification details
    - DELETE /api/notifications/{id}/ - Delete a notification
    - POST /api/notifications/mark-read/ - Mark notifications as read
    - POST /api/notifications/mark-all-read/ - Mark all notifications as read
    - GET /api/notifications/unread-count/ - Get unread notification count
    - DELETE /api/notifications/clear-all/ - Clear all notifications
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'delete', 'post']

    def get_queryset(self):
        queryset = UserNotification.objects.filter(user=self.request.user)

        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """Get notification and mark as read"""
        instance = self.get_object()
        instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_read(self, request):
        """Mark specific notifications as read"""
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids', [])

        if notification_ids:
            notifications = UserNotification.objects.filter(
                user=request.user,
                id__in=notification_ids,
                is_read=False
            )
        else:
            # If no IDs provided, mark all as read
            notifications = UserNotification.objects.filter(
                user=request.user,
                is_read=False
            )

        updated_count = notifications.update(is_read=True)

        return Response({
            'message': f'{updated_count} notification(s) marked as read',
            'updated_count': updated_count
        })

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated_count = UserNotification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            'message': 'All notifications marked as read',
            'updated_count': updated_count
        })

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get unread notification count"""
        unread = UserNotification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        total = UserNotification.objects.filter(user=request.user).count()

        return Response(UnreadCountSerializer({
            'unread_count': unread,
            'total_count': total
        }).data)

    @action(detail=False, methods=['delete'], url_path='clear-all')
    def clear_all(self, request):
        """Clear all notifications"""
        deleted_count, _ = UserNotification.objects.filter(
            user=request.user
        ).delete()

        return Response({
            'message': 'All notifications cleared',
            'deleted_count': deleted_count
        })

    @action(detail=True, methods=['post'], url_path='mark-unread')
    def mark_unread(self, request, pk=None):
        """Mark a specific notification as unread"""
        notification = self.get_object()
        notification.mark_as_unread()

        return Response({
            'message': 'Notification marked as unread',
            'notification': NotificationDetailSerializer(notification).data
        })


# ============== Activity Log ViewSet ==============

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user activity logs

    Endpoints:
    - GET /api/notifications/activity/ - List user's activity logs
    - GET /api/notifications/activity/{id}/ - Get activity log details
    - GET /api/notifications/activity/summary/ - Get activity summary
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        queryset = UserActivityLog.objects.filter(user=self.request.user)

        # Filter by activity type
        activity_type = self.request.query_params.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        if from_date:
            queryset = queryset.filter(timestamp__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(timestamp__date__lte=to_date)

        return queryset.order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get activity summary for the last N days"""
        days = int(request.query_params.get('days', 30))
        summary = UserActivityLog.get_user_activity_summary(request.user, days=days)

        return Response({
            'days': days,
            'summary': ActivitySummarySerializer(summary, many=True).data
        })


# ============== Log Activity View ==============

class LogActivityView(APIView):
    """
    Log a user activity

    POST /api/notifications/activity/log/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ActivityLogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        activity = UserActivityLog.log_activity(
            user=request.user,
            activity_type=serializer.validated_data['activity_type'],
            description=serializer.validated_data.get('description', ''),
            ip_address=ip_address,
            metadata=serializer.validated_data.get('metadata')
        )

        return Response({
            'message': 'Activity logged successfully',
            'activity': ActivityLogSerializer(activity).data
        }, status=status.HTTP_201_CREATED)


# ============== Notification Stats View ==============

class NotificationStatsView(APIView):
    """
    Get notification statistics

    GET /api/notifications/stats/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count

        user = request.user

        # Count by type
        by_type = UserNotification.objects.filter(user=user).values(
            'notification_type'
        ).annotate(count=Count('id')).order_by('-count')

        # Count by read status
        total = UserNotification.objects.filter(user=user).count()
        unread = UserNotification.objects.filter(user=user, is_read=False).count()
        read = total - unread

        # Recent notifications
        recent = UserNotification.objects.filter(user=user).order_by('-created_at')[:5]

        return Response({
            'total_notifications': total,
            'unread_count': unread,
            'read_count': read,
            'by_type': list(by_type),
            'recent_notifications': NotificationListSerializer(recent, many=True).data
        })
