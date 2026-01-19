"""
URL patterns for Skills API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from skills.views import SkillViewSet, SkillLevelViewSet, UserSkillViewSet

router = DefaultRouter()
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'levels', SkillLevelViewSet, basename='skill-level')
router.register(r'user-skills', UserSkillViewSet, basename='user-skill')

urlpatterns = [
    path('', include(router.urls)),
]