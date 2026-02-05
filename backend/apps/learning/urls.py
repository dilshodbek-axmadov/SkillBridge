"""
Learning App URLs
=================
API endpoints for learning roadmaps.

Endpoints:
- POST /api/v1/roadmaps/generate/          - Generate new roadmap
- GET  /api/v1/roadmaps/                   - List user's roadmaps
- GET  /api/v1/roadmaps/{roadmap_id}/      - Get roadmap details
- DELETE /api/v1/roadmaps/{roadmap_id}/    - Deactivate roadmap
- GET  /api/v1/roadmaps/{roadmap_id}/progress/ - Get progress summary
- GET  /api/v1/roadmaps/items/{item_id}/   - Get item details
- PUT  /api/v1/roadmaps/items/{item_id}/status/ - Update item status
- GET  /api/v1/roadmaps/resources/         - List learning resources
"""

from django.urls import path
from apps.learning import views

app_name = 'learning'

urlpatterns = [
    # Roadmap generation
    path('generate/', views.GenerateRoadmapView.as_view(), name='generate_roadmap'),

    # Roadmap list and detail
    path('', views.UserRoadmapsView.as_view(), name='user_roadmaps'),
    path('<int:roadmap_id>/', views.RoadmapDetailView.as_view(), name='roadmap_detail'),
    path('<int:roadmap_id>/progress/', views.RoadmapProgressView.as_view(), name='roadmap_progress'),

    # Roadmap items
    path('items/<int:item_id>/', views.RoadmapItemDetailView.as_view(), name='item_detail'),
    path('items/<int:item_id>/status/', views.UpdateItemStatusView.as_view(), name='update_item_status'),

    # Learning resources
    path('resources/', views.LearningResourcesView.as_view(), name='learning_resources'),
]
