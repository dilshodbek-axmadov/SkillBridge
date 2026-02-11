"""
Skills URLs
===========
backend/apps/skills/urls.py

API Endpoints:
- POST /api/v1/skills/analyze-gap/           - Analyze skill gaps
- GET  /api/v1/skills/gaps/                  - Get user's skill gaps
- GET  /api/v1/skills/gaps/{gap_id}/         - Get specific gap details
- PUT  /api/v1/skills/gaps/{gap_id}/status/  - Update gap status
- GET  /api/v1/skills/market-trends/         - Get market trends
- GET  /api/v1/skills/categories/            - Get skill categories
"""

from django.urls import path
from . import views

app_name = 'skills'

urlpatterns = [
    # Skill Gap Analysis
    path('analyze-gap/', views.AnalyzeGapView.as_view(), name='analyze_gap'),

    # User Gaps
    path('gaps/', views.UserGapsView.as_view(), name='user_gaps'),
    path('gaps/clear/', views.ClearGapsView.as_view(), name='clear_gaps'),
    path('gaps/<int:gap_id>/', views.GapDetailView.as_view(), name='gap_detail'),
    path('gaps/<int:gap_id>/status/', views.UpdateGapStatusView.as_view(), name='update_gap_status'),

    # Market Data
    path('market-trends/', views.MarketTrendsView.as_view(), name='market_trends'),
    path('categories/', views.SkillCategoriesView.as_view(), name='categories'),
]
