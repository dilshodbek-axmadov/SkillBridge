"""
CV App Views
============
API views for CV creation, management, auto-populate, and export.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse

from apps.cv.models import CV
from apps.cv.services.cv_service import CVService
from apps.cv.services.cv_export import CVExportService
from apps.cv.serializers import (
    CVListSerializer,
    CVDetailSerializer,
    CreateCVRequestSerializer,
    AutoPopulateRequestSerializer,
    UpdateSectionsRequestSerializer,
    SwitchTemplateRequestSerializer,
    ExportCVRequestSerializer,
)


def _build_export_response(cv, export_format):
    """Build file download response for a CV export request."""
    export_service = CVExportService(cv)

    if export_format == 'pdf':
        buffer = export_service.export_pdf()
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf',
        )
        filename = f"{cv.title.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    buffer = export_service.export_docx()
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    filename = f"{cv.title.replace(' ', '_')}.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class CreateCVView(APIView):
    """
    POST /api/v1/cv/create/

    Create a new CV manually with optional sections.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateCVRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = CVService(user=request.user)
        cv = service.create_cv(
            title=serializer.validated_data['title'],
            template_type=serializer.validated_data.get('template_type', 'modern'),
            language_code=serializer.validated_data.get('language_code', 'en'),
            is_default=serializer.validated_data.get('is_default', False),
            sections=serializer.validated_data.get('sections'),
        )

        return Response(
            CVDetailSerializer(cv).data,
            status=status.HTTP_201_CREATED,
        )


class CVDetailView(APIView):
    """
    GET /api/v1/cv/{cv_id}/
    DELETE /api/v1/cv/{cv_id}/

    Get CV details or delete a CV.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, cv_id):
        # Backward-compatible export fallback via detail route:
        # GET /api/v1/cv/{cv_id}/?download=1&export_format=pdf|docx
        if request.query_params.get('download') in ('1', 'true', 'True'):
            serializer = ExportCVRequestSerializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            export_format = serializer.validated_data.get('export_format', 'pdf')
            try:
                cv = CV.objects.prefetch_related('cv_sections').get(cv_id=cv_id, user=request.user)
            except CV.DoesNotExist:
                return Response(
                    {'error': 'CV not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return _build_export_response(cv, export_format)

        try:
            service = CVService(user=request.user)
            cv = service.get_cv_detail(cv_id)
        except CV.DoesNotExist:
            return Response(
                {'error': 'CV not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CVDetailSerializer(cv).data)

    def delete(self, request, cv_id):
        try:
            service = CVService(user=request.user)
            service.delete_cv(cv_id)
        except CV.DoesNotExist:
            return Response(
                {'error': 'CV not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {'message': 'CV deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT,
        )


class CVListView(APIView):
    """
    GET /api/v1/cv/

    List all CVs for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cvs = CV.objects.filter(user=request.user)
        return Response({
            'count': cvs.count(),
            'cvs': CVListSerializer(cvs, many=True).data,
        })


class UpdateSectionsView(APIView):
    """
    PUT /api/v1/cv/{cv_id}/sections/

    Update CV sections (create, update, or reorder).
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, cv_id):
        serializer = UpdateSectionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = CVService(user=request.user)
            cv = service.update_sections(
                cv_id=cv_id,
                sections_data=serializer.validated_data['sections'],
            )
        except CV.DoesNotExist:
            return Response(
                {'error': 'CV not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CVDetailSerializer(cv).data)


class AutoPopulateView(APIView):
    """
    POST /api/v1/cv/auto-populate/

    Create a new CV auto-populated from user profile data.
    Pulls from: UserProfile, UserSkill, UserProject, completed roadmap items.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AutoPopulateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = CVService(user=request.user)
        cv = service.auto_populate(
            title=serializer.validated_data.get('title'),
            template_type=serializer.validated_data.get('template_type', 'modern'),
            language_code=serializer.validated_data.get('language_code', 'en'),
        )

        return Response(
            CVDetailSerializer(cv).data,
            status=status.HTTP_201_CREATED,
        )


class AutoPopulateExistingView(APIView):
    """
    POST /api/v1/cv/{cv_id}/auto-populate/

    Re-populate an existing CV from profile data.
    Replaces all sections with auto-generated content.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, cv_id):
        try:
            service = CVService(user=request.user)
            cv = service.auto_populate(cv_id=cv_id)
        except CV.DoesNotExist:
            return Response(
                {'error': 'CV not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CVDetailSerializer(cv).data)


class SwitchTemplateView(APIView):
    """
    PUT /api/v1/cv/{cv_id}/template/

    Switch CV template and reorder sections.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, cv_id):
        serializer = SwitchTemplateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = CVService(user=request.user)
            cv = service.switch_template(
                cv_id=cv_id,
                new_template_type=serializer.validated_data['template_type'],
            )
        except CV.DoesNotExist:
            return Response(
                {'error': 'CV not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(CVDetailSerializer(cv).data)


class ExportCVView(APIView):
    """
    GET /api/v1/cv/{cv_id}/export/?format=pdf|docx

    Export CV as PDF or DOCX file for download.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, cv_id):
        serializer = ExportCVRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        export_format = serializer.validated_data.get('export_format', 'pdf')

        try:
            cv = (
                CV.objects.select_related('user', 'user__profile')
                .prefetch_related('cv_sections')
                .get(cv_id=cv_id)
            )
        except CV.DoesNotExist:
            return Response(
                {'error': 'CV not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Owner can always export their own CV.
        if cv.user_id == request.user.id:
            return _build_export_response(cv, export_format)

        # Staff may export any CV for support/testing.
        if request.user.is_staff:
            return _build_export_response(cv, export_format)

        # Recruiter Pro may export CVs of visible developer profiles.
        if request.user.is_recruiter_pro:
            owner = cv.user
            owner_profile = getattr(owner, 'profile', None)
            if owner.is_developer and owner_profile and owner_profile.open_to_recruiters:
                return _build_export_response(cv, export_format)

        # Avoid leaking CV existence.
        return Response({'error': 'CV not found.'}, status=status.HTTP_404_NOT_FOUND)



class TemplateListView(APIView):
    """
    GET /api/v1/cv/templates/

    List available CV templates.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        templates = CVService.get_available_templates()
        return Response({
            'count': len(templates),
            'templates': templates,
        })
