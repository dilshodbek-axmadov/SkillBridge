"""
URL configuration for Learning app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LearningRoadmapViewSet,
    RoadmapItemViewSet,
    LearningResourceViewSet,
    RoadmapResourceViewSet
)

app_name = 'learning'

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'roadmaps', LearningRoadmapViewSet, basename='roadmap')
router.register(r'roadmap-items', RoadmapItemViewSet, basename='roadmap-item')
router.register(r'resources', LearningResourceViewSet, basename='resource')
router.register(r'roadmap-resources', RoadmapResourceViewSet, basename='roadmap-resource')

urlpatterns = [
    path('', include(router.urls)),
]