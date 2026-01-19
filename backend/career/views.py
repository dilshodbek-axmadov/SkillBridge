"""
Views for Career API
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from career.models import (
    Role, RoleRequiredSkill, UserRecommendedRole, SkillGapAnalysis
)
from career.serializers import (
    RoleListSerializer, RoleDetailSerializer,
    UserRecommendedRoleSerializer, SkillGapAnalysisSerializer,
    PerformGapAnalysisSerializer, SelectTargetRoleSerializer,
    RoleRecommendationSerializer
)
from career.services import SkillGapAnalyzer, RoadmapGenerator
from notifications.models import UserNotification


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for IT roles
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['category']
    ordering_fields = ['title', 'demand_score', 'growth_potential']
    ordering = ['-demand_score']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoleDetailSerializer
        return RoleListSerializer
    
    def get_queryset(self):
        queryset = Role.objects.select_related('category').prefetch_related(
            'role_required_skills__skill',
            'role_required_skills__minimum_level'
        )
        
        # Filter by minimum demand score
        min_demand = self.request.query_params.get('min_demand')
        if min_demand:
            try:
                queryset = queryset.filter(demand_score__gte=float(min_demand))
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular/in-demand roles"""
        limit = int(request.query_params.get('limit', 10))
        roles = self.get_queryset().order_by('-demand_score')[:limit]
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_growth(self, request):
        """Get roles with high growth potential"""
        limit = int(request.query_params.get('limit', 10))
        roles = self.get_queryset().order_by('-growth_potential')[:limit]
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def analyze(self, request, pk=None):
        """Perform skill gap analysis for this role"""
        role = self.get_object()
        user = request.user
        
        analyzer = SkillGapAnalyzer()
        gap_analysis_data = analyzer.analyze_user_for_role(user, role)
        
        # Get the created gap analysis object
        gap_analysis = SkillGapAnalysis.objects.get(
            id=gap_analysis_data['gap_analysis_id']
        )
        
        serializer = SkillGapAnalysisSerializer(gap_analysis)
        return Response({
            'role': RoleDetailSerializer(role).data,
            'gap_analysis': serializer.data
        })


class RecommendationViewSet(viewsets.ViewSet):
    """
    ViewSet for career recommendations
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get role recommendations for user"""
        user = request.user
        
        analyzer = SkillGapAnalyzer()
        recommendations = analyzer.recommend_roles_for_user(user, top_n=10)
        
        serializer = RoleRecommendationSerializer(recommendations, many=True)
        return Response({
            'count': len(recommendations),
            'recommendations': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def analyze_role(self, request):
        """Perform gap analysis for a specific role"""
        serializer = PerformGapAnalysisSerializer(data=request.data)
        
        if serializer.is_valid():
            role_id = serializer.validated_data['role_id']
            role = Role.objects.get(id=role_id)
            user = request.user
            
            analyzer = SkillGapAnalyzer()
            gap_analysis_data = analyzer.analyze_user_for_role(user, role)
            
            # Get the created gap analysis object
            gap_analysis = SkillGapAnalysis.objects.get(
                id=gap_analysis_data['gap_analysis_id']
            )
            
            result_serializer = SkillGapAnalysisSerializer(gap_analysis)
            return Response({
                'message': 'Gap analysis completed',
                'gap_analysis': result_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def select_target_role(self, request):
        """Select a target role and generate roadmap"""
        serializer = SelectTargetRoleSerializer(data=request.data)
        
        if serializer.is_valid():
            role_id = serializer.validated_data['role_id']
            role = Role.objects.get(id=role_id)
            user = request.user
            
            # Perform gap analysis
            analyzer = SkillGapAnalyzer()
            gap_analysis_data = analyzer.analyze_user_for_role(user, role)
            
            # Generate roadmap
            generator = RoadmapGenerator()
            roadmap = generator.generate_roadmap(user, role)
            
            # Create notification
            UserNotification.create_notification(
                user=user,
                notification_type='roadmap_update',
                title=f'Your {role.title} Roadmap is Ready!',
                message=f'We created a personalized learning roadmap with {roadmap.roadmap_items.count()} skills to learn.',
                link_url=f'/roadmap/{roadmap.id}'
            )
            
            return Response({
                'message': f'Target role selected: {role.title}',
                'role': RoleDetailSerializer(role).data,
                'gap_analysis': gap_analysis_data,
                'roadmap_id': roadmap.id,
                'roadmap_items_count': roadmap.roadmap_items.count(),
                'estimated_completion_weeks': gap_analysis_data['estimated_learning_weeks']
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRecommendedRoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user's recommended roles
    """
    serializer_class = UserRecommendedRoleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserRecommendedRole.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('role', 'role__category').order_by('-match_percentage')
    
    @action(detail=False, methods=['get'])
    def top(self, request):
        """Get top 5 recommended roles"""
        top_roles = self.get_queryset()[:5]
        serializer = self.get_serializer(top_roles, many=True)
        return Response(serializer.data)


class GapAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for skill gap analyses
    """
    serializer_class = SkillGapAnalysisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SkillGapAnalysis.objects.filter(
            user=self.request.user
        ).select_related('role').prefetch_related(
            'missing_skills__skill',
            'missing_skills__required_level'
        ).order_by('-analysis_date')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest gap analysis"""
        latest = self.get_queryset().first()
        
        if not latest:
            return Response({
                'message': 'No gap analysis found. Please select a target role first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(latest)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """Refresh/recalculate gap analysis"""
        gap_analysis = self.get_object()
        
        analyzer = SkillGapAnalyzer()
        new_gap_data = analyzer.analyze_user_for_role(
            request.user,
            gap_analysis.role
        )
        
        # Get the updated gap analysis
        updated_gap = SkillGapAnalysis.objects.get(
            id=new_gap_data['gap_analysis_id']
        )
        
        serializer = self.get_serializer(updated_gap)
        return Response({
            'message': 'Gap analysis refreshed',
            'gap_analysis': serializer.data
        })