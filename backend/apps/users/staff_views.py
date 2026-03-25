"""
In-app admin console API (staff users only).
Superusers may additionally toggle is_staff / is_superuser on accounts.
"""

from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.jobs.models import JobPosting

from .models import User
from .staff_serializers import StaffUserListSerializer, StaffUserUpdateSerializer


class StaffOverviewView(APIView):
    """
    GET /api/v1/users/staff/overview/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        users_qs = User.objects.all()
        return Response(
            {
                'users': {
                    'total': users_qs.count(),
                    'developers': users_qs.filter(user_type=User.UserType.DEVELOPER).count(),
                    'recruiters': users_qs.filter(user_type=User.UserType.RECRUITER).count(),
                    'recruiter_pro': users_qs.filter(
                        user_type=User.UserType.RECRUITER,
                        recruiter_plan=User.RecruiterPlan.PRO,
                    ).count(),
                    'staff': users_qs.filter(is_staff=True).count(),
                },
                'jobs': {
                    'total': JobPosting.objects.count(),
                    'listing_active': JobPosting.objects.filter(
                        listing_status=JobPosting.ListingStatus.ACTIVE
                    ).count(),
                },
            }
        )


class StaffUserListView(APIView):
    """
    GET /api/v1/users/staff/users/
    Query: q, page, page_size, user_type, recruiter_plan
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            page = max(int(request.query_params.get('page', 1)), 1)
            page_size = min(max(int(request.query_params.get('page_size', 25)), 1), 100)
        except ValueError:
            return Response({'error': 'Invalid pagination'}, status=status.HTTP_400_BAD_REQUEST)

        qs = User.objects.all().order_by('-created_at')

        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(email__icontains=q)
                | Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )

        ut = request.query_params.get('user_type', '').strip()
        if ut in dict(User.UserType.choices):
            qs = qs.filter(user_type=ut)

        rp = request.query_params.get('recruiter_plan', '').strip()
        if rp in dict(User.RecruiterPlan.choices):
            qs = qs.filter(recruiter_plan=rp)

        total = qs.count()
        offset = (page - 1) * page_size
        rows = qs[offset : offset + page_size]

        return Response(
            {
                'count': total,
                'page': page,
                'page_size': page_size,
                'results': StaffUserListSerializer(rows, many=True).data,
            }
        )


class StaffUserDetailView(APIView):
    """
    GET/PATCH /api/v1/users/staff/users/<user_id>/
    """

    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StaffUserListSerializer(user).data)

    def patch(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if user_id == request.user.id and request.user.is_superuser:
            # Superuser editing self — block stripping own superuser in validate below
            pass

        serializer = StaffUserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if ('is_staff' in data or 'is_superuser' in data) and not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can change staff flags.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user_id == request.user.id:
            if data.get('is_superuser') is False or data.get('is_staff') is False:
                return Response(
                    {'error': 'You cannot remove your own staff or superuser access here.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        for field in ('recruiter_plan', 'user_type', 'is_active', 'is_staff', 'is_superuser'):
            if field in data:
                setattr(user, field, data[field])

        user.save()
        return Response(StaffUserListSerializer(user).data)


class StaffPlatformSettingsView(APIView):
    """
    GET /api/v1/users/staff/settings/
    Safe, non-secret platform hints for the in-app admin panel.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(
            {
                'platform': {
                    'debug': settings.DEBUG,
                    'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
                    'allowed_hosts_preview': list(getattr(settings, 'ALLOWED_HOSTS', [])[:8]),
                    'django_admin_path': '/admin/',
                },
            }
        )
