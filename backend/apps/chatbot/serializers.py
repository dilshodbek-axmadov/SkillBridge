"""
Chatbot App Serializers
=======================
Serializers for chatbot conversations and messages.
"""

from rest_framework import serializers
from apps.chatbot.models import ChatbotConversation, ChatbotMessage


class ChatbotMessageSerializer(serializers.ModelSerializer):
    """Chatbot message serializer."""

    class Meta:
        model = ChatbotMessage
        fields = [
            'message_id',
            'sender_type',
            'message_text',
            'context_data',
            'timestamp',
        ]
        read_only_fields = ['message_id', 'timestamp']


class ChatbotConversationSerializer(serializers.ModelSerializer):
    """Chatbot conversation serializer."""

    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatbotConversation
        fields = [
            'conversation_id',
            'context_type',
            'is_active',
            'started_at',
            'ended_at',
            'message_count',
        ]
        read_only_fields = ['conversation_id', 'started_at', 'ended_at']

    def get_message_count(self, obj):
        return obj.get_message_count()


class ChatbotConversationDetailSerializer(serializers.ModelSerializer):
    """Detailed conversation serializer with messages."""

    messages = ChatbotMessageSerializer(source='chatbot_messages', many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatbotConversation
        fields = [
            'conversation_id',
            'context_type',
            'is_active',
            'started_at',
            'ended_at',
            'message_count',
            'messages',
        ]

    def get_message_count(self, obj):
        return obj.get_message_count()


# Request Serializers

class StartConversationRequestSerializer(serializers.Serializer):
    """Request serializer for starting a conversation."""

    context_type = serializers.ChoiceField(
        choices=['onboarding', 'roadmap', 'career', 'help'],
        default='help',
        help_text="Type of conversation context."
    )
    initial_message = serializers.CharField(
        required=False,
        max_length=2000,
        help_text="Optional initial message to send."
    )


class SendMessageRequestSerializer(serializers.Serializer):
    """Request serializer for sending a message."""

    message = serializers.CharField(
        max_length=2000,
        help_text="Message text to send."
    )
    language = serializers.ChoiceField(
        choices=['en', 'ru', 'uz'],
        default='en',
        required=False,
        help_text="Response language."
    )


# Response Serializers

class StartConversationResponseSerializer(serializers.Serializer):
    """Response serializer for starting a conversation."""

    conversation_id = serializers.IntegerField()
    context_type = serializers.CharField()
    greeting = serializers.CharField()
    started_at = serializers.CharField()
    initial_response = serializers.DictField(required=False)


class SendMessageResponseSerializer(serializers.Serializer):
    """Response serializer for sending a message."""

    success = serializers.BooleanField()
    conversation_id = serializers.IntegerField(required=False)
    message_id = serializers.IntegerField(required=False)
    response = serializers.CharField(required=False)
    response_type = serializers.CharField(required=False)
    context_data = serializers.DictField(required=False)
    timestamp = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
