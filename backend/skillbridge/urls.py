from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/career/', include('apps.career.urls')),
    path('api/v1/skills/', include('apps.skills.urls')),
    path('api/v1/roadmaps/', include('apps.learning.urls')),
    path('api/v1/resources/', include('apps.learning.urls_resources')),
    path('api/v1/projects/', include('apps.projects.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/chatbot/', include('apps.chatbot.urls')),
    path('api/v1/cv/', include('apps.cv.urls')),
    path('api/v1/interests/', include('apps.interests.urls')),

    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Language switching
    path('i18n/', include('django.conf.urls.i18n')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
