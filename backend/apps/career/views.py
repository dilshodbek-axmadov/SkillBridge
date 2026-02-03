"""
Career Views
============
backend/apps/career/views.py

API endpoints for career assessment and recommendations.
"""

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone

from .models import ITRole, AssessmentQuestion, UserAssessment, CareerRecommendation
from .serializers import (
    ITRoleSerializer,
    AssessmentQuestionSerializer,
    SubmitAssessmentSerializer,
    UserAssessmentSerializer,
    CareerRecommendationSerializer,
    SelectRoleSerializer
)
from .utils.career_matcher import CareerMatcher


class GetQuestionsView(APIView):
    """
    Get assessment questions.
    
    GET /api/career/questions/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        questions = AssessmentQuestion.objects.filter(is_active=True).order_by('order')
        serializer = AssessmentQuestionSerializer(questions, many=True)
        
        return Response({
            'questions': serializer.data,
            'total': questions.count()
        })


class SubmitAssessmentView(APIView):
    """
    Submit assessment and get recommendations.
    
    POST /api/career/assessment/
    
    Body:
    {
        "responses": {
            "1": 0,  // question_id: option_index
            "2": 2,
            ...
        }
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Validate
        serializer = SubmitAssessmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        responses = serializer.validated_data['responses']
        
        # Match roles
        matcher = CareerMatcher()
        matches = matcher.match_user(responses)
        
        # Get or create assessment
        assessment, created = UserAssessment.objects.get_or_create(
            user=request.user,
            defaults={'responses': responses}
        )
        
        if not created:
            # Update existing
            assessment.responses = responses
        
        # Save user scores
        if matches:
            first_match = matches[0]
            user_scores = first_match['user_scores']
            user_work_style = first_match['user_work_style']
            
            assessment.problem_solving_score = user_scores.get('problem_solving', 0.0)
            assessment.creativity_score = user_scores.get('creativity', 0.0)
            assessment.data_analysis_score = user_scores.get('data_analysis', 0.0)
            assessment.technical_depth_score = user_scores.get('technical_depth', 0.0)
            assessment.communication_score = user_scores.get('communication', 0.0)
            assessment.visual_design_score = user_scores.get('visual_design', 0.0)
            
            assessment.prefers_independent = user_work_style.get('independent')
            assessment.prefers_collaborative = user_work_style.get('collaborative')
            assessment.prefers_fast_paced = user_work_style.get('fast_paced')
        
        assessment.completed = True
        assessment.completed_at = timezone.now()
        assessment.save()
        
        # Delete old recommendations
        CareerRecommendation.objects.filter(user=request.user).delete()
        
        # Save new recommendations
        recommendations = []
        for match in matches:
            rec = CareerRecommendation.objects.create(
                user=request.user,
                role=match['role'],
                match_score=match['match_score'],
                rank=match['rank'],
                reasoning=match.get('reasoning', '')
            )
            recommendations.append(rec)
        
        # Serialize response
        rec_serializer = CareerRecommendationSerializer(recommendations, many=True)
        
        return Response({
            'assessment_completed': True,
            'recommendations': rec_serializer.data
        }, status=201)


class GetRecommendationsView(APIView):
    """
    Get user's latest recommendations.
    
    GET /api/career/recommendations/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        recommendations = CareerRecommendation.objects.filter(
            user=request.user
        ).select_related('role').order_by('rank')
        
        if not recommendations.exists():
            return Response({
                'message': 'No recommendations yet. Complete assessment first.',
                'recommendations': []
            })
        
        serializer = CareerRecommendationSerializer(recommendations, many=True)
        
        return Response({
            'recommendations': serializer.data
        })


class SelectRoleView(APIView):
    """
    Select a recommended role.
    
    POST /api/career/select-role/
    
    Body:
    {
        "recommendation_id": 123
    }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = SelectRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        recommendation_id = serializer.validated_data['recommendation_id']
        
        # Get recommendation
        try:
            recommendation = CareerRecommendation.objects.get(
                id=recommendation_id,
                user=request.user
            )
        except CareerRecommendation.DoesNotExist:
            return Response({
                'error': 'Recommendation not found'
            }, status=404)
        
        # Mark as selected
        recommendation.user_selected = True
        recommendation.save()
        
        # Update user profile
        profile = request.user.profile
        profile.desired_role = recommendation.role.name
        profile.save()
        
        return Response({
            'message': f'Selected {recommendation.role.name} as your career path',
            'role': ITRoleSerializer(recommendation.role).data
        })


class GetAssessmentStatusView(APIView):
    """
    Check if user has completed assessment.
    
    GET /api/career/status/
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            assessment = UserAssessment.objects.get(user=request.user)
            
            return Response({
                'has_assessment': True,
                'completed': assessment.completed,
                'completed_at': assessment.completed_at,
                'has_recommendations': CareerRecommendation.objects.filter(
                    user=request.user
                ).exists()
            })
        
        except UserAssessment.DoesNotExist:
            return Response({
                'has_assessment': False,
                'completed': False,
                'has_recommendations': False
            })


class GetAllRolesView(APIView):
    """
    Get all available IT roles.
    
    GET /api/career/roles/
    """
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        roles = ITRole.objects.filter(is_active=True)
        serializer = ITRoleSerializer(roles, many=True)
        
        return Response({
            'roles': serializer.data,
            'count': roles.count()
        })