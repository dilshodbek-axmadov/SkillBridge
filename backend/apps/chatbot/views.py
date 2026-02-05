"""
Chatbot App Views
=================
API views for chatbot conversations.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.chatbot.services import ChatbotService
from apps.chatbot.serializers import (
    StartConversationRequestSerializer,
    SendMessageRequestSerializer,
)


class StartConversationView(APIView):
    """
    POST /api/v1/chatbot/conversations/start/

    Start a new chatbot conversation.

    Request body:
    - context_type: Type of conversation (onboarding, roadmap, career, help)
    - initial_message: Optional initial message to send
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StartConversationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ChatbotService(user=request.user)
        result = service.start_conversation(
            context_type=serializer.validated_data.get('context_type', 'help'),
            initial_message=serializer.validated_data.get('initial_message'),
        )

        return Response(result, status=status.HTTP_201_CREATED)


class SendMessageView(APIView):
    """
    POST /api/v1/chatbot/conversations/{conv_id}/message/

    Send a message in a conversation and get bot response.

    Request body:
    - message: Message text to send
    - language: Response language (en, ru, uz)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, conv_id):
        serializer = SendMessageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ChatbotService(user=request.user)
        result = service.send_message(
            conversation_id=conv_id,
            message=serializer.validated_data['message'],
            language=serializer.validated_data.get('language', 'en'),
        )

        if result.get('success'):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class ConversationHistoryView(APIView):
    """
    GET /api/v1/chatbot/conversations/{conv_id}/history/

    Get conversation history with all messages.

    Query params:
    - limit: Max number of messages to return (default: 50)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, conv_id):
        limit = int(request.query_params.get('limit', 50))

        service = ChatbotService(user=request.user)
        result = service.get_conversation_history(
            conversation_id=conv_id,
            limit=limit
        )

        if not result:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)


class EndConversationView(APIView):
    """
    POST /api/v1/chatbot/conversations/{conv_id}/end/

    End/close a conversation.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, conv_id):
        service = ChatbotService(user=request.user)
        success = service.end_conversation(conv_id)

        if success:
            return Response({
                'success': True,
                'conversation_id': conv_id,
                'message': 'Conversation ended successfully',
            })
        else:
            return Response(
                {'error': 'Conversation not found or already ended'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserConversationsView(APIView):
    """
    GET /api/v1/chatbot/conversations/

    Get list of user's conversations.

    Query params:
    - active_only: If true, only return active conversations
    - limit: Max number of conversations (default: 20)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        limit = int(request.query_params.get('limit', 20))

        service = ChatbotService(user=request.user)
        conversations = service.get_user_conversations(
            active_only=active_only,
            limit=limit
        )

        return Response({
            'count': len(conversations),
            'conversations': conversations,
        })


class QuickChatView(APIView):
    """
    POST /api/v1/chatbot/quick/

    Quick one-off chat without conversation context.
    Starts a conversation, sends message, and returns response.

    Request body:
    - message: Message text
    - context_type: Context type (default: help)
    - language: Response language (default: en)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message')
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        context_type = request.data.get('context_type', 'help')
        language = request.data.get('language', 'en')

        service = ChatbotService(user=request.user)

        # Start conversation
        result = service.start_conversation(
            context_type=context_type,
        )

        # Send the message with language preference
        message_result = service.send_message(
            conversation_id=result['conversation_id'],
            message=message,
            language=language
        )
        result['initial_response'] = message_result

        # Extract just the response part
        if 'initial_response' in result:
            return Response({
                'conversation_id': result['conversation_id'],
                'response': result['initial_response'].get('response'),
                'response_type': result['initial_response'].get('response_type'),
            })

        return Response(result, status=status.HTTP_201_CREATED)
