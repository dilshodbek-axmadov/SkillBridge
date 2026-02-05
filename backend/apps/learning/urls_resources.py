"""
Learning Resources URLs
=======================
API endpoints for learning resources and recommendations.

Endpoints:
- GET  /api/v1/resources/skill/{skill_id}/     - Get AI-recommended resources for skill
- POST /api/v1/resources/{resource_id}/start/  - Start learning a resource
- PUT  /api/v1/resources/{resource_id}/progress/ - Update learning progress
- GET  /api/v1/resources/progress/             - Get user's learning progress
"""

from django.urls import path
from apps.learning import views

app_name = 'resources'

urlpatterns = [
    # Resource recommendations
    path('skill/<int:skill_id>/', views.SkillResourcesView.as_view(), name='skill_resources'),

    # Resource progress tracking
    path('<int:resource_id>/start/', views.StartResourceView.as_view(), name='start_resource'),
    path('<int:resource_id>/progress/', views.UpdateResourceProgressView.as_view(), name='update_progress'),

    # User progress
    path('progress/', views.UserLearningProgressView.as_view(), name='user_progress'),
]
