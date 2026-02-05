from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/career/', include('apps.career.urls')),
    path('api/v1/skills/', include('apps.skills.urls')),
    path('api/v1/roadmaps/', include('apps.learning.urls')),
    path('api/v1/resources/', include('apps.learning.urls_resources')),
    path('api/v1/projects/', include('apps.projects.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    