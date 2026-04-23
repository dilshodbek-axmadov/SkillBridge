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

from django.conf import settings as django_settings

from apps.cv.models import CV
from apps.cv.services.cv_export import CVExportService
from apps.jobs.models import JobPosting
from apps.payments.recruiter_access import (
    can_post_job,
    can_view_analytics,
    get_developer_visibility_limit,
    get_recruiter_access_state,
)
from apps.payments.services import (
    create_pro_subscription_checkout_session,
    verify_and_sync_pro_subscription,
)
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
        # Staff may access recruiter tools to test the product without switching accounts.
        if request.user.is_staff:
            return None
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
                'access': get_recruiter_access_state(request.user),
            }
        )


class RecruiterAccessStateView(RecruiterOnlyMixin, APIView):
    """
    GET /api/v1/recruiters/access/

    Single source of truth for the frontend to render plan-gated UI state.
    """

    def get(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied
        return Response(get_recruiter_access_state(request.user))


class RecruiterProSubscribeView(RecruiterOnlyMixin, APIView):
    """
    POST /api/v1/recruiters/subscribe/

    Initiates a Stripe Checkout session for Recruiter Pro. Returns a URL the
    frontend redirects to; after Stripe success, the subscription webhook sets
    User.recruiter_plan = PRO and access-state endpoints immediately unlock.
    """

    def post(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        if request.user.is_recruiter_pro:
            return Response(
                {'error': 'You are already on Recruiter Pro.', 'code': 'already_pro'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        frontend_url = getattr(django_settings, 'FRONTEND_URL', '').rstrip('/')
        success_url = f"{frontend_url}/payment/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{frontend_url}/payment/subscription/failure"

        try:
            checkout_url = create_pro_subscription_checkout_session(
                user=request.user,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except ValueError as e:
            return Response(
                {'error': str(e), 'code': 'subscription_not_configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {'error': f'Could not start checkout: {e}', 'code': 'stripe_error'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'checkout_url': checkout_url}, status=status.HTTP_200_OK)


class RecruiterProSubscribeVerifyView(RecruiterOnlyMixin, APIView):
    """
    POST /api/v1/recruiters/subscribe/verify/

    Called by the frontend success page after Stripe redirects back with
    ?session_id=cs_test_xxx. We retrieve the session from Stripe, validate
    it belongs to this user and was paid, then upsert the Subscription row
    and flip User.recruiter_plan to PRO server-side.

    This is webhook-independent; it guarantees access unlocks instantly
    even when Stripe CLI isn't forwarding events locally.
    """

    def post(self, request):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        session_id = (request.data.get('session_id') or '').strip()
        if not session_id:
            return Response(
                {'error': 'session_id is required.', 'code': 'missing_session_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = verify_and_sync_pro_subscription(user=request.user, session_id=session_id)
        except Exception as e:
            # Don't 500: the plan may have been flipped before the error.
            # Tell the frontend what the current access state is.
            import traceback as _tb
            _tb.print_exc()
            return Response(
                {
                    'error': f'Verification hit an error but your plan state was refreshed: {e}',
                    'code': 'verify_partial',
                    'is_pro': request.user.is_recruiter_pro,
                    'access': get_recruiter_access_state(request.user),
                },
                status=status.HTTP_200_OK,
            )
        if not result['ok']:
            return Response(
                {'error': result['reason'] or 'Could not verify subscription.', 'code': 'verify_failed'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                'is_pro': result['is_pro'],
                'access': get_recruiter_access_state(request.user),
            },
            status=status.HTTP_200_OK,
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
        access = can_view_analytics(request.user)
        if not access['allowed']:
            return Response(
                {
                    'error': access['reason'],
                    'code': access['code'],
                    'plan': access['plan'],
                    'upgrade_required': True,
                    'unlock': {
                        'target': 'recruiter_pro',
                        'feature': 'analytics',
                    },
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

        # Plan-based visibility cap: free recruiters see at most N results total.
        visibility_limit = get_developer_visibility_limit(request.user)
        visible_total = total if visibility_limit is None else min(total, visibility_limit)

        effective_limit = limit
        effective_offset = offset
        if visibility_limit is not None:
            # Clamp offset+limit to the visibility window.
            if effective_offset >= visibility_limit:
                effective_offset = visibility_limit
                effective_limit = 0
            else:
                effective_limit = min(limit, visibility_limit - effective_offset)

        rows = qs[effective_offset : effective_offset + effective_limit] if effective_limit > 0 else qs.none()
        data = CandidateCardSerializer(rows, many=True).data

        # Mark if saved by this recruiter
        saved_ids = set(
            SavedCandidate.objects.filter(recruiter=request.user, candidate_id__in=[c['id'] for c in data]).values_list(
                'candidate_id', flat=True
            )
        )
        for row in data:
            row['is_saved'] = row['id'] in saved_ids

        return Response({
            'total': visible_total,
            'total_unfiltered': total,
            'limit': effective_limit,
            'offset': effective_offset,
            'candidates': data,
            'access': {
                'plan': 'pro' if request.user.is_recruiter_pro or request.user.is_staff else 'free',
                'developer_visibility_limit': visibility_limit,
                'truncated': visibility_limit is not None and total > visibility_limit,
                'upgrade_required': visibility_limit is not None and total > visibility_limit,
            },
        })


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
        contact_unlocked = request.user.is_recruiter_pro or request.user.is_staff
        data['contact_unlocked'] = contact_unlocked
        if not contact_unlocked:
            data['email'] = None
            data['phone'] = None
        return Response(data)


class CandidateCVDownloadView(RecruiterOnlyMixin, APIView):
    """
    GET /api/v1/recruiters/candidates/{candidate_id}/cv/download/?format=pdf|docx

    Recruiter Pro feature: download candidate CV export (default CV).
    """

    def get(self, request, candidate_id):
        denied = self._ensure_recruiter(request)
        if denied:
            return denied

        if not request.user.is_recruiter_pro and not request.user.is_staff:
            return Response(
                {
                    'error': 'CV download is available on SkillBridge Recruiter Pro.',
                    'code': 'pro_required',
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        export_format = (request.query_params.get('format') or 'pdf').strip().lower()
        if export_format not in ('pdf', 'docx'):
            return Response({'error': 'format must be pdf or docx'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            requested_cv_id = int(request.query_params.get('cv_id')) if request.query_params.get('cv_id') else None
        except (TypeError, ValueError):
            return Response({'error': 'cv_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        candidate = (
            User.objects.select_related('profile')
            .filter(
                id=candidate_id,
                user_type=User.UserType.DEVELOPER,
                profile__open_to_recruiters=True,
            )
            .first()
        )
        if not candidate:
            return Response(
                {'error': 'Candidate not found or not visible to recruiters.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        cv_qs = CV.objects.prefetch_related('cv_sections').filter(user_id=candidate.id)
        if requested_cv_id is not None:
            cv = cv_qs.filter(cv_id=requested_cv_id).first()
        else:
            cv = cv_qs.order_by('-is_default', '-updated_at').first()

        if not cv:
            # Fallback: some users upload a raw CV file without creating a CV model record.
            p = getattr(candidate, 'profile', None)
            uploaded = getattr(p, 'cv_file_path', None) if p else None
            if uploaded and getattr(uploaded, 'name', None):
                from django.http import FileResponse
                import mimetypes
                import os

                try:
                    file_path = uploaded.path
                    filename = os.path.basename(uploaded.name)
                    content_type, _ = mimetypes.guess_type(filename)
                    resp = FileResponse(open(file_path, 'rb'), content_type=content_type or 'application/octet-stream')
                    resp['Content-Disposition'] = f'attachment; filename=\"{filename}\"'
                    return resp
                except FileNotFoundError:
                    return Response(
                        {'error': 'Candidate CV file record exists, but file is missing on server.'},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                except Exception:
                    return Response(
                        {'error': 'Could not open candidate CV file.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            return Response(
                {
                    'error': 'Candidate has no CV.',
                    'cv_count': cv_qs.count(),
                    'has_uploaded_cv_file': bool(uploaded and getattr(uploaded, 'name', None)),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        export_service = CVExportService(cv)
        if export_format == 'pdf':
            buffer = export_service.export_pdf()
            content_type = 'application/pdf'
            filename = f"{cv.title.replace(' ', '_')}.pdf"
        else:
            buffer = export_service.export_docx()
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f"{cv.title.replace(' ', '_')}.docx"

        from django.http import HttpResponse

        resp = HttpResponse(buffer.getvalue(), content_type=content_type)
        resp['Content-Disposition'] = f'attachment; filename=\"{filename}\"'
        return resp


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

        # Subscription/plan gating (Free: 1 job per 30d; Pro: unlimited).
        access = can_post_job(request.user)
        if not access['allowed']:
            return Response(
                {
                    'error': access['reason'],
                    'code': access['code'],
                    'plan': access['plan'],
                    'used': access['used'],
                    'limit': access['limit'],
                    'remaining': access['remaining'],
                    'window_days': access['window_days'],
                    'upgrade_required': True,
                    'unlock': {
                        'target': 'recruiter_pro',
                        'feature': 'job_post',
                    },
                },
                status=status.HTTP_403_FORBIDDEN,
            )

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

