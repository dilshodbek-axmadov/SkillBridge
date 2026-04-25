"""
Users App Views - Part 1: Authentication

API endpoints for user authentication.
"""

import secrets

import requests
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string

from .models import User, UserProfile, UserActivity
from .activity_log import log_user_activity
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    UserProfileSerializer
)


class RegisterView(APIView):
    """
    User registration endpoint.
    
    POST /api/auth/register/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()

            home_path = (
                '/recruiter/dashboard'
                if user.user_type == User.UserType.RECRUITER
                else '/dashboard'
            )
            log_user_activity(
                user,
                UserActivity.ActivityType.ACCOUNT_CREATED,
                'Welcome! Your SkillBridge account is ready.',
                link_path=home_path,
            )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Send welcome email (optional)
            self._send_welcome_email(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def _send_welcome_email(self, user):
        """Send welcome email to new user."""
        try:
            subject = 'Welcome to SkillBridge!'
            message = render_to_string('emails/welcome.html', {
                'user': user,
                'site_name': 'SkillBridge'
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send welcome email: {e}")


class LoginView(APIView):
    """
    User login endpoint.
    
    POST /api/auth/login/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Update last login
            from django.utils import timezone
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    """
    User logout endpoint (blacklist refresh token).
    
    POST /api/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Logout successful'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class GoogleAuthView(APIView):
    """
    Sign in / sign up with Google.

    POST /api/v1/users/auth/google/
    body: {
        "access_token": "<Google OAuth 2.0 access token from GIS>",
        "user_type": "developer" | "recruiter"   # optional, only used on new sign-up
    }

    We verify the access token by calling Google's userinfo endpoint over HTTPS;
    a 200 response from accounts.google.com / googleapis.com is proof that the
    token is valid and Google has verified the email.

    Behaviour:
      - Existing user (matched by email): log them in. user_type is NOT changed.
      - New user: create account with a random unusable-style password, set
        user_type from the request (default: developer), create blank profile.
    Returns the same shape as the regular /login/ endpoint.
    """

    permission_classes = [permissions.AllowAny]

    USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

    def post(self, request):
        access_token = (request.data.get('access_token') or '').strip()
        if not access_token:
            return Response(
                {'error': 'access_token is required.', 'code': 'missing_access_token'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resp = requests.get(
                self.USERINFO_URL,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
        except requests.RequestException as e:
            return Response(
                {'error': f'Could not reach Google: {e}', 'code': 'google_unreachable'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if resp.status_code != 200:
            return Response(
                {'error': 'Invalid Google access token.', 'code': 'invalid_google_token'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        info = resp.json() or {}
        email = (info.get('email') or '').strip().lower()
        email_verified = info.get('email_verified') in (True, 'true', 'True', 1)
        google_sub = info.get('sub')
        given_name = info.get('given_name') or ''
        family_name = info.get('family_name') or ''

        if not email or not google_sub:
            return Response(
                {'error': 'Google did not return an email.', 'code': 'google_no_email'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not email_verified:
            return Response(
                {
                    'error': 'Your Google email is not verified. Please verify it with Google first.',
                    'code': 'google_email_unverified',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        requested_type = (request.data.get('user_type') or '').strip()
        if requested_type not in (User.UserType.DEVELOPER, User.UserType.RECRUITER):
            requested_type = User.UserType.DEVELOPER

        created = False
        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                username = self._pick_unique_username(email)
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=secrets.token_urlsafe(32),
                    first_name=given_name,
                    last_name=family_name,
                    user_type=requested_type,
                    recruiter_plan=User.RecruiterPlan.FREE,
                )
                UserProfile.objects.get_or_create(user=user)
                created = True

                home_path = (
                    '/recruiter/dashboard'
                    if user.user_type == User.UserType.RECRUITER
                    else '/dashboard'
                )
                log_user_activity(
                    user,
                    UserActivity.ActivityType.ACCOUNT_CREATED,
                    'Welcome! Your SkillBridge account is ready.',
                    link_path=home_path,
                )
            else:
                UserProfile.objects.get_or_create(user=user)

        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'message': 'Signed up with Google.' if created else 'Logged in with Google.',
                'created': created,
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @staticmethod
    def _pick_unique_username(email):
        base = (email.split('@')[0] or 'user').lower()
        base = ''.join(ch for ch in base if ch.isalnum() or ch in '._-')[:24] or 'user'
        candidate = base
        suffix = 0
        while User.objects.filter(username=candidate).exists():
            suffix += 1
            candidate = f'{base}{suffix}'
            if suffix > 9999:
                candidate = f'{base}{secrets.token_hex(3)}'
                break
        return candidate


class PasswordResetRequestView(APIView):
    """
    Request password reset email.
    
    POST /api/auth/password-reset/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Send reset email
            self._send_reset_email(user, reset_link)
            
            return Response({
                'message': 'Password reset email sent',
                'detail': 'Check your email for reset instructions'
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def _send_reset_email(self, user, reset_link):
        """Send password reset email."""
        subject = 'Reset Your SkillBridge Password'
        message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_link': reset_link,
            'site_name': 'SkillBridge'
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    
    POST /api/auth/password-reset/confirm/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            # Extract UID and token from request
            uid = request.data.get('uid')
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                # Decode user ID
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
                
                # Verify token
                if default_token_generator.check_token(user, token):
                    # Set new password
                    user.set_password(new_password)
                    user.save()
                    
                    return Response({
                        'message': 'Password reset successful',
                        'detail': 'You can now login with your new password'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'error': 'Invalid or expired token'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {'error': 'Invalid reset link'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class CurrentUserView(APIView):
    """
    Get current authenticated user details.
    
    GET /api/auth/me/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_serializer = UserSerializer(request.user)
        
        try:
            profile_serializer = UserProfileSerializer(request.user.profile)
            
            return Response({
                'user': user_serializer.data,
                'profile': profile_serializer.data
            }, status=status.HTTP_200_OK)
        
        except UserProfile.DoesNotExist:
            # Create profile if doesn't exist
            profile = UserProfile.objects.create(user=request.user)
            profile_serializer = UserProfileSerializer(profile)

            return Response({
                'user': user_serializer.data,
                'profile': profile_serializer.data
            }, status=status.HTTP_200_OK)


class UpdateUserView(APIView):
    """
    Update current user's basic info.

    PATCH /api/auth/update/
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        allowed = ['first_name', 'last_name', 'phone', 'preferred_language']
        updated = []

        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])
                updated.append(field)

        if not updated:
            return Response(
                {'error': 'No valid fields provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.save(update_fields=updated + ['updated_at'])
        return Response({
            'message': 'User updated successfully',
            'user': UserSerializer(user).data
        })


class ChangePasswordView(APIView):
    """
    Change password for authenticated user.

    POST /api/auth/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'current_password': ['Current password is incorrect.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({'message': 'Password changed successfully'})


class DeleteAccountView(APIView):
    """
    Delete the current user's account.

    POST /api/auth/delete-account/
    Requires password confirmation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        password = request.data.get('password', '')
        if not password:
            return Response(
                {'error': 'Password is required to delete account'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(password):
            return Response(
                {'error': 'Incorrect password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.delete()
        return Response({'message': 'Account deleted successfully'})


class ExportUserDataView(APIView):
    """
    Export all user data as JSON.

    GET /api/auth/export-data/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        from apps.skills.models import UserSkill

        try:
            profile = user.profile
            profile_data = {
                'current_job_position': profile.current_job_position,
                'desired_role': profile.desired_role,
                'experience_level': profile.experience_level,
                'bio': profile.bio,
                'location': profile.location,
                'profile_source': profile.profile_source,
                'github_url': profile.github_url,
                'linkedin_url': profile.linkedin_url,
                'portfolio_url': profile.portfolio_url,
                'created_at': str(profile.created_at),
                'updated_at': str(profile.updated_at),
            }
        except UserProfile.DoesNotExist:
            profile_data = None

        skills = list(
            UserSkill.objects.filter(user=user)
            .select_related('skill')
            .values(
                'skill__name_en', 'proficiency_level',
                'years_of_experience', 'is_primary', 'source'
            )
        )

        return Response({
            'user': {
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'preferred_language': user.preferred_language,
                'created_at': str(user.created_at),
            },
            'profile': profile_data,
            'skills': skills,
        })