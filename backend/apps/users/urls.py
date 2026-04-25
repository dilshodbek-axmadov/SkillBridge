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
    GoogleAuthView,
    PasswordResetOTPRequestView,
    PasswordResetOTPConfirmView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    CurrentUserView,
    UpdateUserView,
    ChangePasswordView,
    DeleteAccountView,
    ExportUserDataView,
)
from .staff_views import (
    StaffOverviewView,
    StaffUserListView,
    StaffUserDetailView,
    StaffPlatformSettingsView,
)
from .views_profile import (
    UserProfileView,
    CVUploadView
)
from .views_profile import (
    # Skills browsing
    GetAllSkillsView,
    SearchSkillsView,
    GetSkillCategoriesView,
    
    # Profile creation
    CreateManualProfileView,
    GetProfileSummaryView,
    
    # Skills management
    GetMySkillsView,
    AddSkillView,
    BulkAddSkillsView,
    UpdateSkillView,
    DeleteSkillView,
    
    # Quick updates
    UpdateJobPositionView,
    UpdateExperienceLevelView,
    UserActivityListView,
)

app_name = 'users'

urlpatterns = [
    # ==================== AUTHENTICATION ====================
    
    # User registration & login
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/password-reset-otp/', PasswordResetOTPRequestView.as_view(), name='password_reset_otp'),
    path('auth/password-reset-otp/confirm/', PasswordResetOTPConfirmView.as_view(), name='password_reset_otp_confirm'),
    
    # JWT token refresh
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password reset
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Current user
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),
    path('auth/update/', UpdateUserView.as_view(), name='update_user'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('auth/export-data/', ExportUserDataView.as_view(), name='export_data'),
    
    # ==================== PROFILE MANAGEMENT ====================
    
    # Profile CRUD
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # CV upload profile creation
    path('profile/cv-upload/', CVUploadView.as_view(), name='cv_upload'),

    # ===== MANUAL PROFILE CREATION =====
    path('profile/create-manual/', CreateManualProfileView.as_view(), name='create_manual'),
    path('profile/summary/', GetProfileSummaryView.as_view(), name='profile_summary'),

    # ==================== Skills Management =====================

    # ===== SKILLS BROWSING =====
    path('skills/browse/', GetAllSkillsView.as_view(), name='browse_skills'),
    path('skills/search/', SearchSkillsView.as_view(), name='search_skills'),
    path('skills/categories/', GetSkillCategoriesView.as_view(), name='skill_categories'),
    
    # ===== USER SKILLS MANAGEMENT (CRUD) =====
    path('profile/my-skills/', GetMySkillsView.as_view(), name='my_skills'),
    path('profile/skills/add/', AddSkillView.as_view(), name='add_skill'),
    path('profile/skills/bulk-add/', BulkAddSkillsView.as_view(), name='bulk_add_skills'),
    path('profile/skills/update/<int:user_skill_id>/', UpdateSkillView.as_view(), name='update_skill'),
    path('profile/skills/delete/<int:user_skill_id>/', DeleteSkillView.as_view(), name='delete_skill'),
    
    # ===== QUICK UPDATES =====
    path('profile/update-position/', UpdateJobPositionView.as_view(), name='update_position'),
    path('profile/update-experience/', UpdateExperienceLevelView.as_view(), name='update_experience'),

    path('profile/activity/', UserActivityListView.as_view(), name='user_activity'),

    # ==================== Staff / in-app admin ====================
    path('staff/overview/', StaffOverviewView.as_view(), name='staff_overview'),
    path('staff/users/', StaffUserListView.as_view(), name='staff_user_list'),
    path('staff/users/<int:user_id>/', StaffUserDetailView.as_view(), name='staff_user_detail'),
    path('staff/settings/', StaffPlatformSettingsView.as_view(), name='staff_platform_settings'),
]