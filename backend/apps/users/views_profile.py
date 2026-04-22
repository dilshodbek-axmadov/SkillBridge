"""
Users App Views - Part 2: Profile & Skills Management

API endpoints for profile management and user skills.
"""

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.db.models import Q

from .models import User, UserProfile, UserActivity
from apps.skills.models import Skill, UserSkill
from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    CVUploadSerializer,
    UserActivitySerializer,
)
from .serializers_profile import (
    StepByStepProfileSerializer,
    UserProfileSummarySerializer,
    AddUserSkillSerializer,
    UpdateUserSkillSerializer,
    BulkAddSkillsSerializer,
    UserSkillSerializer,
    SkillListSerializer
)
from .utils.cv_processor import CVProcessor
from apps.users.utils.profile_updater import ProfileUpdater
from .activity_log import log_user_activity

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
            skills_n = len(result['data'].get('skill_matches') or [])
            log_user_activity(
                request.user,
                UserActivity.ActivityType.CV_UPLOADED,
                f'CV processed: {skills_n} skill(s) matched to your profile.',
                metadata={'skills_found': skills_n},
                link_path='/profile-cv',
            )
            return Response({
                'success': True,
                'extraction': {
                    'method': result['data'].get('_extraction_method'),
                    'quality': result['data'].get('_quality_score'),
                    'time': result['data'].get('_processing_time'),
                    'job_position': result['data']['job_position'],
                    'skills_found': skills_n,
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
    
# ===== SKILLS BROWSING =====

class GetAllSkillsView(APIView):
    """
    Get all available skills for selection.
    
    GET /api/skills/browse/
    
    Query params:
    - category: Filter by category (optional)
    - search: Search by name (optional)
    - verified_only: true/false (default: true)
    - page: Page number (default: 1)
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Base queryset
        skills = Skill.objects.all()
        
        # Filter by verified
        verified_only = request.query_params.get('verified_only', 'true').lower() == 'true'
        if verified_only:
            skills = skills.filter(is_verified=True)
        
        # Filter by category
        category = request.query_params.get('category')
        if category:
            skills = skills.filter(category=category)
        
        # Search by name
        search = request.query_params.get('search', '').strip()
        if search:
            skills = skills.filter(
                Q(name_en__icontains=search) |
                Q(name_ru__icontains=search) |
                Q(name_uz__icontains=search) |
                Q(normalized_key__icontains=search)
            )
        
        # Order by name
        skills = skills.order_by('name_en')
        
        # Pagination
        page_size = 50
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = skills.count()
        skills_page = skills[start:end]
        
        serializer = SkillListSerializer(skills_page, many=True)
        
        return Response({
            'skills': serializer.data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'has_next': end < total_count,
            'total_pages': (total_count + page_size - 1) // page_size
        })


class SearchSkillsView(APIView):
    """
    Search skills by name (for autocomplete).
    
    GET /api/skills/search/?q=python
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Response({
                'message': 'Query must be at least 2 characters',
                'skills': []
            })
        
        # Search in all language fields and normalized key
        skills = Skill.objects.filter(
            Q(name_en__icontains=query) |
            Q(name_ru__icontains=query) |
            Q(name_uz__icontains=query) |
            Q(normalized_key__icontains=query)
        )

        verified_only = request.query_params.get('verified_only', 'true').lower() == 'true'
        if verified_only:
            skills = skills.filter(is_verified=True)

        skills = skills.order_by('name_en')[:20]
        
        serializer = SkillListSerializer(skills, many=True)
        
        return Response({
            'query': query,
            'skills': serializer.data,
            'count': len(serializer.data)
        })


class GetSkillCategoriesView(APIView):
    """
    Get available skill categories.
    
    GET /api/skills/categories/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        categories = [
            {'value': code, 'label': label}
            for code, label in Skill.CATEGORY_CHOICES
        ]
        
        return Response({'categories': categories})


# ===== MANUAL PROFILE CREATION =====

class CreateManualProfileView(APIView):
    """
    Create user profile manually (step-by-step).
    
    POST /api/profile/create-manual/
    
    Body:
    {
        "current_job_position": "Backend Developer",
        "experience_level": "mid",
        "skills": [
            {"skill_id": 1, "proficiency_level": "intermediate", "years_of_experience": 2.0},
            {"skill_id": 5, "proficiency_level": "beginner"}
        ],
        "interest_ids": [1, 3, 5],
        "bio": "Optional bio"
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Validate input
        serializer = StepByStepProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        # Create profile
        result = serializer.create_profile(request.user)
        
        # Prepare response
        profile_serializer = UserProfileSummarySerializer(result['profile'])

        log_user_activity(
            request.user,
            UserActivity.ActivityType.PROFILE_SETUP,
            'Profile created with your role and skills.',
            metadata={
                'skills_added': result.get('skills_added', 0),
            },
            link_path='/dashboard',
        )

        return Response({
            'message': 'Profile created successfully',
            'profile': profile_serializer.data,
            'stats': {
                'skills_added': result['skills_added'],
            },
            'profile_completed': True
        }, status=201)


class GetProfileSummaryView(APIView):
    """
    Get user's complete profile summary.
    
    GET /api/profile/summary/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        profile = user.profile
        
        # Get skills
        user_skills = UserSkill.objects.filter(user=user).select_related('skill')
        primary_skills = user_skills.filter(is_primary=True)
        
        # Check profile completion
        has_position = bool(profile.current_job_position or profile.desired_role)
        has_skills = user_skills.count() >= 1
        has_experience = bool(profile.experience_level)
        profile_completed = has_position and has_skills and has_experience
        
        return Response({
            'user': {
                'email': user.email,
                'profile_completed': user.profile_completed
            },
            'profile': {
                'current_job_position': profile.current_job_position,
                'desired_role': profile.desired_role,
                'experience_level': profile.experience_level,
                'bio': profile.bio,
                'profile_source': profile.profile_source
            },
            'skills': {
                'total': user_skills.count(),
                'primary': primary_skills.count(),
                'list': [
                    {
                        'user_skill_id': skill.user_skill_id,
                        'name_en': skill.skill.name_en,
                        'name_ru': skill.skill.name_ru,
                        'category': skill.skill.category,
                        'proficiency': skill.proficiency_level,
                        'years': skill.years_of_experience,
                        'is_primary': skill.is_primary,
                        'source': skill.source
                    }
                    for skill in user_skills
                ]
            },
            'completion': {
                'profile_completed': profile_completed,
                'has_position': has_position,
                'has_skills': has_skills,
                'has_experience': has_experience,
                'completion_percentage': int((
                    (has_position + has_skills + has_experience) / 3.0
                ) * 100)
            }
        })


# ===== USER SKILLS MANAGEMENT (CRUD) =====

class GetMySkillsView(APIView):
    """
    Get user's skills.
    
    GET /api/profile/my-skills/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_skills = UserSkill.objects.filter(
            user=request.user
        ).select_related('skill').order_by('-is_primary', 'skill__name_en')
        
        serializer = UserSkillSerializer(user_skills, many=True)
        
        return Response({
            'skills': serializer.data,
            'count': user_skills.count()
        })


class AddSkillView(APIView):
    """
    Add a skill to user's profile.
    
    POST /api/profile/skills/add/
    
    Body:
    {
        "skill_id": 1,
        "proficiency_level": "intermediate",
        "years_of_experience": 2.0,
        "is_primary": false
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = AddUserSkillSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        data = serializer.validated_data
        
        # Check if skill already exists
        if UserSkill.objects.filter(user=request.user, skill_id=data['skill_id']).exists():
            return Response({
                'error': 'This skill is already in your profile'
            }, status=400)
        
        # Create UserSkill
        user_skill = UserSkill.objects.create(
            user=request.user,
            skill_id=data['skill_id'],
            proficiency_level=data['proficiency_level'],
            years_of_experience=data['years_of_experience'],
            is_primary=data['is_primary'],
            source='manual'
        )
        
        response_serializer = UserSkillSerializer(user_skill)
        skill_name = user_skill.skill.name_en if hasattr(user_skill, 'skill') else ''

        log_user_activity(
            request.user,
            UserActivity.ActivityType.SKILL_ADDED,
            f'Added skill: {skill_name}.',
            metadata={'skill_id': user_skill.skill_id, 'skill_name': skill_name},
            link_path='/manage-skills',
        )

        return Response({
            'message': 'Skill added successfully',
            'skill': response_serializer.data
        }, status=201)


class BulkAddSkillsView(APIView):
    """
    Add multiple skills at once.
    
    POST /api/profile/skills/bulk-add/
    
    Body:
    {
        "skills": [
            {"skill_id": 1, "proficiency_level": "intermediate", "years_of_experience": 2.0},
            {"skill_id": 5, "proficiency_level": "beginner"}
        ]
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = BulkAddSkillsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        skills_data = serializer.validated_data['skills']
        
        added = 0
        skipped = 0
        
        for skill_data in skills_data:
            # Check if already exists
            if UserSkill.objects.filter(user=request.user, skill_id=skill_data['skill_id']).exists():
                skipped += 1
                continue
            
            # Create UserSkill
            UserSkill.objects.create(
                user=request.user,
                skill_id=skill_data['skill_id'],
                proficiency_level=skill_data['proficiency_level'],
                years_of_experience=skill_data['years_of_experience'],
                is_primary=skill_data['is_primary'],
                source='manual'
            )
            added += 1

        if added > 0:
            log_user_activity(
                request.user,
                UserActivity.ActivityType.SKILLS_BULK_ADDED,
                f'Added {added} skills to your profile.',
                metadata={'added': added, 'skipped': skipped},
                link_path='/manage-skills',
            )

        return Response({
            'message': f'Added {added} skills',
            'added': added,
            'skipped': skipped,
            'total': added + skipped
        }, status=201)


class UpdateSkillView(APIView):
    """
    Update a user's skill.
    
    PATCH /api/profile/skills/update/<int:user_skill_id>/
    
    Body:
    {
        "proficiency_level": "advanced",
        "years_of_experience": 3.0,
        "is_primary": true
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def patch(self, request, user_skill_id):
        # Get user skill
        try:
            user_skill = UserSkill.objects.get(
                user_skill_id=user_skill_id,
                user=request.user
            )
        except UserSkill.DoesNotExist:
            return Response({
                'error': 'Skill not found in your profile'
            }, status=404)
        
        # Validate input
        serializer = UpdateUserSkillSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        # Update fields
        data = serializer.validated_data
        
        if 'proficiency_level' in data:
            user_skill.proficiency_level = data['proficiency_level']
        
        if 'years_of_experience' in data:
            user_skill.years_of_experience = data['years_of_experience']
        
        if 'is_primary' in data:
            user_skill.is_primary = data['is_primary']
        
        user_skill.save()
        
        response_serializer = UserSkillSerializer(user_skill)
        
        return Response({
            'message': 'Skill updated successfully',
            'skill': response_serializer.data
        })


class DeleteSkillView(APIView):
    """
    Delete a user's skill.
    
    DELETE /api/profile/skills/delete/<int:user_skill_id>/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def delete(self, request, user_skill_id):
        try:
            user_skill = UserSkill.objects.select_related('skill').get(
                user_skill_id=user_skill_id,
                user=request.user
            )
        except UserSkill.DoesNotExist:
            return Response({
                'error': 'Skill not found in your profile'
            }, status=404)
        
        skill_name = user_skill.skill.name_en
        user_skill.delete()

        log_user_activity(
            request.user,
            UserActivity.ActivityType.SKILL_REMOVED,
            f'Removed skill: {skill_name}.',
            metadata={'skill_name': skill_name},
            link_path='/manage-skills',
        )

        return Response({
            'message': f'Skill "{skill_name}" removed from profile'
        })


class UpdateJobPositionView(APIView):
    """
    Update job position only.
    
    PATCH /api/profile/update-position/
    
    Body:
    {
        "current_job_position": "Senior Backend Developer"
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        job_position = request.data.get('current_job_position', '').strip()
        
        if not job_position:
            return Response({
                'error': 'Job position cannot be empty'
            }, status=400)
        
        profile = request.user.profile
        profile.current_job_position = job_position
        profile.save()
        
        return Response({
            'message': 'Job position updated',
            'current_job_position': profile.current_job_position
        })


class UpdateExperienceLevelView(APIView):
    """
    Update experience level only.
    
    PATCH /api/profile/update-experience/
    
    Body:
    {
        "experience_level": "senior"
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        experience_level = request.data.get('experience_level', '').strip()
        
        valid_levels = ['beginner', 'junior', 'mid', 'senior', 'lead']
        if experience_level not in valid_levels:
            return Response({
                'error': f'Invalid experience level. Must be one of: {", ".join(valid_levels)}'
            }, status=400)
        
        profile = request.user.profile
        profile.experience_level = experience_level
        profile.save()
        
        return Response({
            'message': 'Experience level updated',
            'experience_level': profile.experience_level
        })


class UserActivityListView(APIView):
    """
    Paginated activity feed for the authenticated user.

    GET /api/v1/users/profile/activity/?page=1&page_size=20
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.query_params.get('page_size', 20))
        except (TypeError, ValueError):
            page_size = 20
        page_size = min(max(page_size, 1), 50)

        qs = UserActivity.objects.filter(user=request.user).order_by('-created_at')
        total = qs.count()
        start = (page - 1) * page_size
        rows = qs[start:start + page_size]
        total_pages = (total + page_size - 1) // page_size if total else 0

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'results': UserActivitySerializer(rows, many=True).data,
        })