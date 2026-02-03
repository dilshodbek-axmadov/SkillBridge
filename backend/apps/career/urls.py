"""
Career URLs
===========
backend/apps/career/urls.py
"""

from django.urls import path
from . import views

app_name = 'career'

urlpatterns = [
    # Assessment
    path('questions/', views.GetQuestionsView.as_view(), name='questions'),
    path('assessment/', views.SubmitAssessmentView.as_view(), name='submit_assessment'),
    path('status/', views.GetAssessmentStatusView.as_view(), name='status'),
    
    # Recommendations
    path('recommendations/', views.GetRecommendationsView.as_view(), name='recommendations'),
    path('select-role/', views.SelectRoleView.as_view(), name='select_role'),
    
    # Roles
    path('roles/', views.GetAllRolesView.as_view(), name='roles'),
]