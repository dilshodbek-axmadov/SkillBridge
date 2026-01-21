"""
Views for Chatbot app with Groq AI integration
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionListSerializer, ChatSessionDetailSerializer, ChatSessionCreateSerializer,
    ChatMessageSerializer, ChatMessageCreateSerializer, ChatMessageResponseSerializer,
    CareerQuestionsResponseSerializer, CareerAnswersSerializer, CareerAdviceResponseSerializer,
    CareerAdviceRequestSerializer, ChatHistoryRequestSerializer, ChatHistoryResponseSerializer,
    SessionEndSerializer, SessionEndResponseSerializer, QuickActionsResponseSerializer
)
from .services import ChatbotService, ConversationManager


# ============== Chat Session ViewSet ==============

class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat sessions

    Endpoints:
    - GET /api/chatbot/sessions/ - List user's chat sessions
    - POST /api/chatbot/sessions/ - Start new chat session
    - GET /api/chatbot/sessions/{id}/ - Get session details with messages
    - DELETE /api/chatbot/sessions/{id}/ - Delete a session
    - POST /api/chatbot/sessions/{id}/end/ - End a chat session
    - GET /api/chatbot/sessions/active/ - Get current active session
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by('-session_start')

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        elif self.action == 'create':
            return ChatSessionCreateSerializer
        return ChatSessionDetailSerializer

    def create(self, request, *args, **kwargs):
        """Start a new chat session"""
        serializer = ChatSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = ConversationManager.start_session(request.user)

        return Response({
            'message': 'New chat session started',
            'session': result
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a chat session"""
        result = ConversationManager.end_session(pk, request.user)

        if result is None:
            return Response(
                {'detail': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(SessionEndResponseSerializer(result).data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get current active session"""
        session = ChatSession.objects.filter(
            user=request.user, is_active=True
        ).first()

        if not session:
            return Response(
                {'detail': 'No active session found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(ChatSessionDetailSerializer(session).data)


# ============== Chat Message View ==============

class SendMessageView(APIView):
    """
    Send a message to the chatbot

    POST /api/chatbot/message/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']

        chatbot = ChatbotService()
        result = chatbot.send_message(request.user, message)

        return Response(
            ChatMessageResponseSerializer(result).data,
            status=status.HTTP_200_OK
        )


# ============== Chat History View ==============

class ChatHistoryView(APIView):
    """
    Get chat history

    GET /api/chatbot/history/
    GET /api/chatbot/history/?session_id={id}&limit={limit}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        limit = int(request.query_params.get('limit', 50))

        if session_id:
            session_id = int(session_id)

        messages = ConversationManager.get_chat_history(
            request.user,
            session_id=session_id,
            limit=limit
        )

        if messages is None:
            return Response(
                {'detail': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'count': len(messages),
            'messages': messages
        })


# ============== Career Questions ViewSet ==============

class CareerQuestionsViewSet(viewsets.ViewSet):
    """
    ViewSet for career discovery questions

    Endpoints:
    - GET /api/chatbot/career/questions/ - Get career questions
    - POST /api/chatbot/career/submit-answers/ - Submit answers and get advice
    - POST /api/chatbot/career/advice/ - Get personalized career advice
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def questions(self, request):
        """Get career discovery questions"""
        chatbot = ChatbotService()
        result = chatbot.get_career_questions(request.user)

        return Response(CareerQuestionsResponseSerializer(result).data)

    @action(detail=False, methods=['post'], url_path='submit-answers')
    def submit_answers(self, request):
        """Submit career questionnaire answers"""
        serializer = CareerAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = serializer.validated_data['answers']

        chatbot = ChatbotService()
        result = chatbot.process_career_answers(request.user, answers)

        return Response(CareerAdviceResponseSerializer(result).data)

    @action(detail=False, methods=['post'])
    def advice(self, request):
        """Get personalized career advice"""
        serializer = CareerAdviceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic = serializer.validated_data.get('topic')

        chatbot = ChatbotService()
        result = chatbot.get_career_advice(request.user, topic)

        return Response(ChatMessageResponseSerializer(result).data)


# ============== Quick Actions View ==============

class QuickActionsView(APIView):
    """
    Get quick action buttons for chatbot UI

    GET /api/chatbot/quick-actions/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Check user state to personalize quick actions
        from skills.models import UserSkill

        user_skills_count = UserSkill.objects.filter(
            user=request.user, status='learned'
        ).count()

        if user_skills_count == 0:
            # New user actions
            actions = [
                {
                    "id": "get_started",
                    "label": "Get Started",
                    "prompt": "I'm new to IT and want to start my career. Where should I begin?",
                    "icon": "rocket"
                },
                {
                    "id": "explore_careers",
                    "label": "Explore IT Careers",
                    "prompt": "What are the most in-demand IT careers in Uzbekistan right now?",
                    "icon": "briefcase"
                },
                {
                    "id": "learn_programming",
                    "label": "Learn Programming",
                    "prompt": "I want to learn programming. Which language should I start with?",
                    "icon": "code"
                },
                {
                    "id": "market_trends",
                    "label": "Market Trends",
                    "prompt": "What skills are most in demand in the IT job market?",
                    "icon": "trending-up"
                }
            ]
        else:
            # Returning user actions
            actions = [
                {
                    "id": "skill_gap",
                    "label": "Analyze Skills",
                    "prompt": "Analyze my current skills and tell me what I should learn next",
                    "icon": "target"
                },
                {
                    "id": "career_match",
                    "label": "Career Match",
                    "prompt": "Based on my skills, what career roles am I best suited for?",
                    "icon": "users"
                },
                {
                    "id": "job_search",
                    "label": "Find Jobs",
                    "prompt": "Show me job opportunities that match my current skills",
                    "icon": "search"
                },
                {
                    "id": "learning_path",
                    "label": "Learning Path",
                    "prompt": "Create a learning roadmap for me to reach my career goals",
                    "icon": "map"
                },
                {
                    "id": "salary_info",
                    "label": "Salary Info",
                    "prompt": "What salary can I expect based on my current skills?",
                    "icon": "dollar-sign"
                }
            ]

        return Response(QuickActionsResponseSerializer({'actions': actions}).data)


# ============== Chatbot Stats View ==============

class ChatbotStatsView(APIView):
    """
    Get chatbot usage statistics for current user

    GET /api/chatbot/stats/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)
        total_sessions = sessions.count()
        active_sessions = sessions.filter(is_active=True).count()

        total_messages = ChatMessage.objects.filter(
            session__user=request.user
        ).count()

        user_messages = ChatMessage.objects.filter(
            session__user=request.user,
            sender_type='user'
        ).count()

        bot_messages = ChatMessage.objects.filter(
            session__user=request.user,
            sender_type='bot'
        ).count()

        # Get recent session
        recent_session = sessions.first()

        return Response({
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_messages': total_messages,
            'user_messages': user_messages,
            'bot_messages': bot_messages,
            'recent_session': ChatSessionListSerializer(recent_session).data if recent_session else None
        })


# ============== Suggested Questions View ==============

class SuggestedQuestionsView(APIView):
    """
    Get AI-suggested questions based on user context

    GET /api/chatbot/suggestions/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from skills.models import UserSkill
        from career.models import UserRecommendedRole

        user = request.user
        suggestions = []

        # Check user's skills
        learned_skills = UserSkill.objects.filter(
            user=user, status='learned'
        ).select_related('skill')[:5]

        in_progress_skills = UserSkill.objects.filter(
            user=user, status='in_progress'
        ).select_related('skill')[:3]

        # Skill-based suggestions
        if learned_skills:
            skill_names = [us.skill.name for us in learned_skills[:3]]
            suggestions.append({
                "category": "Skills",
                "questions": [
                    f"What jobs can I get with {', '.join(skill_names)}?",
                    "What skills should I learn next to advance my career?",
                    "How do my skills compare to industry requirements?"
                ]
            })

        if in_progress_skills:
            skill = in_progress_skills[0].skill.name
            suggestions.append({
                "category": "Learning",
                "questions": [
                    f"What are the best resources to learn {skill}?",
                    f"How long will it take to master {skill}?",
                    "Can you create a study plan for me?"
                ]
            })

        # Career suggestions
        recommendations = UserRecommendedRole.objects.filter(
            user=user, is_active=True
        ).select_related('role')[:3]

        if recommendations:
            role = recommendations[0].role.title
            suggestions.append({
                "category": "Career",
                "questions": [
                    f"What's the career path for a {role}?",
                    f"What's the salary range for {role} in Uzbekistan?",
                    "How can I improve my chances of getting hired?"
                ]
            })

        # Default suggestions for new users
        if not suggestions:
            suggestions = [
                {
                    "category": "Getting Started",
                    "questions": [
                        "What IT career path should I choose?",
                        "Which programming language is best for beginners?",
                        "How do I start a career in tech?"
                    ]
                },
                {
                    "category": "Market Insights",
                    "questions": [
                        "What are the most in-demand tech skills?",
                        "What's the IT job market like in Uzbekistan?",
                        "Which tech companies are hiring?"
                    ]
                }
            ]

        return Response({'suggestions': suggestions})
