"""
URL patterns for Jobs API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from jobs.views import JobCategoryViewSet, JobPostingViewSet

router = DefaultRouter()
router.register(r'categories', JobCategoryViewSet, basename='job-category')
router.register(r'postings', JobPostingViewSet, basename='job-posting')

urlpatterns = [
    path('', include(router.urls)),
]