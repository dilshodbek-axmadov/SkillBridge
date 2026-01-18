"""
Admin configuration for chatbot models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ChatSession, ChatMessage, ChatbotIntent, ChatbotContext


class ChatMessageInline(admin.TabularInline):
    """Inline for chat messages"""
    model = ChatMessage
    extra = 0
    fields = ['sender_type', 'message_preview', 'intent_detected', 'timestamp']
    readonly_fields = ['message_preview', 'timestamp']
    can_delete = False
    
    def message_preview(self, obj):
        preview = obj.message_text[:100] + "..." if len(obj.message_text) > 100 else obj.message_text
        return preview
    message_preview.short_description = 'Message'


class ChatbotContextInline(admin.TabularInline):
    """Inline for context"""
    model = ChatbotContext
    extra = 0
    fields = ['context_key', 'context_value', 'updated_at']
    readonly_fields = ['updated_at']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Admin for chat sessions"""
    list_display = [
        'id', 'user', 'status_display', 'message_count',
        'duration_display', 'session_start', 'session_end'
    ]
    list_filter = ['is_active', 'session_start']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['session_start', 'session_end']
    date_hierarchy = 'session_start'
    inlines = [ChatMessageInline, ChatbotContextInline]
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('session_start', 'session_end')
        }),
    )
    
    def status_display(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: gray;">● Closed</span>'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_active'
    
    def message_count(self, obj):
        return obj.get_message_count()
    message_count.short_description = 'Messages'
    
    def duration_display(self, obj):
        return obj.get_duration_display()
    duration_display.short_description = 'Duration'
    
    actions = ['close_sessions']
    
    def close_sessions(self, request, queryset):
        """Close selected sessions"""
        updated = 0
        for session in queryset.filter(is_active=True):
            session.close_session()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully closed {updated} session(s).'
        )
    close_sessions.short_description = 'Close selected sessions'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin for chat messages"""
    list_display = [
        'id', 'session_user', 'sender_display',
        'message_preview', 'intent_detected',
        'confidence_display', 'timestamp'
    ]
    list_filter = ['sender_type', 'timestamp']
    search_fields = [
        'session__user__email', 'message_text', 'intent_detected'
    ]
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Session', {
            'fields': ('session',)
        }),
        ('Message', {
            'fields': ('sender_type', 'message_text')
        }),
        ('AI Analysis', {
            'fields': ('intent_detected', 'confidence_score', 'context_used')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def session_user(self, obj):
        return obj.session.user.email
    session_user.short_description = 'User'
    session_user.admin_order_field = 'session__user__email'
    
    def sender_display(self, obj):
        if obj.sender_type == 'user':
            return format_html(
                '<span style="color: blue; font-weight: bold;">👤 User</span>'
            )
        return format_html(
            '<span style="color: green; font-weight: bold;">🤖 Bot</span>'
        )
    sender_display.short_description = 'Sender'
    sender_display.admin_order_field = 'sender_type'
    
    def message_preview(self, obj):
        preview = obj.message_text[:80] + "..." if len(obj.message_text) > 80 else obj.message_text
        return preview
    message_preview.short_description = 'Message'
    
    def confidence_display(self, obj):
        if obj.confidence_score is not None:
            percentage = obj.confidence_score * 100
            if percentage >= 80:
                color = 'green'
            elif percentage >= 50:
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color,
                percentage
            )
        return '-'
    confidence_display.short_description = 'Confidence'
    confidence_display.admin_order_field = 'confidence_score'


@admin.register(ChatbotIntent)
class ChatbotIntentAdmin(admin.ModelAdmin):
    """Admin for chatbot intents"""
    list_display = [
        'intent_name', 'description_preview',
        'handler_function', 'example_count', 'is_active'
    ]
    list_filter = ['is_active']
    search_fields = ['intent_name', 'description', 'handler_function']
    
    fieldsets = (
        ('Intent Info', {
            'fields': ('intent_name', 'description', 'is_active')
        }),
        ('Response', {
            'fields': ('response_template', 'handler_function')
        }),
        ('Training Examples', {
            'fields': ('example_phrases',)
        }),
    )
    
    def description_preview(self, obj):
        return obj.description[:60] + "..." if len(obj.description) > 60 else obj.description
    description_preview.short_description = 'Description'
    
    def example_count(self, obj):
        if isinstance(obj.example_phrases, list):
            return len(obj.example_phrases)
        return 0
    example_count.short_description = 'Examples'


@admin.register(ChatbotContext)
class ChatbotContextAdmin(admin.ModelAdmin):
    """Admin for chatbot context"""
    list_display = [
        'session_user', 'context_key', 'value_preview',
        'updated_at'
    ]
    list_filter = ['context_key', 'updated_at']
    search_fields = ['session__user__email', 'context_key']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Context', {
            'fields': ('session', 'context_key', 'context_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def session_user(self, obj):
        return obj.session.user.email
    session_user.short_description = 'User'
    
    def value_preview(self, obj):
        import json
        value_str = json.dumps(obj.context_value)
        return value_str[:100] + "..." if len(value_str) > 100 else value_str
    value_preview.short_description = 'Value'