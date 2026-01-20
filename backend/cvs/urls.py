"""
URL patterns for CVs app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CVUploadView, UploadedCVListView, UploadedCVDetailView,
    UserCVViewSet, CVSectionViewSet, WorkExperienceViewSet,
    EducationViewSet, ProjectViewSet, CVGenerationViewSet, CVExportViewSet
)

router = DefaultRouter()
router.register(r'my-cvs', UserCVViewSet, basename='user-cv')
router.register(r'sections', CVSectionViewSet, basename='cv-section')
router.register(r'experience', WorkExperienceViewSet, basename='work-experience')
router.register(r'education', EducationViewSet, basename='education')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'generate', CVGenerationViewSet, basename='cv-generation')
router.register(r'export', CVExportViewSet, basename='cv-export')

urlpatterns = [
    # CV Upload endpoints (existing)
    path('upload/', CVUploadView.as_view(), name='cv-upload'),
    path('uploaded/', UploadedCVListView.as_view(), name='uploaded-cv-list'),
    path('uploaded/<int:pk>/', UploadedCVDetailView.as_view(), name='uploaded-cv-detail'),

    # Router URLs
    path('', include(router.urls)),
]
