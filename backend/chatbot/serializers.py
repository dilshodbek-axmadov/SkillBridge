"""
Serializers for Chatbot app
"""
from rest_framework import serializers
from .models import ChatSession, ChatMessage, ChatbotIntent, ChatbotContext


# ============== Chat Session Serializers ==============

class ChatSessionListSerializer(serializers.ModelSerializer):
    """Serializer for listing chat sessions"""
    message_count = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_start', 'session_end', 'is_active',
            'message_count', 'duration'
        ]

    def get_message_count(self, obj):
        return obj.get_message_count()

    def get_duration(self, obj):
        return obj.get_duration_display()


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer for chat session details with messages"""
    messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_start', 'session_end', 'is_active',
            'message_count', 'duration', 'messages'
        ]

    def get_messages(self, obj):
        messages = obj.chat_messages.order_by('timestamp')
        return ChatMessageSerializer(messages, many=True).data

    def get_message_count(self, obj):
        return obj.get_message_count()

    def get_duration(self, obj):
        return obj.get_duration_display()


class ChatSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new chat session"""
    close_existing = serializers.BooleanField(
        default=True,
        help_text="Close existing active sessions before creating new one"
    )


# ============== Chat Message Serializers ==============

class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender = serializers.CharField(source='sender_type')

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'session', 'sender', 'message_text', 'timestamp',
            'intent_detected', 'confidence_score'
        ]
        read_only_fields = ['id', 'timestamp', 'intent_detected', 'confidence_score']


class ChatMessageCreateSerializer(serializers.Serializer):
    """Serializer for sending a message to chatbot"""
    message = serializers.CharField(
        max_length=4000,
        help_text="The message to send to the chatbot"
    )
    session_id = serializers.IntegerField(
        required=False,
        help_text="Optional session ID. If not provided, uses active session or creates new one"
    )


class ChatMessageResponseSerializer(serializers.Serializer):
    """Serializer for chatbot response"""
    session_id = serializers.IntegerField()
    user_message = serializers.DictField()
    bot_response = serializers.DictField()


# ============== Career Questions Serializers ==============

class QuestionOptionSerializer(serializers.Serializer):
    """Serializer for question options"""
    value = serializers.CharField()
    label = serializers.CharField()


class CareerQuestionSerializer(serializers.Serializer):
    """Serializer for a career question"""
    id = serializers.CharField()
    question = serializers.CharField()
    type = serializers.ChoiceField(choices=['single_choice', 'multiple_choice', 'text'])
    options = QuestionOptionSerializer(many=True, required=False)


class CareerQuestionsResponseSerializer(serializers.Serializer):
    """Serializer for career questions response"""
    session_id = serializers.IntegerField()
    questions = CareerQuestionSerializer(many=True)
    user_state = serializers.DictField()


class CareerAnswersSerializer(serializers.Serializer):
    """Serializer for submitting career questionnaire answers"""
    answers = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dictionary of question_id: answer pairs"
    )


class CareerAdviceResponseSerializer(serializers.Serializer):
    """Serializer for career advice response"""
    session_id = serializers.IntegerField()
    answers_processed = serializers.DictField(required=False)
    advice = serializers.CharField()


# ============== Career Advice Serializers ==============

class CareerAdviceRequestSerializer(serializers.Serializer):
    """Serializer for career advice request"""
    topic = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Specific topic to get advice about (optional)"
    )


# ============== Chat History Serializers ==============

class ChatHistoryRequestSerializer(serializers.Serializer):
    """Serializer for chat history request"""
    session_id = serializers.IntegerField(
        required=False,
        help_text="Get history for specific session. If not provided, returns recent messages from all sessions"
    )
    limit = serializers.IntegerField(
        required=False,
        default=50,
        min_value=1,
        max_value=200,
        help_text="Maximum number of messages to return"
    )


class ChatHistoryItemSerializer(serializers.Serializer):
    """Serializer for a single chat history item"""
    id = serializers.IntegerField()
    session_id = serializers.IntegerField()
    sender = serializers.CharField()
    text = serializers.CharField()
    timestamp = serializers.DateTimeField()
    intent = serializers.CharField(allow_null=True)


class ChatHistoryResponseSerializer(serializers.Serializer):
    """Serializer for chat history response"""
    count = serializers.IntegerField()
    messages = ChatHistoryItemSerializer(many=True)


# ============== Chatbot Intent Serializers ==============

class ChatbotIntentSerializer(serializers.ModelSerializer):
    """Serializer for chatbot intents"""
    class Meta:
        model = ChatbotIntent
        fields = [
            'id', 'intent_name', 'description', 'response_template',
            'example_phrases', 'handler_function', 'is_active'
        ]
        read_only_fields = ['id']


# ============== Chatbot Context Serializers ==============

class ChatbotContextSerializer(serializers.ModelSerializer):
    """Serializer for chatbot context"""
    class Meta:
        model = ChatbotContext
        fields = ['id', 'session', 'context_key', 'context_value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============== Session End Serializers ==============

class SessionEndSerializer(serializers.Serializer):
    """Serializer for ending a session"""
    session_id = serializers.IntegerField(help_text="ID of the session to end")


class SessionEndResponseSerializer(serializers.Serializer):
    """Serializer for session end response"""
    session_id = serializers.IntegerField()
    ended_at = serializers.DateTimeField()
    duration = serializers.CharField()
    message_count = serializers.IntegerField()


# ============== Quick Actions Serializers ==============

class QuickActionSerializer(serializers.Serializer):
    """Serializer for quick action buttons"""
    id = serializers.CharField()
    label = serializers.CharField()
    prompt = serializers.CharField()
    icon = serializers.CharField(required=False)


class QuickActionsResponseSerializer(serializers.Serializer):
    """Serializer for quick actions list"""
    actions = QuickActionSerializer(many=True)
