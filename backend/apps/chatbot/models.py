"""
Chatbot App Models
==================
backend/apps/chatbot/models.py

AI-powered chatbot for career guidance.
Stores conversation history and context.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ChatbotConversation(models.Model):
    """
    Chatbot conversation session.
    Groups related messages together.
    """
    
    CONTEXT_TYPE_CHOICES = [
        ('onboarding', _('Onboarding / Career Assessment')),
        ('roadmap', _('Learning Roadmap')),
        ('career', _('Career Advice')),
        ('help', _('General Help')),
    ]
    
    conversation_id = models.AutoField(primary_key=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chatbot_conversations',
        verbose_name=_('user')
    )
    
    context_type = models.CharField(
        _('context type'),
        max_length=20,
        choices=CONTEXT_TYPE_CHOICES,
        help_text=_('Type of conversation/assistance')
    )
    
    started_at = models.DateTimeField(
        _('started at'),
        auto_now_add=True
    )
    
    ended_at = models.DateTimeField(
        _('ended at'),
        null=True,
        blank=True,
        help_text=_('When conversation was closed/completed')
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Is this conversation still ongoing?')
    )
    
    class Meta:
        db_table = 'chatbot_conversations'
        ordering = ['-started_at']
        verbose_name = _('chatbot conversation')
        verbose_name_plural = _('chatbot conversations')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-started_at']),
        ]
    
    def __str__(self):
        status = 'Active' if self.is_active else 'Ended'
        return f"{self.user.username} - {self.get_context_type_display()} [{status}]"
    
    def get_message_count(self):
        """Get total message count in this conversation."""
        return self.chatbot_messages.count()
    
    def get_user_message_count(self):
        """Get count of user messages."""
        return self.chatbot_messages.filter(sender_type='user').count()
    
    def get_bot_message_count(self):
        """Get count of bot messages."""
        return self.chatbot_messages.filter(sender_type='bot').count()
    
    def get_duration(self):
        """Get conversation duration."""
        if self.ended_at:
            return self.ended_at - self.started_at
        return None
    
    def close_conversation(self):
        """Close/end the conversation."""
        from django.utils import timezone
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()


class ChatbotMessage(models.Model):
    """
    Individual messages in chatbot conversation.
    Stores both user and bot messages with context.
    """
    
    SENDER_TYPE_CHOICES = [
        ('user', _('User')),
        ('bot', _('Bot')),
    ]
    
    message_id = models.AutoField(primary_key=True)
    
    conversation = models.ForeignKey(
        ChatbotConversation,
        on_delete=models.CASCADE,
        related_name='chatbot_messages',
        verbose_name=_('conversation')
    )
    
    sender_type = models.CharField(
        _('sender type'),
        max_length=10,
        choices=SENDER_TYPE_CHOICES
    )
    
    message_text = models.TextField(
        _('message text'),
        help_text=_('Message content')
    )
    
    context_data = models.JSONField(
        _('context data'),
        blank=True,
        null=True,
        help_text=_('Additional context like skills, roles, intent, etc.')
    )
    
    timestamp = models.DateTimeField(
        _('timestamp'),
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'chatbot_messages'
        ordering = ['timestamp']
        verbose_name = _('chatbot message')
        verbose_name_plural = _('chatbot messages')
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender_type']),
        ]
    
    def __str__(self):
        preview = self.message_text[:50] + '...' if len(self.message_text) > 50 else self.message_text
        return f"{self.get_sender_type_display()}: {preview}"
    
    def is_from_user(self):
        """Check if message is from user."""
        return self.sender_type == 'user'
    
    def is_from_bot(self):
        """Check if message is from bot."""
        return self.sender_type == 'bot'


"""
Example ChatbotMessage.context_data JSON structures:

USER MESSAGE (with intent):
{
    "intent": "ask_about_skill",
    "entities": {
        "skill": "Python",
        "question_type": "learning_resources"
    },
    "user_state": {
        "current_role": null,
        "skill_level": "beginner"
    }
}

BOT MESSAGE (with skill recommendations):
{
    "response_type": "skill_recommendation",
    "recommended_skills": [
        {"skill_id": 123, "skill_name": "Python", "priority": "high"},
        {"skill_id": 456, "skill_name": "SQL", "priority": "medium"}
    ],
    "reasoning": "Based on your interest in data analysis..."
}

BOT MESSAGE (with career role suggestion):
{
    "response_type": "role_suggestion",
    "suggested_roles": [
        {
            "role_id": 5,
            "role_name": "Backend Developer",
            "match_score": 0.85,
            "reasoning": "Your skills align well with..."
        }
    ]
}

BOT MESSAGE (with learning resources):
{
    "response_type": "learning_resource",
    "resources": [
        {
            "resource_id": 789,
            "title": "Python for Beginners",
            "type": "video",
            "url": "https://..."
        }
    ]
}

USER MESSAGE (career assessment answer):
{
    "assessment_question_id": 12,
    "selected_options": [5, 8, 12],
    "assessment_progress": 0.4
}
"""