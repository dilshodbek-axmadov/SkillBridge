"""
Interests URLs
==============
backend/apps/interests/urls.py

API Endpoints:
- GET  /api/v1/interests/browse/                      - List all interests
- GET  /api/v1/interests/search/?q=...                - Search interests
- GET  /api/v1/interests/categories/                  - List categories
- GET  /api/v1/interests/my-interests/                - Get user's interests
- POST /api/v1/interests/add/                         - Add single interest
- POST /api/v1/interests/bulk-add/                    - Add multiple interests
- DELETE /api/v1/interests/delete/<user_interest_id>/  - Remove interest
"""

from django.urls import path
from . import views

app_name = 'interests'

urlpatterns = [
    # ===== BROWSING (Public) =====
    path('browse/', views.GetAllInterestsView.as_view(), name='browse_interests'),
    path('search/', views.SearchInterestsView.as_view(), name='search_interests'),
    path('categories/', views.GetInterestCategoriesView.as_view(), name='interest_categories'),

    # ===== USER INTERESTS (Authenticated) =====
    path('my-interests/', views.GetMyInterestsView.as_view(), name='my_interests'),
    path('add/', views.AddInterestView.as_view(), name='add_interest'),
    path('bulk-add/', views.BulkAddInterestsView.as_view(), name='bulk_add_interests'),
    path('delete/<int:user_interest_id>/', views.DeleteInterestView.as_view(), name='delete_interest'),
]
