"""
Main URL configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/cvs/', include('cvs.urls')),
    path('api/skills/', include('skills.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/career/', include('career.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/cvs/', include('cvs.urls')),
]

# media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)