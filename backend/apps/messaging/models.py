from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class MessageThread(models.Model):
    """
    1:1 conversation between a recruiter and a developer.

    We keep explicit foreign keys for easy querying and to avoid
    allowing recruiter↔recruiter or developer↔developer threads.
    """

    thread_id = models.AutoField(primary_key=True)
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_threads_as_recruiter',
    )
    developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_threads_as_developer',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'message_threads'
        constraints = [
            models.UniqueConstraint(fields=['recruiter', 'developer'], name='uniq_thread_recruiter_developer'),
            models.CheckConstraint(check=~Q(recruiter=models.F('developer')), name='chk_thread_not_self'),
        ]

    def touch(self):
        self.last_message_at = timezone.now()
        self.save(update_fields=['last_message_at', 'updated_at'])


class ThreadMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'thread_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
        ]

