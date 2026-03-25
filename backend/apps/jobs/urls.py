"""
Jobs App URLs
=============
API endpoints for job listings, recommendations, and extraction management.
"""

from django.urls import path
from . import views
from . import views_extraction

app_name = 'jobs'

urlpatterns = [
    # Public job endpoints
    path('', views.JobListView.as_view(), name='job_list'),
    path('recommended/', views.RecommendedJobsView.as_view(), name='recommended'),
    path('filters/', views.JobFiltersView.as_view(), name='filters'),
    path('<int:job_id>/apply/', views.JobApplyView.as_view(), name='job_apply'),
    path('<int:job_id>/', views.JobDetailView.as_view(), name='job_detail'),

    # Extraction admin endpoints (IsAdminUser)
    path('extraction-runs/', views_extraction.ExtractionRunListView.as_view(), name='extraction_runs'),
    path('extraction-runs/trigger/', views_extraction.ManualExtractionView.as_view(), name='extraction_trigger'),
    path('extraction-runs/<int:run_id>/retry/', views_extraction.RetryExtractionView.as_view(), name='extraction_retry'),
    path('extraction-stats/', views_extraction.ExtractionStatsView.as_view(), name='extraction_stats'),
]
