"""
Users App Views - Part 2: Profile & Skills Management
======================================================
backend/apps/users/views_profile.py

API endpoints for profile management and user skills.
"""

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction

from .models import User, UserProfile
from apps.skills.models import Skill, UserSkill
from apps.interests.models import Interest, UserInterest
from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    QuestionnaireProfileSerializer,
    CVUploadSerializer,
    UserSkillSerializer,
    AddUserSkillSerializer,
    UpdateUserSkillSerializer
)
from .utils.cv_processor import CVProcessor
from apps.users.utils.profile_updater import ProfileUpdater

class UserProfileView(APIView):
    """
    Get or update user profile.
    
    GET /api/profile/
    PUT /api/profile/
    PATCH /api/profile/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current user's profile."""
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        """Full update of user profile."""
        try:
            profile = request.user.profile
            serializer = UserProfileUpdateSerializer(
                profile,
                data=request.data
            )
            
            if serializer.is_valid():
                serializer.save()
                
                # Mark profile as completed if basic info is filled
                if profile.current_job_position or profile.desired_role:
                    request.user.profile_completed = True
                    request.user.save()
                
                return Response(
                    UserProfileSerializer(profile).data,
                    status=status.HTTP_200_OK
                )
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request):
        """Partial update of user profile."""
        try:
            profile = request.user.profile
            serializer = UserProfileUpdateSerializer(
                profile,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                
                return Response(
                    UserProfileSerializer(profile).data,
                    status=status.HTTP_200_OK
                )
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class QuestionnaireProfileView(APIView):
    """
    Create/update profile via step-by-step questionnaire.
    
    POST /api/profile/questionnaire/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = QuestionnaireProfileSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Update profile
            profile = request.user.profile
            profile.current_job_position = data.get('current_job_position', '')
            profile.desired_role = data.get('desired_role', '')
            profile.experience_level = data['experience_level']
            profile.bio = data.get('bio', '')
            profile.location = data.get('location', '')
            profile.profile_source = 'assessment'
            profile.save()
            
            # Add skills
            skill_ids = data.get('skills', [])
            if skill_ids:
                for skill_id in skill_ids:
                    UserSkill.objects.get_or_create(
                        user=request.user,
                        skill_id=skill_id,
                        defaults={'source': 'assessment'}
                    )
            
            # Add interests
            interest_ids = data.get('interests', [])
            if interest_ids:
                for interest_id in interest_ids:
                    UserInterest.objects.get_or_create(
                        user=request.user,
                        interest_id=interest_id
                    )
            
            # Mark profile as completed
            request.user.profile_completed = True
            request.user.save()
            
            return Response({
                'message': 'Profile created successfully',
                'profile': UserProfileSerializer(profile).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class CVUploadView(APIView):
    """Upload and process CV with hybrid extraction."""
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @transaction.atomic
    def post(self, request):
        # Validate
        serializer = CVUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        cv_file = serializer.validated_data['cv_file']
        
        try:
            # Save file
            profile = request.user.profile
            profile.cv_file_path = cv_file
            profile.save()
            
            # Process
            processor = CVProcessor(
                use_ollama_fallback=True,
                quality_threshold=0.6
            )
            result = processor.process(profile.cv_file_path.path)
            
            if not result['success']:
                return Response({
                    'success': False,
                    'errors': result['errors']
                }, status=500)
            
            # Update profile
            updater = ProfileUpdater()
            update_result = updater.update_from_cv(request.user, result['data'])
            
            # Validate
            validation = updater.validate_for_roadmap(request.user)
            
            # Response
            return Response({
                'success': True,
                'extraction': {
                    'method': result['data'].get('_extraction_method'),
                    'quality': result['data'].get('_quality_score'),
                    'time': result['data'].get('_processing_time'),
                    'job_position': result['data']['job_position'],
                    'skills_found': len(result['data']['skill_matches']),
                    'years': result['data']['years_of_experience']
                },
                'updates': update_result,
                'roadmap_ready': validation['ready']
            }, status=201)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

    
    def _update_profile(self, user, extracted_data: dict) -> list:
        """
        Update user profile with extracted data.
        
        Returns list of updated field names.
        """
        profile = user.profile
        updated_fields = []
        
        # Update job position
        if extracted_data.get('job_position'):
            profile.current_job_position = extracted_data['job_position']
            updated_fields.append('job_position')
        
        # Update experience level
        if extracted_data.get('experience_level'):
            profile.experience_level = extracted_data['experience_level']
            updated_fields.append('experience_level')
        
        # Update bio
        if extracted_data.get('bio'):
            profile.bio = extracted_data['bio']
            updated_fields.append('bio')
        
        # Update education (if not already set)
        if extracted_data.get('education') and not profile.bio:
            profile.bio = extracted_data['education']
            updated_fields.append('education')
        
        # Update phone (if user doesn't have one)
        if extracted_data.get('phone') and not user.phone:
            user.phone = extracted_data['phone']
            user.save()
            updated_fields.append('phone')
        
        profile.save()
        return updated_fields
    
    def _add_skills(self, user, skill_ids: list) -> int:
        """
        Add extracted skills to user profile.
        
        Returns count of skills added.
        """
        added_count = 0
        
        for skill_id in skill_ids:
            _, created = UserSkill.objects.get_or_create(
                user=user,
                skill_id=skill_id,
                defaults={
                    'source': 'cv',
                    'proficiency_level': 'intermediate',  # Default
                    'years_of_experience': 0.0
                }
            )
            
            if created:
                added_count += 1
        
        return added_count

class UserSkillsView(APIView):
    """
    Get all user skills.
    
    GET /api/profile/skills/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_skills = UserSkill.objects.filter(
            user=request.user
        ).select_related('skill').order_by('-added_at')
        
        serializer = UserSkillSerializer(user_skills, many=True)
        
        return Response({
            'count': user_skills.count(),
            'skills': serializer.data
        }, status=status.HTTP_200_OK)


class AddUserSkillsView(APIView):
    """
    Add skills to user profile.
    
    POST /api/profile/skills/add/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = AddUserSkillSerializer(data=request.data)
        
        if serializer.is_valid():
            skill_ids = serializer.validated_data['skill_ids']
            proficiency_level = serializer.validated_data['proficiency_level']
            years_of_experience = serializer.validated_data.get('years_of_experience', 0.0)
            source = serializer.validated_data['source']
            is_primary = serializer.validated_data.get('is_primary', False) 
            
            added_skills = []
            
            for skill_id in skill_ids:
                user_skill, created = UserSkill.objects.get_or_create(
                    user=request.user,
                    skill_id=skill_id,
                    defaults={
                        'proficiency_level': proficiency_level,
                        'years_of_experience': years_of_experience,
                        'source': source,
                        'is_primary': is_primary
                    }
                )
                
                if created:
                    added_skills.append(user_skill)
            
            return Response({
                'message': f'{len(added_skills)} skill(s) added successfully',
                'skills': UserSkillSerializer(added_skills, many=True).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class UpdateUserSkillView(APIView):
    """
    Update user skill proficiency.
    
    PATCH /api/profile/skills/<skill_id>/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, skill_id):
        try:
            user_skill = UserSkill.objects.get(
                user=request.user,
                user_skill_id=skill_id
            )
            
            serializer = UpdateUserSkillSerializer(
                user_skill,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                
                return Response({
                    'message': 'Skill updated successfully',
                    'skill': UserSkillSerializer(user_skill).data
                }, status=status.HTTP_200_OK)
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except UserSkill.DoesNotExist:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DeleteUserSkillView(APIView):
    """
    Delete user skill.
    
    DELETE /api/profile/skills/<skill_id>/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, skill_id):
        try:
            user_skill = UserSkill.objects.get(
                user=request.user,
                user_skill_id=skill_id
            )
            
            skill_name = user_skill.skill.name_en
            user_skill.delete()
            
            return Response({
                'message': f'Skill "{skill_name}" removed successfully'
            }, status=status.HTTP_200_OK)
        
        except UserSkill.DoesNotExist:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )