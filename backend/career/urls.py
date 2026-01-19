"""
URL patterns for Career API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from career.views import (
    RoleViewSet, RecommendationViewSet,
    UserRecommendedRoleViewSet, GapAnalysisViewSet
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
router.register(r'my-recommended-roles', UserRecommendedRoleViewSet, basename='user-recommended-role')
router.register(r'gap-analyses', GapAnalysisViewSet, basename='gap-analysis')

urlpatterns = [
    path('', include(router.urls)),
]