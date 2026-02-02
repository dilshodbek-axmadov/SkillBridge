"""
Users App URLs
==============
backend/apps/users/urls.py

URL routing for user authentication and profile management.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    CurrentUserView
)
from .views_profile import (
    UserProfileView,
    QuestionnaireProfileView,
    CVUploadView,
    UserSkillsView,
    AddUserSkillsView,
    UpdateUserSkillView,
    DeleteUserSkillView
)

app_name = 'users'

urlpatterns = [
    # ==================== AUTHENTICATION ====================
    
    # User registration & login
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # JWT token refresh
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password reset
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Current user
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),
    
    # ==================== PROFILE MANAGEMENT ====================
    
    # Profile CRUD
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # Profile creation methods
    path('profile/questionnaire/', QuestionnaireProfileView.as_view(), name='profile_questionnaire'),
    path('profile/cv-upload/', CVUploadView.as_view(), name='cv_upload'),
    
    # ==================== SKILLS MANAGEMENT ====================
    
    # User skills
    path('profile/skills/', UserSkillsView.as_view(), name='user_skills'),
    path('profile/skills/add/', AddUserSkillsView.as_view(), name='add_skills'),
    path('profile/skills/<int:skill_id>/', UpdateUserSkillView.as_view(), name='update_skill'),
    path('profile/skills/<int:skill_id>/delete/', DeleteUserSkillView.as_view(), name='delete_skill'),
]