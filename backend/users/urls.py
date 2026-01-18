from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView, UserProfileView, ChangePasswordView,
    UpdateProfileView, UpdateExtendedProfileView, UserInterestViewSet
)

router = DefaultRouter()
router.register(r'interests', UserInterestViewSet, basename='user-interests')

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('profile/extended/', UpdateExtendedProfileView.as_view(), name='update-extended-profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # User interests
    path('', include(router.urls)),
]