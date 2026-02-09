"""
Jobs App URLs
=============
API endpoints for job listings and recommendations.

- GET /api/v1/jobs/              - List/search jobs with filters
- GET /api/v1/jobs/recommended/  - Personalized job recommendations
- GET /api/v1/jobs/filters/      - Available filter options
- GET /api/v1/jobs/<job_id>/     - Job detail
"""

from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.JobListView.as_view(), name='job_list'),
    path('recommended/', views.RecommendedJobsView.as_view(), name='recommended'),
    path('filters/', views.JobFiltersView.as_view(), name='filters'),
    path('<int:job_id>/', views.JobDetailView.as_view(), name='job_detail'),
]
