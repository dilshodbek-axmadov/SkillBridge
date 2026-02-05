"""
Chatbot App URLs
================
API endpoints for chatbot conversations.

Endpoints:
- POST /api/v1/chatbot/conversations/start/         - Start new conversation
- GET  /api/v1/chatbot/conversations/               - List user's conversations
- POST /api/v1/chatbot/conversations/{id}/message/  - Send message
- GET  /api/v1/chatbot/conversations/{id}/history/  - Get conversation history
- POST /api/v1/chatbot/conversations/{id}/end/      - End conversation
- POST /api/v1/chatbot/quick/                       - Quick one-off chat
"""

from django.urls import path
from apps.chatbot import views

app_name = 'chatbot'

urlpatterns = [
    # Conversation management
    path('conversations/start/', views.StartConversationView.as_view(), name='start_conversation'),
    path('conversations/', views.UserConversationsView.as_view(), name='user_conversations'),

    # Conversation actions
    path('conversations/<int:conv_id>/message/', views.SendMessageView.as_view(), name='send_message'),
    path('conversations/<int:conv_id>/history/', views.ConversationHistoryView.as_view(), name='conversation_history'),
    path('conversations/<int:conv_id>/end/', views.EndConversationView.as_view(), name='end_conversation'),

    # Quick chat (no persistent conversation)
    path('quick/', views.QuickChatView.as_view(), name='quick_chat'),
]
