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
    """
    Upload CV and extract profile data using NLP.
    
    POST /api/profile/cv-upload/
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @transaction.atomic
    def post(self, request):
        serializer = CVUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            cv_file = serializer.validated_data['cv_file']
            
            # Save CV file
            profile = request.user.profile
            profile.cv_file_path = cv_file
            profile.profile_source = 'cv_upload'
            profile.save()
            
            # Extract data from CV
            try:
                extracted_data = self._extract_cv_data(cv_file)
                
                # Update profile with extracted data
                if extracted_data:
                    profile.current_job_position = extracted_data.get('job_position', '')
                    profile.experience_level = extracted_data.get('experience_level', 'beginner')
                    profile.bio = extracted_data.get('summary', '')
                    profile.save()
                    
                    # Add extracted skills
                    skill_names = extracted_data.get('skills', [])
                    added_skills = self._add_skills_from_cv(request.user, skill_names)
                    
                    # Mark profile as completed
                    request.user.profile_completed = True
                    request.user.save()
                    
                    return Response({
                        'message': 'CV uploaded and analyzed successfully',
                        'profile': UserProfileSerializer(profile).data,
                        'extracted_data': {
                            'job_position': extracted_data.get('job_position'),
                            'experience_level': extracted_data.get('experience_level'),
                            'skills_added': added_skills
                        }
                    }, status=status.HTTP_201_CREATED)
                
                else:
                    return Response({
                        'message': 'CV uploaded but extraction failed',
                        'detail': 'Please complete your profile manually',
                        'profile': UserProfileSerializer(profile).data
                    }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({
                    'error': 'CV processing failed',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def _extract_cv_data(self, cv_file):
        """
        Extract data from CV using NLP.
        
        Uses spaCy or other NLP library to extract:
        - Job position
        - Skills
        - Experience level
        - Summary/bio
        """
        # TODO: Implement NLP extraction
        # For now, return None (will be implemented in next step)
        return None
    
    def _add_skills_from_cv(self, user, skill_names):
        """
        Match extracted skill names to database skills and add to user.
        """
        added_count = 0
        
        for skill_name in skill_names:
            # Try to find skill by name (case-insensitive)
            skill = Skill.objects.filter(
                name_en__iexact=skill_name
            ).first()
            
            if skill:
                UserSkill.objects.get_or_create(
                    user=user,
                    skill=skill,
                    defaults={'source': 'cv'}
                )
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