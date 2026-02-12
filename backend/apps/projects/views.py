"""
Projects App Views
==================
API views for project ideas and user projects.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.projects.services import ProjectIdeaGenerator
from apps.projects.serializers import (
    GenerateProjectsRequestSerializer,
    UpdateProjectStatusRequestSerializer,
)


class GenerateProjectsView(APIView):
    """
    POST /api/v1/projects/generate/

    Generate AI-powered project ideas based on:
    - Target role
    - Experience/difficulty level
    - Optional skill focus
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateProjectsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        generator = ProjectIdeaGenerator(user=request.user)
        result = generator.generate_projects(
            target_role=serializer.validated_data['target_role'],
            difficulty_level=serializer.validated_data.get('difficulty_level', 'beginner'),
            skill_ids=serializer.validated_data.get('skill_ids'),
            language=serializer.validated_data.get('language', 'en'),
            count=serializer.validated_data.get('count', 3),
        )

        if result.get('success'):
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class RoleProjectsView(APIView):
    """
    GET /api/v1/projects/role/{role_name}/

    Get existing project ideas for a specific role.

    Query params:
    - difficulty_level: filter by difficulty
    - limit: max results
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, role_name):
        difficulty = request.query_params.get('difficulty_level')
        limit = int(request.query_params.get('limit', 10))

        generator = ProjectIdeaGenerator(user=request.user)
        projects = generator.get_projects_for_role(
            role_name=role_name,
            difficulty_level=difficulty,
            limit=limit
        )

        return Response({
            'role': role_name,
            'count': len(projects),
            'projects': projects,
        })


class ProjectSkillsView(APIView):
    """
    GET /api/v1/projects/{project_id}/skills/

    Get skills required for a specific project.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        generator = ProjectIdeaGenerator(user=request.user)
        result = generator.get_project_skills(project_id)

        if not result:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)


class StartProjectView(APIView):
    """
    POST /api/v1/projects/{project_id}/start/

    Start working on a project (adds to user's projects).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        generator = ProjectIdeaGenerator(user=request.user)
        result = generator.start_project(project_id)

        if not result:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        status_code = status.HTTP_201_CREATED if result.get('created') else status.HTTP_200_OK
        return Response(result, status=status_code)


class UpdateProjectStatusView(APIView):
    """
    PUT /api/v1/projects/{project_id}/status/

    Update user's project status.

    Request body:
    - status: planned/in_progress/completed
    - github_url: optional
    - live_demo_url: optional
    - notes: optional
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, project_id):
        serializer = UpdateProjectStatusRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        generator = ProjectIdeaGenerator(user=request.user)
        result = generator.update_project_status(
            project_id=project_id,
            status=serializer.validated_data['status'],
            github_url=serializer.validated_data.get('github_url'),
            live_demo_url=serializer.validated_data.get('live_demo_url'),
            notes=serializer.validated_data.get('notes'),
        )

        if not result:
            return Response(
                {'error': 'User project not found. Start the project first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)


class UserProjectsView(APIView):
    """
    GET /api/v1/projects/my/

    Get all projects for the authenticated user.

    Query params:
    - status: filter by status (planned/in_progress/completed)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')

        generator = ProjectIdeaGenerator(user=request.user)
        projects = generator.get_user_projects(status=status_filter)

        return Response({
            'count': len(projects),
            'projects': projects,
        })


class AllProjectsView(APIView):
    """
    GET /api/v1/projects/all/

    List all project ideas with optional filters.

    Query params:
    - difficulty_level: filter by difficulty
    - search: search title/description
    - limit: max results (default 50)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        difficulty = request.query_params.get('difficulty_level')
        search = request.query_params.get('search', '')
        limit = int(request.query_params.get('limit', 50))

        generator = ProjectIdeaGenerator(user=request.user)
        projects = generator.get_all_projects(
            difficulty_level=difficulty,
            search=search,
            limit=limit,
        )

        return Response({
            'count': len(projects),
            'projects': projects,
        })


class ProjectDetailView(APIView):
    """
    GET /api/v1/projects/{project_id}/

    Get project details with skills.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        generator = ProjectIdeaGenerator(user=request.user)
        result = generator.get_project_skills(project_id)

        if not result:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)
