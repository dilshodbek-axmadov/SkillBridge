from rest_framework import serializers

from apps.messaging.models import MessageThread, ThreadMessage
from apps.users.models import User


class ThreadParticipantSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'user_type']


class ThreadMessageSerializer(serializers.ModelSerializer):
    sender = ThreadParticipantSerializer(read_only=True)

    class Meta:
        model = ThreadMessage
        fields = ['message_id', 'thread', 'sender', 'body', 'created_at', 'read_at']
        read_only_fields = ['message_id', 'thread', 'sender', 'created_at', 'read_at']


class MessageThreadSerializer(serializers.ModelSerializer):
    recruiter = ThreadParticipantSerializer(read_only=True)
    developer = ThreadParticipantSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = [
            'thread_id',
            'recruiter',
            'developer',
            'created_at',
            'updated_at',
            'last_message_at',
            'last_message',
            'unread_count',
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').select_related('sender').first()
        if not msg:
            return None
        return {
            'message_id': msg.message_id,
            'sender_id': msg.sender_id,
            'body': msg.body[:240],
            'created_at': msg.created_at,
        }

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(read_at__isnull=True).exclude(sender_id=request.user.id).count()


class SendMessageSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField(required=True)
    body = serializers.CharField(required=True, allow_blank=False, max_length=5000)

