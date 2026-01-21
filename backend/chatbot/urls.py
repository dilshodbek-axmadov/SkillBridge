"""
URL patterns for Chatbot app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatSessionViewSet, SendMessageView, ChatHistoryView,
    CareerQuestionsViewSet, QuickActionsView, ChatbotStatsView,
    SuggestedQuestionsView
)

router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='chat-session')
router.register(r'career', CareerQuestionsViewSet, basename='career-questions')

urlpatterns = [
    # Send message to chatbot
    path('message/', SendMessageView.as_view(), name='send-message'),

    # Chat history
    path('history/', ChatHistoryView.as_view(), name='chat-history'),

    # Quick actions for UI
    path('quick-actions/', QuickActionsView.as_view(), name='quick-actions'),

    # Chatbot usage stats
    path('stats/', ChatbotStatsView.as_view(), name='chatbot-stats'),

    # AI-suggested questions
    path('suggestions/', SuggestedQuestionsView.as_view(), name='suggestions'),

    # Router URLs
    path('', include(router.urls)),
]
