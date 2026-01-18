"""
Views for user authentication and profile management
"""
from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db import transaction

from .serializers import (
    UserSerializer, RegisterSerializer, ChangePasswordSerializer,
    UpdateProfileSerializer, UserProfileSerializer, UpdateUserProfileSerializer,
    UserInterestSerializer,
    # Career Discovery serializers
    CareerDiscoveryQuestionSerializer, CareerDiscoveryResponseSerializer,
    CareerRecommendationSerializer,
    # Onboarding serializers
    OnboardingStep2Serializer, OnboardingStep3Serializer,
    OnboardingStep4Serializer, OnboardingStep5Serializer,
    CompleteOnboardingSerializer
)
from .models import UserProfile, UserInterest
from .services import CareerDiscoveryService
from career.models import Role
from career.services import SkillGapAnalyzer
from notifications.models import UserNotification

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update current user's profile
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """
    Change user password
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get('old_password')):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.data.get('new_password'))
            user.save()
            
            return Response(
                {"message": "Password updated successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(generics.UpdateAPIView):
    """
    Update basic user information
    """
    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UpdateExtendedProfileView(generics.UpdateAPIView):
    """
    Update extended user profile
    """
    serializer_class = UpdateUserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserInterestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user interests
    """
    serializer_class = UserInterestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserInterest.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CareerDiscoveryQuestionsView(generics.ListAPIView):
    """
    Get all career discovery questions for beginners
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CareerDiscoveryQuestionSerializer
    
    def get_queryset(self):
        """Return questions as queryset-like structure"""
        return CareerDiscoveryService.get_questions()
    
    def list(self, request, *args, **kwargs):
        """Override to return custom response format"""
        questions = self.get_queryset()
        serializer = self.get_serializer(questions, many=True)
        
        return Response({
            'questions': serializer.data,
            'total_steps': len(questions),
            'user_it_level': request.user.it_knowledge_level
        })


class CareerDiscoverySubmitView(generics.CreateAPIView):
    """
    Submit career discovery quiz responses and get recommendations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CareerDiscoveryResponseSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            responses = serializer.validated_data['responses']
            
            # Save responses to user profile
            CareerDiscoveryService.save_responses(user, responses)
            
            # Update user's IT knowledge level
            user.it_knowledge_level = 'complete_beginner'
            user.onboarding_method = 'career_discovery'
            user.save(update_fields=['it_knowledge_level', 'onboarding_method'])
            
            # Get recommendations
            recommendations = CareerDiscoveryService.get_recommended_roles(
                responses, 
                top_n=5
            )
            
            # Serialize recommendations
            rec_serializer = CareerRecommendationSerializer(
                recommendations, 
                many=True
            )
            
            return Response({
                'message': 'Career discovery completed!',
                'recommendations': rec_serializer.data,
                'total_recommendations': len(recommendations),
                'next_step': 'analytics_dashboard'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CareerDiscoverySelectView(generics.CreateAPIView):
    """
    User selects a career from discovery recommendations
    """
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        role_id = request.data.get('role_id')
        
        if not role_id:
            return Response(
                {'error': 'role_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            role = Role.objects.get(id=role_id)
            user = request.user
            
            # Perform skill gap analysis
            analyzer = SkillGapAnalyzer()
            gap_analysis = analyzer.analyze_user_for_role(user, role)
            
            # Create notification
            UserNotification.create_notification(
                user=user,
                notification_type='roadmap_update',
                title=f'Your {role.title} Roadmap is Ready!',
                message=f'We created a personalized learning roadmap to become a {role.title}.',
                link_url=f'/roadmap/{gap_analysis["gap_analysis_id"]}'
            )
            
            return Response({
                'message': f'Career path selected: {role.title}',
                'role': {
                    'id': role.id,
                    'title': role.title,
                    'description': role.description
                },
                'gap_analysis': gap_analysis,
                'next_step': 'view_roadmap'
            }, status=status.HTTP_201_CREATED)
            
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================
# ONBOARDING VIEWS (Class-Based)
# ============================================

class OnboardingStatusView(APIView):
    """
    Get current onboarding status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Check if user has completed onboarding
        has_profile = hasattr(user, 'userprofile') and user.userprofile.experience_level
        has_interests = user.user_interests.exists()
        has_skills = user.user_skills.exists()
        has_target_role = user.recommended_roles.exists()
        
        completed = all([has_profile, has_interests, has_skills, has_target_role])
        
        return Response({
            'completed': completed,
            'onboarding_method': user.onboarding_method,
            'it_knowledge_level': user.it_knowledge_level,
            'steps': {
                'step1': True,  # Registration is complete
                'step2': has_profile,
                'step3': has_interests,
                'step4': has_skills,
                'step5': has_target_role,
            }
        })


class OnboardingStep2View(generics.CreateAPIView):
    """
    Step 2: Professional background
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OnboardingStep2Serializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update profile
            profile.current_role = serializer.validated_data.get('current_role', '')
            profile.experience_level = serializer.validated_data['experience_level']
            profile.preferred_work_type = serializer.validated_data['preferred_work_type']
            profile.availability_status = serializer.validated_data['availability_status']
            profile.save()
            
            # Update user's profile completion
            user.update_profile_completion()
            
            return Response({
                'message': 'Step 2 completed',
                'profile': UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingStep3View(generics.CreateAPIView):
    """
    Step 3: Career interests
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OnboardingStep3Serializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Clear existing interests
            user.user_interests.all().delete()
            
            # Add new interests
            interests_data = serializer.validated_data['interests']
            for interest_data in interests_data:
                UserInterest.objects.create(
                    user=user,
                    interest_area=interest_data['interest_area'],
                    priority_level=interest_data['priority_level']
                )
            
            # Update profile completion
            user.update_profile_completion()
            
            return Response({
                'message': 'Step 3 completed',
                'interests': UserInterestSerializer(
                    user.user_interests.all(), 
                    many=True
                ).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingStep4View(generics.CreateAPIView):
    """
    Step 4: Current skills
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OnboardingStep4Serializer
    
    def create(self, request, *args, **kwargs):
        from skills.models import Skill, SkillLevel, UserSkill
        
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            skills_data = serializer.validated_data['skills']
            
            # Process each skill
            created_skills = []
            for skill_data in skills_data:
                skill_name = skill_data['skill_name'].strip()
                level_name = skill_data['level'].lower()
                
                # Get or create skill
                skill, _ = Skill.objects.get_or_create(
                    name__iexact=skill_name,
                    defaults={'name': skill_name, 'category': 'other'}
                )
                
                # Get skill level
                try:
                    skill_level = SkillLevel.objects.get(name__iexact=level_name)
                except SkillLevel.DoesNotExist:
                    skill_level = SkillLevel.objects.filter(level_order=2).first()
                
                # Create or update UserSkill
                user_skill, created = UserSkill.objects.update_or_create(
                    user=user,
                    skill=skill,
                    defaults={
                        'level': skill_level,
                        'status': 'learned',
                        'self_assessed': True
                    }
                )
                created_skills.append(user_skill)
            
            # Update profile completion
            user.update_profile_completion()
            
            return Response({
                'message': f'Step 4 completed. Added {len(created_skills)} skills.',
                'skills_count': len(created_skills)
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingStep5View(generics.CreateAPIView):
    """
    Step 5: Career goals and complete onboarding
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OnboardingStep5Serializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            target_role_id = serializer.validated_data['target_role_id']
            
            # Get the target role
            target_role = Role.objects.get(id=target_role_id)
            
            # Perform skill gap analysis
            analyzer = SkillGapAnalyzer()
            gap_analysis = analyzer.analyze_user_for_role(user, target_role)
            
            # Mark onboarding as complete
            user.onboarding_method = 'questionnaire'
            user.save(update_fields=['onboarding_method'])
            
            # Create notification
            UserNotification.create_notification(
                user=user,
                notification_type='system',
                title='Welcome to SkillBridge!',
                message=f'Your profile is set up. We found {gap_analysis["missing_skills_count"]} skills to learn for {target_role.title}.',
                link_url='/dashboard'
            )
            
            return Response({
                'message': 'Onboarding completed!',
                'onboarding_method': 'questionnaire',
                'gap_analysis': gap_analysis
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteOnboardingView(generics.CreateAPIView):
    """
    Complete all onboarding steps at once
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompleteOnboardingSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        from skills.models import Skill, SkillLevel, UserSkill
        
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            data = serializer.validated_data
            
            # Step 2: Professional background
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.current_role = data.get('current_role', '')
            profile.experience_level = data['experience_level']
            profile.preferred_work_type = data['preferred_work_type']
            profile.availability_status = data['availability_status']
            profile.save()
            
            # Step 3: Interests
            user.user_interests.all().delete()
            for interest_data in data['interests']:
                UserInterest.objects.create(
                    user=user,
                    interest_area=interest_data['interest_area'],
                    priority_level=interest_data['priority_level']
                )
            
            # Step 4: Skills
            for skill_data in data['skills']:
                skill_name = skill_data['skill_name'].strip()
                level_name = skill_data['level'].lower()
                
                skill, _ = Skill.objects.get_or_create(
                    name__iexact=skill_name,
                    defaults={'name': skill_name, 'category': 'other'}
                )
                
                try:
                    skill_level = SkillLevel.objects.get(name__iexact=level_name)
                except SkillLevel.DoesNotExist:
                    skill_level = SkillLevel.objects.filter(level_order=2).first()
                
                UserSkill.objects.update_or_create(
                    user=user,
                    skill=skill,
                    defaults={
                        'level': skill_level,
                        'status': 'learned',
                        'self_assessed': True
                    }
                )
            
            # Step 5: Target role
            target_role = Role.objects.get(id=data['target_role_id'])
            
            # Perform gap analysis
            analyzer = SkillGapAnalyzer()
            gap_analysis = analyzer.analyze_user_for_role(user, target_role)
            
            # Mark onboarding complete
            user.onboarding_method = 'questionnaire'
            user.update_profile_completion()
            user.save(update_fields=['onboarding_method'])
            
            # Create notification
            UserNotification.create_notification(
                user=user,
                notification_type='system',
                title='Welcome to SkillBridge!',
                message=f'Your profile is set up. Ready to start learning!',
                link_url='/dashboard'
            )
            
            return Response({
                'message': 'Onboarding completed successfully!',
                'onboarding_method': 'questionnaire',
                'profile_completion': user.profile_completion_percentage,
                'gap_analysis': gap_analysis
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)