"""
Recruiter API routes.
"""

from django.urls import path

from . import views

app_name = 'recruiters'

urlpatterns = [
    path('dashboard/', views.RecruiterDashboardView.as_view(), name='dashboard'),

    path('candidates/', views.CandidateListView.as_view(), name='candidate_list'),
    path('candidates/<int:candidate_id>/', views.CandidateDetailView.as_view(), name='candidate_detail'),

    path('saved-candidates/', views.SavedCandidateListCreateView.as_view(), name='saved_candidate_list_create'),
    path('saved-candidates/<int:saved_id>/', views.SavedCandidateDetailView.as_view(), name='saved_candidate_detail'),

    path('saved-searches/', views.SavedSearchListCreateView.as_view(), name='saved_search_list_create'),
    path('saved-searches/<int:search_id>/', views.SavedSearchDetailView.as_view(), name='saved_search_detail'),

    path('jobs/', views.RecruiterJobListCreateView.as_view(), name='recruiter_jobs'),
    path('jobs/<int:job_id>/', views.RecruiterJobDetailView.as_view(), name='recruiter_job_detail'),
]

