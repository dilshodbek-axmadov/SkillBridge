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
    CVPayView,
    CVAccessStatusView,
)

app_name = 'cv'

urlpatterns = [
    # CV CRUD
    path('', CVListView.as_view(), name='cv-list'),
    path('create/', CreateCVView.as_view(), name='cv-create'),

    # Sections
    path('<int:cv_id>/sections/', UpdateSectionsView.as_view(), name='cv-sections'),

    # Auto-populate
    path('auto-populate/', AutoPopulateView.as_view(), name='cv-auto-populate'),
    path('<int:cv_id>/auto-populate/', AutoPopulateExistingView.as_view(), name='cv-auto-populate-existing'),

    # Templates
    path('templates/', TemplateListView.as_view(), name='cv-templates'),
    path('<int:cv_id>/template/', SwitchTemplateView.as_view(), name='cv-switch-template'),

    # Export (primary + aliases for compatibility)
    path('<int:cv_id>/export/', ExportCVView.as_view(), name='cv-export'),
    path('<int:cv_id>/export', ExportCVView.as_view(), name='cv-export-no-slash'),
    path('export/<int:cv_id>/', ExportCVView.as_view(), name='cv-export-alt'),
    path('<int:cv_id>/download/', ExportCVView.as_view(), name='cv-download'),

    # CV payments (download)
    path('<int:cv_id>/pay/', CVPayView.as_view(), name='cv-pay'),
    path('<int:cv_id>/access-status/', CVAccessStatusView.as_view(), name='cv-access-status'),

    # CV detail (keep generic route last)
    path('<int:cv_id>/', CVDetailView.as_view(), name='cv-detail'),
]
