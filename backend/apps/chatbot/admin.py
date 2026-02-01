"""
Chatbot App Admin
=================
backend/apps/chatbot/admin.py

Admin interface for viewing and managing chatbot conversations.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from .models import ChatbotConversation, ChatbotMessage
from django.utils.translation import gettext as _ 


class ChatbotMessageInline(admin.TabularInline):
    """Inline for chatbot messages."""
    model = ChatbotMessage
    extra = 0
    fields = ['sender_type', 'message_preview', 'timestamp']
    readonly_fields = ['sender_type', 'message_preview', 'timestamp']
    ordering = ['timestamp']
    
    def message_preview(self, obj):
        """Show message preview."""
        preview = obj.message_text[:100] + '...' if len(obj.message_text) > 100 else obj.message_text
        return preview
    
    message_preview.short_description = _('Message')
    
    def has_add_permission(self, request, obj=None):
        """Don't allow adding messages from admin."""
        return False


@admin.register(ChatbotConversation)
class ChatbotConversationAdmin(admin.ModelAdmin):
    """Admin interface for ChatbotConversation model."""
    
    list_display = [
        'conversation_id',
        'user_link',
        'context_type_badge',
        'status_badge',
        'message_stats',
        'duration_display',
        'started_at',
        'ended_at'
    ]
    
    list_filter = [
        'context_type',
        'is_active',
        'started_at',
        'ended_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email'
    ]
    
    raw_id_fields = ['user']
    
    ordering = ['-started_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'context_type')
        }),
        (_('Status'), {
            'fields': ('is_active', 'started_at', 'ended_at')
        }),
    )
    
    readonly_fields = ['started_at']
    
    inlines = [ChatbotMessageInline]
    
    actions = ['close_conversations']
    
    def user_link(self, obj):
        """Link to user admin."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    
    user_link.short_description = _('User')
    user_link.admin_order_field = 'user__username'
    
    def context_type_badge(self, obj):
        """Display context type with color badge."""
        colors = {
            'onboarding': '#007bff',
            'roadmap': '#28a745',
            'career': '#17a2b8',
            'help': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.context_type, '#6c757d'),
            obj.get_context_type_display()
        )
    
    context_type_badge.short_description = _('Context')
    context_type_badge.admin_order_field = 'context_type'
    
    def status_badge(self, obj):
        """Display active/ended status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">🟢 Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">⚪ Ended</span>'
        )
    
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'is_active'
    
    def message_stats(self, obj):
        """Show message statistics."""
        total = obj.get_message_count()
        user_msgs = obj.get_user_message_count()
        bot_msgs = obj.get_bot_message_count()
        
        return format_html(
            '<span title="User: {} | Bot: {}">📊 {} total</span>',
            user_msgs,
            bot_msgs,
            total
        )
    
    message_stats.short_description = _('Messages')
    
    def duration_display(self, obj):
        """Display conversation duration."""
        if obj.ended_at:
            duration = obj.get_duration()
            if duration:
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                
                if hours > 0:
                    return f"{hours}h {minutes}m"
                elif minutes > 0:
                    return f"{minutes}m"
                else:
                    return "< 1m"
        elif obj.is_active:
            # Calculate time since start
            duration = timezone.now() - obj.started_at
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            return format_html(
                '<span style="color: #28a745;">🔴 {}h {}m</span>',
                hours, minutes
            )
        return "—"
    
    duration_display.short_description = _('Duration')
    
    def close_conversations(self, request, queryset):
        """Admin action to close selected conversations."""
        count = 0
        for conversation in queryset.filter(is_active=True):
            conversation.close_conversation()
            count += 1
        
        self.message_user(
            request,
            f"Successfully closed {count} conversation(s)."
        )
    
    close_conversations.short_description = _('Close selected conversations')
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user').annotate(
            message_count=Count('chatbot_messages')
        )


@admin.register(ChatbotMessage)
class ChatbotMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatbotMessage model."""
    
    list_display = [
        'message_id',
        'conversation_link',
        'user_link',
        'sender_badge',
        'message_preview',
        'has_context',
        'timestamp'
    ]
    
    list_filter = [
        'sender_type',
        'timestamp',
        'conversation__context_type'
    ]
    
    search_fields = [
        'message_text',
        'conversation__user__username'
    ]
    
    raw_id_fields = ['conversation']
    
    ordering = ['-timestamp']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('conversation', 'sender_type', 'timestamp')
        }),
        (_('Message Content'), {
            'fields': ('message_text',)
        }),
        (_('Context Data'), {
            'fields': ('context_data',),
            'classes': ('collapse',),
            'description': _('Additional context stored as JSON')
        }),
    )
    
    readonly_fields = ['timestamp']
    
    def conversation_link(self, obj):
        """Link to conversation admin."""
        return format_html(
            '<a href="/admin/chatbot/chatbotconversation/{}/change/">Conv #{}</a>',
            obj.conversation.conversation_id,
            obj.conversation.conversation_id
        )
    
    conversation_link.short_description = _('Conversation')
    conversation_link.admin_order_field = 'conversation__conversation_id'
    
    def user_link(self, obj):
        """Link to user admin."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.conversation.user.id,
            obj.conversation.user.username
        )
    
    user_link.short_description = _('User')
    user_link.admin_order_field = 'conversation__user__username'
    
    def sender_badge(self, obj):
        """Display sender with icon and color."""
        if obj.sender_type == 'user':
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">👤 User</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">🤖 Bot</span>'
        )
    
    sender_badge.short_description = _('Sender')
    sender_badge.admin_order_field = 'sender_type'
    
    def message_preview(self, obj):
        """Show truncated message."""
        if len(obj.message_text) > 80:
            preview = obj.message_text[:80] + '...'
        else:
            preview = obj.message_text
        
        return format_html('<span title="{}">{}</span>', obj.message_text, preview)
    
    message_preview.short_description = _('Message')
    
    def has_context(self, obj):
        """Check if message has context data."""
        if obj.context_data:
            import json
            context_str = json.dumps(obj.context_data, ensure_ascii=False)
            preview = context_str[:50] + '...' if len(context_str) > 50 else context_str
            return format_html(
                '<span title="{}" style="color: #28a745; cursor: help;">✅</span>',
                preview
            )
        return format_html('—')
    
    has_context.short_description = _('Context')
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related(
            'conversation',
            'conversation__user'
        )