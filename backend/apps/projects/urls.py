"""
Projects App URLs
=================
API endpoints for project ideas and user projects.

Endpoints:
- POST /api/v1/projects/generate/              - Generate AI project ideas
- GET  /api/v1/projects/role/{role_name}/      - Get projects for a role
- GET  /api/v1/projects/{project_id}/          - Get project details
- GET  /api/v1/projects/{project_id}/skills/   - Get project skills
- POST /api/v1/projects/{project_id}/start/    - Start a project
- PUT  /api/v1/projects/{project_id}/status/   - Update project status
- GET  /api/v1/projects/my/                    - Get user's projects
"""

from django.urls import path
from apps.projects import views

app_name = 'projects'

urlpatterns = [
    # Project generation
    path('generate/', views.GenerateProjectsView.as_view(), name='generate_projects'),

    # User's projects
    path('my/', views.UserProjectsView.as_view(), name='user_projects'),

    # All projects (browse)
    path('all/', views.AllProjectsView.as_view(), name='all_projects'),

    # Role-based projects
    path('role/<str:role_name>/', views.RoleProjectsView.as_view(), name='role_projects'),

    # Project details and actions
    path('<int:project_id>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:project_id>/skills/', views.ProjectSkillsView.as_view(), name='project_skills'),
    path('<int:project_id>/start/', views.StartProjectView.as_view(), name='start_project'),
    path('<int:project_id>/status/', views.UpdateProjectStatusView.as_view(), name='update_status'),
]
