"""
URL patterns for Notifications app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, ActivityLogViewSet,
    LogActivityView, NotificationStatsView
)

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'activity', ActivityLogViewSet, basename='activity-log')

urlpatterns = [
    # Log activity
    path('activity/log/', LogActivityView.as_view(), name='log-activity'),

    # Notification stats
    path('stats/', NotificationStatsView.as_view(), name='notification-stats'),

    # Router URLs
    path('', include(router.urls)),
]
