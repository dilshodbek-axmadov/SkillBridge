"""
Analytics App URLs
==================
API endpoints for dashboard analytics.

Market Analytics (Public):
- GET /api/v1/analytics/dashboard/              - Complete dashboard summary
- GET /api/v1/analytics/market/overview/        - Market overview stats
- GET /api/v1/analytics/market/skills/trending/ - Trending skills
- GET /api/v1/analytics/market/skills/{id}/trend/ - Skill trend history
- GET /api/v1/analytics/market/salaries/        - Salary insights
- GET /api/v1/analytics/market/categories/      - Jobs by category

User Analytics (Authenticated):
- GET /api/v1/analytics/user/progress/          - Current user's progress
- GET /api/v1/analytics/user/{user_id}/progress/ - Specific user's progress
"""

from django.urls import path
from apps.analytics import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard summary (all-in-one)
    path('dashboard/', views.DashboardSummaryView.as_view(), name='dashboard'),

    # Market analytics
    path('market/overview/', views.MarketOverviewView.as_view(), name='market_overview'),
    path('market/skills/trending/', views.TrendingSkillsView.as_view(), name='trending_skills'),
    path('market/skills/<int:skill_id>/trend/', views.SkillTrendView.as_view(), name='skill_trend'),
    path('market/salaries/', views.SalaryInsightsView.as_view(), name='salaries'),
    path('market/categories/', views.JobCategoriesView.as_view(), name='categories'),

    # User analytics
    path('user/progress/', views.UserProgressView.as_view(), name='user_progress'),
    path('user/<int:user_id>/progress/', views.UserProgressByIdView.as_view(), name='user_progress_by_id'),
]
