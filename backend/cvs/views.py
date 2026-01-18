"""
Views for CV upload and processing
"""
import os
from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from cvs.models import UploadedCV, CVExtractionLog
from cvs.serializers import (
    CVUploadSerializer, UploadedCVSerializer,
    CVExtractionResultSerializer, CVExtractionLogSerializer
)
from cvs.services import CVProcessor
from skills.models import Skill, SkillLevel, UserSkill
from users.models import UserProfile
from notifications.models import UserNotification


class CVUploadView(APIView):
    """
    Upload CV for processing
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = CVUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            cv_file = serializer.validated_data['cv_file']
            user = request.user
            
            # Determine file type
            file_extension = cv_file.name.split('.')[-1].lower()
            
            # Create upload directory if not exists
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_cvs', str(user.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, cv_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in cv_file.chunks():
                    destination.write(chunk)
            
            # Create UploadedCV record
            uploaded_cv = UploadedCV.objects.create(
                user=user,
                original_filename=cv_file.name,
                file_path=file_path,
                file_type=file_extension,
                processing_status='pending'
            )
            
            # Start processing
            try:
                uploaded_cv.mark_processing()
                
                # Process CV
                processor = CVProcessor()
                extracted_data = processor.process_cv(file_path, file_extension)
                
                # Save extracted data
                uploaded_cv.mark_completed(extracted_data)
                
                # Create extraction log
                CVExtractionLog.objects.create(
                    uploaded_cv=uploaded_cv,
                    skills_extracted_count=extracted_data['skills_count'],
                    confidence_score=extracted_data['confidence_score']
                )
                
                # Populate user profile
                self._populate_user_profile(user, extracted_data)
                
                # Create notification
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
        """
        Populate user profile with extracted CV data
        """
        # Update user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        
        # Set experience level
        if extracted_data.get('experience_level'):
            profile.experience_level = extracted_data['experience_level']
        
        # Set current role (from first job title)
        if extracted_data.get('job_titles'):
            profile.current_role = extracted_data['job_titles'][0]
        
        profile.save()
        
        # Add skills
        for skill_name in extracted_data.get('skills', []):
            # Get or create skill
            skill, _ = Skill.objects.get_or_create(
                name__iexact=skill_name,
                defaults={'name': skill_name, 'category': 'other'}
            )
            
            # Get intermediate level by default
            skill_level = SkillLevel.objects.filter(level_order=2).first()
            
            # Create UserSkill
            UserSkill.objects.get_or_create(
                user=user,
                skill=skill,
                defaults={
                    'level': skill_level,
                    'status': 'learned',
                    'self_assessed': False  # From CV, not self-assessed
                }
            )
        
        # Update onboarding method
        user.onboarding_method = 'cv_upload'
        user.it_knowledge_level = 'experienced'
        user.update_profile_completion()
        user.save(update_fields=['onboarding_method', 'it_knowledge_level'])


class UploadedCVListView(generics.ListAPIView):
    """
    List all uploaded CVs for current user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UploadedCVSerializer
    
    def get_queryset(self):
        return UploadedCV.objects.filter(user=self.request.user)


class UploadedCVDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific uploaded CV
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UploadedCVSerializer
    
    def get_queryset(self):
        return UploadedCV.objects.filter(user=self.request.user)