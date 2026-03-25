from django.db import IntegrityError, transaction
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messaging.models import MessageThread, ThreadMessage
from apps.messaging.serializers import MessageThreadSerializer, ThreadMessageSerializer, SendMessageSerializer
from apps.users.models import User


def _thread_queryset_for_user(user):
    if user.is_staff:
        return MessageThread.objects.all()
    return MessageThread.objects.filter(Q(recruiter=user) | Q(developer=user))


def _ensure_can_message(sender: User, recipient: User) -> bool:
    if sender.is_staff:
        return True
    if sender.user_type == User.UserType.RECRUITER and recipient.user_type == User.UserType.DEVELOPER:
        return True
    if sender.user_type == User.UserType.DEVELOPER and recipient.user_type == User.UserType.RECRUITER:
        return True
    return False


class ThreadListCreateView(APIView):
    """
    GET /api/v1/messages/threads/
    POST /api/v1/messages/threads/  { recipient_id, body }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            _thread_queryset_for_user(request.user)
            .select_related('recruiter', 'developer')
            .prefetch_related('messages')
            .order_by('-last_message_at', '-updated_at')
        )
        return Response({'count': qs.count(), 'threads': MessageThreadSerializer(qs, many=True, context={'request': request}).data})

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient_id = serializer.validated_data['recipient_id']
        body = serializer.validated_data['body']

        recipient = get_object_or_404(User, id=recipient_id)
        if not _ensure_can_message(request.user, recipient):
            return Response({'error': 'Messaging is only available between recruiters and developers.'}, status=status.HTTP_400_BAD_REQUEST)

        # Determine roles.
        if request.user.user_type == User.UserType.RECRUITER:
            recruiter = request.user
            developer = recipient
        else:
            recruiter = recipient
            developer = request.user

        try:
            with transaction.atomic():
                thread, _ = MessageThread.objects.get_or_create(recruiter=recruiter, developer=developer)
                msg = ThreadMessage.objects.create(thread=thread, sender=request.user, body=body)
                thread.touch()
        except IntegrityError:
            thread = MessageThread.objects.get(recruiter=recruiter, developer=developer)
            msg = ThreadMessage.objects.create(thread=thread, sender=request.user, body=body)
            thread.touch()

        out_thread = MessageThreadSerializer(thread, context={'request': request}).data
        out_msg = ThreadMessageSerializer(msg).data
        return Response({'thread': out_thread, 'message': out_msg}, status=status.HTTP_201_CREATED)


class ThreadDetailView(APIView):
    """
    GET /api/v1/messages/threads/{thread_id}/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        thread = get_object_or_404(
            _thread_queryset_for_user(request.user).select_related('recruiter', 'developer'),
            thread_id=thread_id,
        )
        return Response(MessageThreadSerializer(thread, context={'request': request}).data)


class ThreadMessageListView(APIView):
    """
    GET /api/v1/messages/threads/{thread_id}/messages/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        thread = get_object_or_404(_thread_queryset_for_user(request.user), thread_id=thread_id)
        qs = thread.messages.select_related('sender').order_by('created_at')

        # Mark messages from the other participant as read when opened.
        thread.messages.filter(read_at__isnull=True).exclude(sender_id=request.user.id).update(read_at=timezone.now())

        return Response({'count': qs.count(), 'messages': ThreadMessageSerializer(qs, many=True).data})


class ThreadSendMessageView(APIView):
    """
    POST /api/v1/messages/threads/{thread_id}/send/ { body }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        thread = get_object_or_404(_thread_queryset_for_user(request.user), thread_id=thread_id)
        body = (request.data.get('body') or '').strip()
        if not body:
            return Response({'error': 'Message body is required.'}, status=status.HTTP_400_BAD_REQUEST)

        msg = ThreadMessage.objects.create(thread=thread, sender=request.user, body=body)
        thread.touch()
        return Response(ThreadMessageSerializer(msg).data, status=status.HTTP_201_CREATED)

