"""
CV App URLs
===========
URL routing for CV endpoints.
"""

from django.urls import path
from apps.cv.views import (
    CreateCVView,
    CVDetailView,
    CVListView,
    UpdateSectionsView,
    AutoPopulateView,
    AutoPopulateExistingView,
    SwitchTemplateView,
    ExportCVView,
    TemplateListView,
)

app_name = 'cv'

urlpatterns = [
    # CV CRUD
    path('', CVListView.as_view(), name='cv-list'),
    path('create/', CreateCVView.as_view(), name='cv-create'),
    path('<int:cv_id>/', CVDetailView.as_view(), name='cv-detail'),

    # Sections
    path('<int:cv_id>/sections/', UpdateSectionsView.as_view(), name='cv-sections'),

    # Auto-populate
    path('auto-populate/', AutoPopulateView.as_view(), name='cv-auto-populate'),
    path('<int:cv_id>/auto-populate/', AutoPopulateExistingView.as_view(), name='cv-auto-populate-existing'),

    # Templates
    path('templates/', TemplateListView.as_view(), name='cv-templates'),
    path('<int:cv_id>/template/', SwitchTemplateView.as_view(), name='cv-switch-template'),

    # Export
    path('<int:cv_id>/export/', ExportCVView.as_view(), name='cv-export'),
]
