"""
Chatbot session and message models
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class ChatSession(models.Model):
    """
    Chat session for a user
    Each session represents a conversation thread
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When session was closed"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this session still active?"
    )
    
    class Meta:
        db_table = 'chat_sessions'
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
        ordering = ['-session_start']
    
    def __str__(self):
        status = "Active" if self.is_active else "Closed"
        return f"{self.user.email} - Session {self.id} ({status})"
    
    def close_session(self):
        """Close this chat session"""
        self.is_active = False
        self.session_end = timezone.now()
        self.save(update_fields=['is_active', 'session_end'])
    
    def get_message_count(self):
        """Get total number of messages in this session"""
        return self.chat_messages.count()
    
    def get_duration(self):
        """Get session duration"""
        if self.session_end:
            delta = self.session_end - self.session_start
            return delta
        else:
            delta = timezone.now() - self.session_start
            return delta
    
    def get_duration_display(self):
        """Get human-readable duration"""
        duration = self.get_duration()
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "< 1m"


class ChatMessage(models.Model):
    """
    Individual messages in a chat session
    """
    SENDER_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPES
    )
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # AI-related fields
    intent_detected = models.CharField(
        max_length=100,
        blank=True,
        help_text="Intent detected by AI (e.g., 'ask_skill_gap', 'request_roadmap')"
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="AI confidence in intent detection (0-1)"
    )
    
    # Optional: store context used for this message
    context_used = models.JSONField(
        default=dict,
        blank=True,
        help_text="Context data used to generate response (user skills, roles, etc.)"
    )
    
    class Meta:
        db_table = 'chat_messages'
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['session', 'timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['sender_type']),
        ]
    
    def __str__(self):
        preview = self.message_text[:50] + "..." if len(self.message_text) > 50 else self.message_text
        return f"{self.get_sender_type_display()}: {preview}"
    
    def is_from_user(self):
        """Check if message is from user"""
        return self.sender_type == 'user'
    
    def is_from_bot(self):
        """Check if message is from bot"""
        return self.sender_type == 'bot'


class ChatbotIntent(models.Model):
    """
    Predefined intents that the chatbot can recognize
    This helps structure the chatbot's capabilities
    """
    intent_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for the intent (e.g., 'ask_skill_gap')"
    )
    description = models.TextField(
        help_text="What this intent represents"
    )
    response_template = models.TextField(
        help_text="Template for response (can include placeholders)"
    )
    
    # Optional: example phrases that trigger this intent
    example_phrases = models.JSONField(
        default=list,
        blank=True,
        help_text="Example user phrases that match this intent"
    )
    
    # Function to call when this intent is detected
    handler_function = models.CharField(
        max_length=100,
        blank=True,
        help_text="Python function to call (e.g., 'get_skill_gap')"
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chatbot_intents'
        verbose_name = 'Chatbot Intent'
        verbose_name_plural = 'Chatbot Intents'
        ordering = ['intent_name']
    
    def __str__(self):
        return f"{self.intent_name} - {self.description[:50]}"


class ChatbotContext(models.Model):
    """
    Store conversation context for better AI responses
    Helps the chatbot remember what the user is talking about
    """
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='contexts'
    )
    context_key = models.CharField(
        max_length=100,
        help_text="Key for the context (e.g., 'target_role', 'discussed_skills')"
    )
    context_value = models.JSONField(
        help_text="Value of the context"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_contexts'
        verbose_name = 'Chatbot Context'
        verbose_name_plural = 'Chatbot Contexts'
        unique_together = ['session', 'context_key']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.session.user.email} - {self.context_key}"