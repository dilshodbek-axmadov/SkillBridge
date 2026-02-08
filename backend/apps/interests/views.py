"""
Interests App Views
===================
backend/apps/interests/views.py

API views for browsing interests and managing user interests.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Interest, UserInterest
from .serializers import (
    InterestSerializer,
    UserInterestSerializer,
    AddUserInterestSerializer,
    BulkAddInterestsSerializer,
    InterestCategorySerializer,
)


# ==================== BROWSING (Public) ====================

class GetAllInterestsView(APIView):
    """
    GET /api/v1/interests/browse/
    List all interests, optionally filtered by category.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='category', type=str, required=False,
                             description='Filter by category (tech, design, management, business, creative)'),
        ],
        responses={200: InterestSerializer(many=True)},
        tags=['Interests'],
    )
    def get(self, request):
        qs = Interest.objects.all()

        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        serializer = InterestSerializer(qs, many=True)
        return Response({
            'interests': serializer.data,
            'total': qs.count(),
        })


class SearchInterestsView(APIView):
    """
    GET /api/v1/interests/search/?q=...
    Search interests by name (en/ru/uz).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', type=str, required=True, description='Search query'),
        ],
        responses={200: InterestSerializer(many=True)},
        tags=['Interests'],
    )
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'interests': [], 'total': 0})

        qs = Interest.objects.filter(
            Q(name_en__icontains=q) |
            Q(name_ru__icontains=q) |
            Q(name_uz__icontains=q)
        )

        serializer = InterestSerializer(qs, many=True)
        return Response({
            'interests': serializer.data,
            'total': qs.count(),
        })


class GetInterestCategoriesView(APIView):
    """
    GET /api/v1/interests/categories/
    List all interest categories with counts.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: InterestCategorySerializer(many=True)},
        tags=['Interests'],
    )
    def get(self, request):
        categories = (
            Interest.objects
            .values('category')
            .annotate(count=Count('interest_id'))
            .order_by('category')
        )

        result = []
        category_labels = dict(Interest.CATEGORY_CHOICES)
        for cat in categories:
            result.append({
                'code': cat['category'],
                'name': str(category_labels.get(cat['category'], cat['category'])),
                'count': cat['count'],
            })

        return Response({'categories': result})


# ==================== USER INTERESTS (Authenticated) ====================

class GetMyInterestsView(APIView):
    """
    GET /api/v1/interests/my-interests/
    Get the current user's interests.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserInterestSerializer(many=True)},
        tags=['User Interests'],
    )
    def get(self, request):
        user_interests = (
            UserInterest.objects
            .filter(user=request.user)
            .select_related('interest')
        )
        serializer = UserInterestSerializer(user_interests, many=True)
        return Response({
            'interests': serializer.data,
            'total': user_interests.count(),
        })


class AddInterestView(APIView):
    """
    POST /api/v1/interests/add/
    Add a single interest for the current user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddUserInterestSerializer,
        responses={201: UserInterestSerializer},
        tags=['User Interests'],
    )
    def post(self, request):
        serializer = AddUserInterestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interest_id = serializer.validated_data['interest_id']

        if UserInterest.objects.filter(user=request.user, interest_id=interest_id).exists():
            return Response(
                {'error': 'You already have this interest.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_interest = UserInterest.objects.create(
            user=request.user,
            interest_id=interest_id,
        )

        return Response(
            UserInterestSerializer(user_interest).data,
            status=status.HTTP_201_CREATED,
        )


class BulkAddInterestsView(APIView):
    """
    POST /api/v1/interests/bulk-add/
    Add multiple interests at once for the current user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=BulkAddInterestsSerializer,
        tags=['User Interests'],
    )
    def post(self, request):
        serializer = BulkAddInterestsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interest_ids = serializer.validated_data['interest_ids']

        existing = set(
            UserInterest.objects
            .filter(user=request.user, interest_id__in=interest_ids)
            .values_list('interest_id', flat=True)
        )

        new_ids = [iid for iid in interest_ids if iid not in existing]

        created = UserInterest.objects.bulk_create([
            UserInterest(user=request.user, interest_id=iid)
            for iid in new_ids
        ])

        return Response({
            'added': len(created),
            'already_existed': len(existing),
            'total_interests': UserInterest.objects.filter(user=request.user).count(),
        }, status=status.HTTP_201_CREATED)


class DeleteInterestView(APIView):
    """
    DELETE /api/v1/interests/delete/<user_interest_id>/
    Remove an interest from the current user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User Interests'],
    )
    def delete(self, request, user_interest_id):
        try:
            user_interest = UserInterest.objects.get(
                user_interest_id=user_interest_id,
                user=request.user,
            )
        except UserInterest.DoesNotExist:
            return Response(
                {'error': 'Interest not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_interest.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
