"""
URL configuration for Analytics API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MarketTrendViewSet,
    SkillDemandViewSet,
    SalaryAnalyticsViewSet,
    SkillCombinationViewSet,
    JobMarketInsightsViewSet,
    DashboardViewSet
)

app_name = 'analytics'

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'trends', MarketTrendViewSet, basename='market-trend')
router.register(r'skills', SkillDemandViewSet, basename='skill-demand')
router.register(r'salary', SalaryAnalyticsViewSet, basename='salary')
router.register(r'combinations', SkillCombinationViewSet, basename='skill-combination')
router.register(r'market', JobMarketInsightsViewSet, basename='job-market')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
