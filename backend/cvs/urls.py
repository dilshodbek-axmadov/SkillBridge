"""
URL patterns for CVs app
"""
from django.urls import path
from .views import (
    CVUploadView, UploadedCVListView, UploadedCVDetailView
)

urlpatterns = [
    path('upload/', CVUploadView.as_view(), name='cv-upload'),
    path('uploaded/', UploadedCVListView.as_view(), name='uploaded-cv-list'),
    path('uploaded/<int:pk>/', UploadedCVDetailView.as_view(), name='uploaded-cv-detail'),
]