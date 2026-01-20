"""
Views for CV upload, generation, and management
"""
import os
from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from .models import (
    UploadedCV, CVExtractionLog, UserCV, CVSection,
    WorkExperience, Education, Project
)
from .serializers import (
    CVUploadSerializer, UploadedCVSerializer,
    CVExtractionResultSerializer,
    WorkExperienceSerializer, WorkExperienceCreateSerializer,
    EducationSerializer, EducationCreateSerializer,
    ProjectSerializer,
    CVSectionSerializer, CVSectionCreateSerializer,
    UserCVListSerializer, UserCVDetailSerializer,
    UserCVCreateSerializer, UserCVUpdateSerializer,
    AutoGenerateCVSerializer, CVTemplateSerializer,
    CVBuilderProgressSerializer
)
from .services import CVProcessor
from skills.models import Skill, SkillLevel, UserSkill
from users.models import UserProfile
from notifications.models import UserNotification


# CV Upload Views 

class CVUploadView(APIView):
    """
    Upload CV for processing

    POST /api/cvs/upload/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CVUploadSerializer(data=request.data)

        if serializer.is_valid():
            cv_file = serializer.validated_data['cv_file']
            user = request.user

            file_extension = cv_file.name.split('.')[-1].lower()

            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_cvs', str(user.id))
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, cv_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in cv_file.chunks():
                    destination.write(chunk)

            uploaded_cv = UploadedCV.objects.create(
                user=user,
                original_filename=cv_file.name,
                file_path=file_path,
                file_type=file_extension,
                processing_status='pending'
            )

            try:
                uploaded_cv.mark_processing()
                processor = CVProcessor()
                extracted_data = processor.process_cv(file_path, file_extension)
                uploaded_cv.mark_completed(extracted_data)

                CVExtractionLog.objects.create(
                    uploaded_cv=uploaded_cv,
                    skills_extracted_count=extracted_data['skills_count'],
                    confidence_score=extracted_data['confidence_score']
                )

                self._populate_user_profile(user, extracted_data)

                UserNotification.create_notification(
                    user=user,
                    notification_type='cv_generated',
                    title='CV Processed Successfully!',
                    message=f'We extracted {extracted_data["skills_count"]} skills from your CV.',
                    link_url='/profile'
                )

                return Response({
                    'message': 'CV uploaded and processed successfully',
                    'uploaded_cv_id': uploaded_cv.id,
                    'extracted_data': CVExtractionResultSerializer(extracted_data).data,
                    'processing_status': 'completed'
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                uploaded_cv.mark_failed()
                CVExtractionLog.objects.create(
                    uploaded_cv=uploaded_cv,
                    skills_extracted_count=0,
                    confidence_score=0.0,
                    errors_json={'error': str(e)}
                )
                return Response({
                    'error': 'Failed to process CV',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _populate_user_profile(self, user, extracted_data):
        """Populate user profile with extracted CV data"""
        profile, _ = UserProfile.objects.get_or_create(user=user)

        if extracted_data.get('experience_level'):
            profile.experience_level = extracted_data['experience_level']

        if extracted_data.get('job_titles'):
            profile.current_role = extracted_data['job_titles'][0]

        profile.save()

        for skill_name in extracted_data.get('skills', []):
            skill, _ = Skill.objects.get_or_create(
                name__iexact=skill_name,
                defaults={'name': skill_name, 'category': 'other'}
            )
            skill_level = SkillLevel.objects.filter(level_order=2).first()
            UserSkill.objects.get_or_create(
                user=user,
                skill=skill,
                defaults={
                    'level': skill_level,
                    'status': 'learned',
                    'self_assessed': False
                }
            )

        user.onboarding_method = 'cv_upload'
        user.it_knowledge_level = 'experienced'
        user.update_profile_completion()
        user.save(update_fields=['onboarding_method', 'it_knowledge_level'])


class UploadedCVListView(generics.ListAPIView):
    """List all uploaded CVs for current user"""
    permission_classes = [IsAuthenticated]
    serializer_class = UploadedCVSerializer

    def get_queryset(self):
        return UploadedCV.objects.filter(user=self.request.user)


class UploadedCVDetailView(generics.RetrieveAPIView):
    """Get details of a specific uploaded CV"""
    permission_classes = [IsAuthenticated]
    serializer_class = UploadedCVSerializer

    def get_queryset(self):
        return UploadedCV.objects.filter(user=self.request.user)


# User CV ViewSet 

class UserCVViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user CVs

    Endpoints:
    - GET /api/cvs/my-cvs/ - List user's CVs
    - POST /api/cvs/my-cvs/ - Create new CV
    - GET /api/cvs/my-cvs/{id}/ - Get CV details
    - PUT /api/cvs/my-cvs/{id}/ - Update CV
    - DELETE /api/cvs/my-cvs/{id}/ - Delete CV
    - POST /api/cvs/my-cvs/{id}/set-primary/ - Set as primary CV
    - GET /api/cvs/my-cvs/primary/ - Get primary CV
    - POST /api/cvs/my-cvs/{id}/duplicate/ - Duplicate CV
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCV.objects.filter(
            user=self.request.user
        ).prefetch_related('cv_sections').order_by('-is_primary', '-last_updated')

    def get_serializer_class(self):
        if self.action == 'list':
            return UserCVListSerializer
        elif self.action == 'create':
            return UserCVCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserCVUpdateSerializer
        return UserCVDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, pk=None):
        """Set CV as primary"""
        cv = self.get_object()
        cv.set_as_primary()
        return Response({
            'message': 'CV set as primary successfully',
            'cv': UserCVDetailSerializer(cv).data
        })

    @action(detail=False, methods=['get'])
    def primary(self, request):
        """Get user's primary CV"""
        primary_cv = self.get_queryset().filter(is_primary=True).first()
        if not primary_cv:
            return Response({'detail': 'No primary CV found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserCVDetailSerializer(primary_cv).data)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate an existing CV"""
        original_cv = self.get_object()
        new_cv = UserCV.objects.create(
            user=request.user,
            template_type=original_cv.template_type,
            is_primary=False
        )
        for section in original_cv.cv_sections.all():
            CVSection.objects.create(
                cv=new_cv,
                section_type=section.section_type,
                content_json=section.content_json,
                display_order=section.display_order
            )
        return Response({
            'message': 'CV duplicated successfully',
            'cv': UserCVDetailSerializer(new_cv).data
        }, status=status.HTTP_201_CREATED)


# CV Section ViewSet

class CVSectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CV sections

    Endpoints:
    - GET /api/cvs/sections/?cv_id={id} - List sections for a CV
    - POST /api/cvs/sections/ - Add section to CV
    - GET /api/cvs/sections/{id}/ - Get section details
    - PUT /api/cvs/sections/{id}/ - Update section
    - DELETE /api/cvs/sections/{id}/ - Delete section
    - POST /api/cvs/sections/reorder/ - Reorder sections
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CVSectionSerializer

    def get_queryset(self):
        cv_id = self.request.query_params.get('cv_id')
        queryset = CVSection.objects.filter(cv__user=self.request.user)
        if cv_id:
            queryset = queryset.filter(cv_id=cv_id)
        return queryset.order_by('display_order')

    def create(self, request, *args, **kwargs):
        cv_id = request.data.get('cv_id')
        if not cv_id:
            return Response({'detail': 'cv_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cv = UserCV.objects.get(id=cv_id, user=request.user)
        except UserCV.DoesNotExist:
            return Response({'detail': 'CV not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CVSectionCreateSerializer(data=request.data)
        if serializer.is_valid():
            section = serializer.save(cv=cv)
            return Response(CVSectionSerializer(section).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder sections"""
        section_orders = request.data.get('section_orders', [])
        for item in section_orders:
            try:
                section = CVSection.objects.get(id=item.get('id'), cv__user=request.user)
                section.display_order = item.get('order')
                section.save(update_fields=['display_order'])
            except CVSection.DoesNotExist:
                pass
        return Response({'message': 'Sections reordered successfully'})


# Work Experience ViewSet

class WorkExperienceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing work experience

    Endpoints:
    - GET /api/cvs/experience/ - List work experiences
    - POST /api/cvs/experience/ - Add work experience
    - GET /api/cvs/experience/{id}/ - Get experience details
    - PUT /api/cvs/experience/{id}/ - Update experience
    - DELETE /api/cvs/experience/{id}/ - Delete experience
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkExperience.objects.filter(user=self.request.user).order_by('-is_current', '-start_date')

    def get_serializer_class(self):
        if self.action == 'create':
            return WorkExperienceCreateSerializer
        return WorkExperienceSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# Education ViewSet

class EducationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing education

    Endpoints:
    - GET /api/cvs/education/ - List education entries
    - POST /api/cvs/education/ - Add education
    - GET /api/cvs/education/{id}/ - Get education details
    - PUT /api/cvs/education/{id}/ - Update education
    - DELETE /api/cvs/education/{id}/ - Delete education
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Education.objects.filter(user=self.request.user).order_by('-start_date')

    def get_serializer_class(self):
        if self.action == 'create':
            return EducationCreateSerializer
        return EducationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# Projects ViewSet

class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects

    Endpoints:
    - GET /api/cvs/projects/ - List projects
    - POST /api/cvs/projects/ - Add project
    - GET /api/cvs/projects/{id}/ - Get project details
    - PUT /api/cvs/projects/{id}/ - Update project
    - DELETE /api/cvs/projects/{id}/ - Delete project
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).prefetch_related('project_skills__skill').order_by('-start_date')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# CV Generation ViewSet

class CVGenerationViewSet(viewsets.ViewSet):
    """
    ViewSet for CV generation

    Endpoints:
    - POST /api/cvs/generate/auto/ - Auto-generate CV from profile
    - GET /api/cvs/generate/preview/ - Preview CV before generation
    - POST /api/cvs/generate/from-data/ - Generate CV from submitted data
    - GET /api/cvs/generate/templates/ - List available templates
    - GET /api/cvs/generate/builder-progress/ - Get CV builder progress
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def auto(self, request):
        """Auto-generate CV from user's profile data"""
        serializer = AutoGenerateCVSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        template_type = serializer.validated_data.get('template_type', 'modern')
        set_as_primary = serializer.validated_data.get('set_as_primary', False)

        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            profile = None

        cv = UserCV.objects.create(user=user, template_type=template_type, is_primary=set_as_primary)

        if set_as_primary:
            UserCV.objects.filter(user=user, is_primary=True).exclude(id=cv.id).update(is_primary=False)

        section_order = 0

        # Personal Details Section
        personal_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone or '',
            'location': user.location or '',
            'linkedin_url': profile.linkedin_url if profile else '',
            'github_url': profile.github_url if profile else '',
            'portfolio_url': profile.portfolio_url if profile else '',
        }
        CVSection.objects.create(
            cv=cv, section_type='summary',
            content_json={'personal_details': personal_data, 'summary': profile.bio if profile else ''},
            display_order=section_order
        )
        section_order += 1

        # Work Experience Section
        experiences = WorkExperience.objects.filter(user=user).order_by('-start_date')
        if experiences.exists():
            CVSection.objects.create(
                cv=cv, section_type='experience',
                content_json={'experiences': WorkExperienceSerializer(experiences, many=True).data},
                display_order=section_order
            )
            section_order += 1

        # Education Section
        education_list = Education.objects.filter(user=user).order_by('-start_date')
        if education_list.exists():
            CVSection.objects.create(
                cv=cv, section_type='education',
                content_json={'education': EducationSerializer(education_list, many=True).data},
                display_order=section_order
            )
            section_order += 1

        # Skills Section
        user_skills = UserSkill.objects.filter(user=user, status='learned').select_related('skill', 'level')
        if user_skills.exists():
            skills_data = [
                {'name': us.skill.name, 'category': us.skill.category, 'level': us.level.name if us.level else 'Intermediate'}
                for us in user_skills
            ]
            CVSection.objects.create(
                cv=cv, section_type='skills',
                content_json={'skills': skills_data},
                display_order=section_order
            )
            section_order += 1

        # Projects Section
        projects = Project.objects.filter(user=user).order_by('-start_date')
        if projects.exists():
            CVSection.objects.create(
                cv=cv, section_type='projects',
                content_json={'projects': ProjectSerializer(projects, many=True).data},
                display_order=section_order
            )

        UserNotification.create_notification(
            user=user, notification_type='cv_generated',
            title='CV Generated!',
            message='Your CV has been automatically generated from your profile.',
            link_url=f'/cv/{cv.id}'
        )

        return Response({
            'message': 'CV generated successfully',
            'cv': UserCVDetailSerializer(cv).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def preview(self, request):
        """Preview CV data before generation"""
        user = request.user
        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            profile = None

        personal_details = {
            'first_name': user.first_name, 'last_name': user.last_name,
            'email': user.email, 'phone': user.phone or '', 'location': user.location or '',
            'linkedin_url': profile.linkedin_url if profile else '',
            'github_url': profile.github_url if profile else '',
            'portfolio_url': profile.portfolio_url if profile else '',
        }

        experiences = WorkExperience.objects.filter(user=user).order_by('-start_date')
        education_list = Education.objects.filter(user=user).order_by('-start_date')
        projects = Project.objects.filter(user=user).order_by('-start_date')
        user_skills = UserSkill.objects.filter(user=user, status='learned').select_related('skill', 'level')

        skills_data = [
            {'id': us.skill.id, 'name': us.skill.name, 'category': us.skill.category, 'level': us.level.name if us.level else 'Intermediate'}
            for us in user_skills
        ]

        return Response({
            'personal_details': personal_details,
            'summary': profile.bio if profile else None,
            'experience': WorkExperienceSerializer(experiences, many=True).data,
            'education': EducationSerializer(education_list, many=True).data,
            'skills': skills_data,
            'projects': ProjectSerializer(projects, many=True).data,
            'certifications': [],
            'languages': [],
            'template_type': 'modern'
        })

    @action(detail=False, methods=['post'], url_path='from-data')
    def from_data(self, request):
        """Generate CV from manually submitted data"""
        user = request.user
        data = request.data
        template_type = data.get('template_type', 'modern')
        set_as_primary = data.get('set_as_primary', False)

        cv = UserCV.objects.create(user=user, template_type=template_type, is_primary=set_as_primary)
        if set_as_primary:
            UserCV.objects.filter(user=user, is_primary=True).exclude(id=cv.id).update(is_primary=False)

        section_order = 0
        if data.get('personal_details'):
            CVSection.objects.create(
                cv=cv, section_type='summary',
                content_json={'personal_details': data['personal_details'], 'summary': data.get('summary', '')},
                display_order=section_order
            )
            section_order += 1

        if data.get('experience'):
            CVSection.objects.create(cv=cv, section_type='experience', content_json={'experiences': data['experience']}, display_order=section_order)
            section_order += 1

        if data.get('education'):
            CVSection.objects.create(cv=cv, section_type='education', content_json={'education': data['education']}, display_order=section_order)
            section_order += 1

        if data.get('skills'):
            CVSection.objects.create(cv=cv, section_type='skills', content_json={'skills': data['skills']}, display_order=section_order)
            section_order += 1

        if data.get('projects'):
            CVSection.objects.create(cv=cv, section_type='projects', content_json={'projects': data['projects']}, display_order=section_order)
            section_order += 1

        if data.get('certifications'):
            CVSection.objects.create(cv=cv, section_type='certifications', content_json={'certifications': data['certifications']}, display_order=section_order)
            section_order += 1

        if data.get('languages'):
            CVSection.objects.create(cv=cv, section_type='languages', content_json={'languages': data['languages']}, display_order=section_order)

        return Response({'message': 'CV created successfully', 'cv': UserCVDetailSerializer(cv).data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def templates(self, request):
        """List available CV templates"""
        templates = [
            {'template_id': 'modern', 'name': 'Modern', 'description': 'Clean and modern design with a professional look', 'preview_image_url': None, 'is_premium': False},
            {'template_id': 'classic', 'name': 'Classic', 'description': 'Traditional CV format, suitable for conservative industries', 'preview_image_url': None, 'is_premium': False},
            {'template_id': 'minimal', 'name': 'Minimal', 'description': 'Simple and minimalist design focusing on content', 'preview_image_url': None, 'is_premium': False},
            {'template_id': 'professional', 'name': 'Professional', 'description': 'Formal design for corporate environments', 'preview_image_url': None, 'is_premium': False},
            {'template_id': 'creative', 'name': 'Creative', 'description': 'Eye-catching design for creative industries', 'preview_image_url': None, 'is_premium': True}
        ]
        serializer = CVTemplateSerializer(templates, many=True)
        return Response({'count': len(templates), 'templates': serializer.data})

    @action(detail=False, methods=['get'], url_path='builder-progress')
    def builder_progress(self, request):
        """Get CV builder progress"""
        user = request.user
        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            profile = None

        has_name = bool(user.first_name and user.last_name)
        has_email = bool(user.email)
        has_summary = bool(profile and profile.bio)
        has_experience = WorkExperience.objects.filter(user=user).exists()
        has_education = Education.objects.filter(user=user).exists()
        has_skills = UserSkill.objects.filter(user=user, status='learned').exists()
        has_projects = Project.objects.filter(user=user).exists()

        completed_steps = []
        if has_name and has_email:
            completed_steps.append('personal_details')
        if has_summary:
            completed_steps.append('summary')
        if has_experience:
            completed_steps.append('experience')
        if has_education:
            completed_steps.append('education')
        if has_skills:
            completed_steps.append('skills')
        if has_projects:
            completed_steps.append('projects')

        all_steps = ['personal_details', 'summary', 'experience', 'education', 'skills', 'projects', 'certifications', 'languages']
        next_step = next((step for step in all_steps if step not in completed_steps), None)

        progress_data = {
            'current_step': len(completed_steps) + 1,
            'total_steps': len(all_steps),
            'completed_steps': completed_steps,
            'next_step': next_step,
            'personal_details_complete': has_name and has_email,
            'summary_complete': has_summary,
            'experience_complete': has_experience,
            'education_complete': has_education,
            'skills_complete': has_skills,
            'projects_complete': has_projects,
            'certifications_complete': False,
            'languages_complete': False
        }
        serializer = CVBuilderProgressSerializer(progress_data)
        return Response(serializer.data)


# CV Export ViewSet

class CVExportViewSet(viewsets.ViewSet):
    """
    ViewSet for CV export

    Endpoints:
    - POST /api/cvs/export/pdf/{cv_id}/ - Export CV as PDF
    - POST /api/cvs/export/docx/{cv_id}/ - Export CV as DOCX
    - GET /api/cvs/export/download/{cv_id}/ - Download generated CV file
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='pdf/(?P<cv_id>[^/.]+)')
    def pdf(self, request, cv_id=None):
        """Export CV as PDF"""
        try:
            cv = UserCV.objects.get(id=cv_id, user=request.user)
        except UserCV.DoesNotExist:
            return Response({'detail': 'CV not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'PDF generation initiated',
            'cv_id': cv.id,
            'cv_data': UserCVDetailSerializer(cv).data,
            'format': 'pdf'
        })

    @action(detail=False, methods=['post'], url_path='docx/(?P<cv_id>[^/.]+)')
    def docx(self, request, cv_id=None):
        """Export CV as DOCX"""
        try:
            cv = UserCV.objects.get(id=cv_id, user=request.user)
        except UserCV.DoesNotExist:
            return Response({'detail': 'CV not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'DOCX generation initiated',
            'cv_id': cv.id,
            'cv_data': UserCVDetailSerializer(cv).data,
            'format': 'docx'
        })

    @action(detail=False, methods=['get'], url_path='download/(?P<cv_id>[^/.]+)')
    def download(self, request, cv_id=None):
        """Download generated CV file"""
        try:
            cv = UserCV.objects.get(id=cv_id, user=request.user)
        except UserCV.DoesNotExist:
            return Response({'detail': 'CV not found'}, status=status.HTTP_404_NOT_FOUND)

        if not cv.file_path or not os.path.exists(cv.file_path):
            return Response({'detail': 'CV file not generated yet. Please export first.'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(cv.file_path, 'rb'), as_attachment=True, filename=os.path.basename(cv.file_path))
