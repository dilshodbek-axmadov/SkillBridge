"""
Recruiter API views.
"""

import uuid

from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.jobs.models import JobPosting
from apps.recruiters.analytics import get_recruiter_analytics
from apps.recruiters.models import RecruiterSavedSearch, SavedCandidate
from apps.recruiters.serializers import (
    CandidateCardSerializer,
    CandidateProfileDetailSerializer,
    RecruiterJobPostingSerializer,
    RecruiterSavedSearchSerializer,
    SavedCandidateSerializer,
)
from apps.users.models import User


class RecruiterOnlyMixin:
    permission_classes = [IsAuthenticated]

    def _ensure_recruiter(self, request):
        if not request.user.is_recruiter_account:
            return Response({'error': 'Recruiter account required.'}, status=status.HTTP_403_FORBIDDEN)
        return None


class RecruiterDashboardView(RecruiterOnlyMixin, APIView):
    """
    GET /api/v1/recruiters/dashboard/
    """

    def get(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        candidates_saved = SavedCandidate.objects.filter(recruiter=request.user).count()
        jobs_posted = JobPosting.objects.filter(posted_by=request.user).count()
        active_jobs = JobPosting.objects.filter(posted_by=request.user, is_active=True).count()

        return Response(
            {
                'stats': {
                    'candidates_saved': candidates_saved,
                    'jobs_posted': jobs_posted,
                    'active_jobs': active_jobs,
                },
                'subscription': {
                    'plan': request.user.recruiter_plan,
                    'is_pro': request.user.is_recruiter_pro,
                },
            }
        )


class RecruiterAnalyticsView(RecruiterOnlyMixin, APIView):
    """
    GET /api/v1/recruiters/analytics/

    SkillBridge Recruiter Pro — market and workspace metrics.
    """

    def get(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        if not request.user.is_recruiter_pro:
            return Response(
                {
                    'error': 'Analytics are available on SkillBridge Recruiter Pro.',
                    'code': 'pro_required',
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            {
                'subscription': {
                    'plan': request.user.recruiter_plan,
                    'is_pro': True,
                },
                **get_recruiter_analytics(request.user),
            }
        )


class CandidateListView(RecruiterOnlyMixin, APIView):
    """
    GET /api/v1/recruiters/candidates/
    """

    def get(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        q = request.query_params.get('q', '').strip()
        location = request.query_params.get('location', '').strip()
        experience_level = request.query_params.get('experience_level', '').strip()
        skill = request.query_params.get('skill', '').strip()
        sort = request.query_params.get('sort', 'newest')
        try:
            limit = min(int(request.query_params.get('limit', 20)), 100)
            offset = max(int(request.query_params.get('offset', 0)), 0)
        except ValueError:
            return Response({'error': 'limit/offset must be integers'}, status=status.HTTP_400_BAD_REQUEST)

        qs = (
            User.objects.filter(
                user_type=User.UserType.DEVELOPER,
                profile__open_to_recruiters=True,
            )
            .select_related('profile')
            .distinct()
        )

        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(profile__current_job_position__icontains=q)
                | Q(profile__desired_role__icontains=q)
            )
        if location:
            qs = qs.filter(profile__location__icontains=location)
        if experience_level:
            qs = qs.filter(profile__experience_level=experience_level)
        if skill:
            qs = qs.filter(skills__skill__name_en__icontains=skill)

        if sort == 'profile_updated':
            qs = qs.order_by('-profile__updated_at')
        else:
            qs = qs.order_by('-created_at')

        total = qs.count()
        rows = qs[offset : offset + limit]
        data = CandidateCardSerializer(rows, many=True).data

        # Mark if saved by this recruiter
        saved_ids = set(
            SavedCandidate.objects.filter(recruiter=request.user, candidate_id__in=[c['id'] for c in data]).values_list(
                'candidate_id', flat=True
            )
        )
        for row in data:
            row['is_saved'] = row['id'] in saved_ids

        return Response({'total': total, 'limit': limit, 'offset': offset, 'candidates': data})


class CandidateDetailView(RecruiterOnlyMixin, APIView):
    """
    GET /api/v1/recruiters/candidates/{candidate_id}/
    """

    def get(self, request, candidate_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        candidate = get_object_or_404(
            User.objects.select_related('profile'),
            id=candidate_id,
            user_type=User.UserType.DEVELOPER,
            profile__open_to_recruiters=True,
        )
        data = CandidateProfileDetailSerializer(candidate).data
        data['contact_unlocked'] = request.user.is_recruiter_pro
        if not request.user.is_recruiter_pro:
            data['email'] = None
            data['phone'] = None
        return Response(data)


class SavedCandidateListCreateView(RecruiterOnlyMixin, APIView):
    """
    GET/POST /api/v1/recruiters/saved-candidates/
    """

    def get(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        rows = SavedCandidate.objects.filter(recruiter=request.user).select_related('candidate', 'candidate__profile')
        return Response({'count': rows.count(), 'saved_candidates': SavedCandidateSerializer(rows, many=True).data})

    def post(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        serializer = SavedCandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate_id = serializer.validated_data['candidate_id']
        if candidate_id == request.user.id:
            return Response({'error': 'Cannot save yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        candidate = get_object_or_404(
            User.objects.select_related('profile'),
            id=candidate_id,
            user_type=User.UserType.DEVELOPER,
            profile__open_to_recruiters=True,
        )
        obj, created = SavedCandidate.objects.get_or_create(
            recruiter=request.user,
            candidate=candidate,
            defaults={'notes': serializer.validated_data.get('notes', '')},
        )
        if not created and 'notes' in serializer.validated_data:
            obj.notes = serializer.validated_data['notes']
            obj.save(update_fields=['notes', 'updated_at'])
        out = SavedCandidateSerializer(obj).data
        return Response(out, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class SavedCandidateDetailView(RecruiterOnlyMixin, APIView):
    """
    PATCH/DELETE /api/v1/recruiters/saved-candidates/{saved_id}/
    """

    def patch(self, request, saved_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        obj = get_object_or_404(SavedCandidate, saved_id=saved_id, recruiter=request.user)
        notes = request.data.get('notes', '')
        obj.notes = notes
        obj.save(update_fields=['notes', 'updated_at'])
        return Response(SavedCandidateSerializer(obj).data)

    def delete(self, request, saved_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        obj = get_object_or_404(SavedCandidate, saved_id=saved_id, recruiter=request.user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SavedSearchListCreateView(RecruiterOnlyMixin, APIView):
    """
    GET/POST /api/v1/recruiters/saved-searches/
    """

    def get(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        rows = RecruiterSavedSearch.objects.filter(recruiter=request.user)
        return Response({'count': rows.count(), 'saved_searches': RecruiterSavedSearchSerializer(rows, many=True).data})

    def post(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        serializer = RecruiterSavedSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = RecruiterSavedSearch.objects.create(
            recruiter=request.user,
            name=serializer.validated_data['name'],
            filters=serializer.validated_data.get('filters', {}),
        )
        return Response(RecruiterSavedSearchSerializer(obj).data, status=status.HTTP_201_CREATED)


class SavedSearchDetailView(RecruiterOnlyMixin, APIView):
    """
    PATCH/DELETE /api/v1/recruiters/saved-searches/{search_id}/
    """

    def patch(self, request, search_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        obj = get_object_or_404(RecruiterSavedSearch, search_id=search_id, recruiter=request.user)
        serializer = RecruiterSavedSearchSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, search_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        obj = get_object_or_404(RecruiterSavedSearch, search_id=search_id, recruiter=request.user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecruiterJobListCreateView(RecruiterOnlyMixin, APIView):
    """
    GET/POST /api/v1/recruiters/jobs/
    """

    def get(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        rows = (
            JobPosting.objects.filter(posted_by=request.user)
            .annotate(application_count=Count('applications', distinct=True))
            .order_by('-posted_date')
        )
        return Response({'count': rows.count(), 'jobs': RecruiterJobPostingSerializer(rows, many=True).data})

    def post(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        serializer = RecruiterJobPostingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        listing_status = data.get('listing_status', JobPosting.ListingStatus.DRAFT)
        if listing_status not in dict(JobPosting.ListingStatus.choices):
            listing_status = JobPosting.ListingStatus.DRAFT
        is_active = listing_status == JobPosting.ListingStatus.ACTIVE
        create_kwargs = {k: v for k, v in data.items() if k not in {'posted_date', 'is_active', 'listing_status'}}
        create_kwargs.setdefault('job_url', '')
        obj = JobPosting.objects.create(
            external_job_id=f"platform-{uuid.uuid4().hex[:20]}",
            source='platform',
            posted_by=request.user,
            original_language=request.user.preferred_language or 'en',
            posted_date=data.get('posted_date') or timezone.now(),
            is_active=is_active,
            listing_status=listing_status,
            **create_kwargs,
        )
        return Response(RecruiterJobPostingSerializer(obj).data, status=status.HTTP_201_CREATED)


class RecruiterJobDetailView(RecruiterOnlyMixin, APIView):
    """
    GET/PATCH/DELETE /api/v1/recruiters/jobs/{job_id}/
    """

    def get_object(self, request, job_id):
        return get_object_or_404(JobPosting, job_id=job_id, posted_by=request.user)

    def get(self, request, job_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        obj = (
            JobPosting.objects.filter(job_id=job_id, posted_by=request.user)
            .annotate(application_count=Count('applications', distinct=True))
            .first()
        )
        if not obj:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RecruiterJobPostingSerializer(obj).data)

    def patch(self, request, job_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        obj = self.get_object(request, job_id)
        serializer = RecruiterJobPostingSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, job_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        obj = self.get_object(request, job_id)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

