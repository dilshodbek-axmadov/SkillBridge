from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView, UserProfileView, ChangePasswordView,
    UpdateProfileView, UpdateExtendedProfileView, UserInterestViewSet,
    # Career Discovery
    CareerDiscoveryQuestionsView, CareerDiscoverySubmitView, 
    CareerDiscoverySelectView,
    # Onboarding
    OnboardingStatusView, OnboardingStep2View, OnboardingStep3View,
    OnboardingStep4View, OnboardingStep5View, CompleteOnboardingView
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
    
    # Career Discovery for Beginners
    path('career-discovery/questions/', CareerDiscoveryQuestionsView.as_view(), name='career-discovery-questions'),
    path('career-discovery/submit/', CareerDiscoverySubmitView.as_view(), name='career-discovery-submit'),
    path('career-discovery/select/', CareerDiscoverySelectView.as_view(), name='career-discovery-select'),
    
    # Onboarding
    path('onboarding/status/', OnboardingStatusView.as_view(), name='onboarding-status'),
    path('onboarding/step2/', OnboardingStep2View.as_view(), name='onboarding-step2'),
    path('onboarding/step3/', OnboardingStep3View.as_view(), name='onboarding-step3'),
    path('onboarding/step4/', OnboardingStep4View.as_view(), name='onboarding-step4'),
    path('onboarding/step5/', OnboardingStep5View.as_view(), name='onboarding-step5'),
    path('onboarding/complete/', CompleteOnboardingView.as_view(), name='onboarding-complete'),

    # User interests
    path('', include(router.urls)),
]