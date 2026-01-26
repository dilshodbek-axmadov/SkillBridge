"""
Career App Admin Configuration
===============================
Django admin interface for career assessment and recommendation models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    CareerQuestion,
    QuestionOption,
    CareerRole,
    RoleMatchingRule,
    UserCareerAssessment,
    AssessmentAnswer
)


class QuestionOptionInline(admin.TabularInline):
    """
    Inline admin for QuestionOption to show options in CareerQuestion admin.
    """
    model = QuestionOption
    extra = 1
    fields = ['option_text_en', 'option_text_ru', 'option_text_uz', 'option_value', 'display_order', 'icon_name']
    ordering = ['display_order']


@admin.register(CareerQuestion)
class CareerQuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for CareerQuestion model.
    """
    
    list_display = [
        'sequence_order',
        'question_preview',
        'category',
        'question_type',
        'is_active',
        'options_count',
        'created_at',
    ]
    
    list_filter = [
        'category',
        'question_type',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'question_text_en',
        'question_text_ru',
        'question_text_uz',
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Question Details'), {
            'fields': (
                'category',
                'question_type',
                'sequence_order',
                'is_active',
            )
        }),
        (_('Question Text'), {
            'fields': (
                'question_text_en',
                'question_text_ru',
                'question_text_uz',
            )
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['sequence_order']
    
    inlines = [QuestionOptionInline]
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def question_preview(self, obj):
        """Show preview of question text."""
        return obj.question_text_en[:60] + '...' if len(obj.question_text_en) > 60 else obj.question_text_en
    question_preview.short_description = _('Question')
    
    def options_count(self, obj):
        """Count of options for this question."""
        return obj.options.count()
    options_count.short_description = _('Options')
    
    def mark_as_active(self, request, queryset):
        """Mark selected questions as active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} question(s) marked as active.'))
    mark_as_active.short_description = _('Mark as active')
    
    def mark_as_inactive(self, request, queryset):
        """Mark selected questions as inactive."""
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} question(s) marked as inactive.'))
    mark_as_inactive.short_description = _('Mark as inactive')


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    """
    Admin interface for QuestionOption model.
    """
    
    list_display = [
        'question_sequence',
        'display_order',
        'option_preview',
        'option_value',
        'icon_name',
        'created_at',
    ]
    
    list_filter = [
        'question__category',
        'created_at',
    ]
    
    search_fields = [
        'option_text_en',
        'option_text_ru',
        'option_text_uz',
        'option_value',
        'question__question_text_en',
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Question'), {
            'fields': ('question', 'display_order')
        }),
        (_('Option Text'), {
            'fields': (
                'option_text_en',
                'option_text_ru',
                'option_text_uz',
            )
        }),
        (_('Metadata'), {
            'fields': ('option_value', 'icon_name')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['question__sequence_order', 'display_order']
    
    autocomplete_fields = ['question']
    
    def question_sequence(self, obj):
        """Display question sequence number."""
        return f"Q{obj.question.sequence_order}"
    question_sequence.short_description = _('Question')
    question_sequence.admin_order_field = 'question__sequence_order'
    
    def option_preview(self, obj):
        """Show preview of option text."""
        return obj.option_text_en[:50] + '...' if len(obj.option_text_en) > 50 else obj.option_text_en
    option_preview.short_description = _('Option Text')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('question')


class RoleMatchingRuleInline(admin.TabularInline):
    """
    Inline admin for RoleMatchingRule to show rules in CareerRole admin.
    """
    model = RoleMatchingRule
    extra = 1
    autocomplete_fields = ['question_option']
    fields = ['question_option', 'match_weight', 'match_type']
    ordering = ['-match_weight']


@admin.register(CareerRole)
class CareerRoleAdmin(admin.ModelAdmin):
    """
    Admin interface for CareerRole model.
    """
    
    list_display = [
        'role_name',
        'category',
        'difficulty_level',
        'demand_score_display',
        'average_salary_display',
        'remote_friendly',
        'typical_learning_months',
        'matching_rules_count',
    ]
    
    list_filter = [
        'category',
        'difficulty_level',
        'remote_friendly',
        'demand_score',
        'created_at',
    ]
    
    search_fields = [
        'role_name',
        'role_name_ru',
        'role_name_uz',
        'description_en',
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'role_name',
                'role_name_ru',
                'role_name_uz',
                'category',
            )
        }),
        (_('Descriptions'), {
            'fields': (
                'description_en',
                'description_ru',
                'description_uz',
            )
        }),
        (_('Role Attributes'), {
            'fields': (
                'difficulty_level',
                'demand_score',
                'work_alone_score',
                'work_team_score',
                'creative_score',
                'analytical_score',
            )
        }),
        (_('Career Information'), {
            'fields': (
                'average_salary_uzb',
                'typical_learning_months',
                'remote_friendly',
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['role_name']
    
    inlines = [RoleMatchingRuleInline]
    
    def demand_score_display(self, obj):
        """Display demand score with visual indicator."""
        stars = '⭐' * obj.demand_score
        return f"{stars} ({obj.demand_score}/10)"
    demand_score_display.short_description = _('Demand')
    
    def average_salary_display(self, obj):
        """Display average salary formatted."""
        if obj.average_salary_uzb:
            return f"{obj.average_salary_uzb:,.0f} UZS"
        return '-'
    average_salary_display.short_description = _('Avg Salary')
    
    def matching_rules_count(self, obj):
        """Count of matching rules."""
        return obj.matching_rules.count()
    matching_rules_count.short_description = _('Rules')


@admin.register(RoleMatchingRule)
class RoleMatchingRuleAdmin(admin.ModelAdmin):
    """
    Admin interface for RoleMatchingRule model.
    """
    
    list_display = [
        'role_name',
        'question_preview',
        'option_preview',
        'match_weight',
        'match_type',
        'created_at',
    ]
    
    list_filter = [
        'match_type',
        'match_weight',
        'role__category',
        'created_at',
    ]
    
    search_fields = [
        'role__role_name',
        'question_option__option_text_en',
        'question_option__option_value',
        'question_option__question__question_text_en',
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Rule Definition'), {
            'fields': ('role', 'question_option')
        }),
        (_('Matching Parameters'), {
            'fields': ('match_weight', 'match_type')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['role', '-match_weight']
    
    autocomplete_fields = ['role', 'question_option']
    
    def role_name(self, obj):
        """Display role name."""
        return obj.role.role_name
    role_name.short_description = _('Role')
    role_name.admin_order_field = 'role__role_name'
    
    def question_preview(self, obj):
        """Show question preview."""
        text = obj.question_option.question.question_text_en
        return f"Q{obj.question_option.question.sequence_order}: {text[:30]}..."
    question_preview.short_description = _('Question')
    
    def option_preview(self, obj):
        """Show option preview."""
        return obj.question_option.option_text_en[:40] + '...' if len(obj.question_option.option_text_en) > 40 else obj.question_option.option_text_en
    option_preview.short_description = _('Option')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('role', 'question_option', 'question_option__question')


class AssessmentAnswerInline(admin.TabularInline):
    """
    Inline admin for AssessmentAnswer to show answers in UserCareerAssessment admin.
    """
    model = AssessmentAnswer
    extra = 0
    fields = ['question', 'selected_option', 'answer_text']
    readonly_fields = ['question', 'selected_option', 'answer_text', 'answered_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(UserCareerAssessment)
class UserCareerAssessmentAdmin(admin.ModelAdmin):
    """
    Admin interface for UserCareerAssessment model.
    """
    
    list_display = [
        'assessment_id',
        'user_email',
        'selected_role_display',
        'top_recommendations',
        'completed_at',
    ]
    
    list_filter = [
        'selected_role',
        'completed_at',
    ]
    
    search_fields = [
        'user__email',
        'user__username',
        'selected_role__role_name',
    ]
    
    readonly_fields = ['completed_at', 'assessment_data', 'recommended_roles']
    
    fieldsets = (
        (_('User & Results'), {
            'fields': ('user', 'selected_role')
        }),
        (_('Assessment Data'), {
            'fields': ('assessment_data', 'recommended_roles'),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('completed_at',),
        }),
    )
    
    ordering = ['-completed_at']
    
    inlines = [AssessmentAnswerInline]
    
    autocomplete_fields = ['user', 'selected_role']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def selected_role_display(self, obj):
        """Display selected role."""
        if obj.selected_role:
            return obj.selected_role.role_name
        return _('Not selected')
    selected_role_display.short_description = _('Selected Role')
    
    def top_recommendations(self, obj):
        """Display top 3 recommended roles."""
        if obj.recommended_roles and isinstance(obj.recommended_roles, list):
            top_3 = obj.recommended_roles[:3]
            return ', '.join([f"{r.get('role_name', 'Unknown')} ({r.get('score', 0):.0f}%)" for r in top_3])
        return '-'
    top_recommendations.short_description = _('Top Recommendations')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'selected_role')


@admin.register(AssessmentAnswer)
class AssessmentAnswerAdmin(admin.ModelAdmin):
    """
    Admin interface for AssessmentAnswer model.
    """
    
    list_display = [
        'assessment_id_display',
        'user_email',
        'question_text',
        'selected_option_display',
        'answered_at',
    ]
    
    list_filter = [
        'question__category',
        'answered_at',
    ]
    
    search_fields = [
        'assessment__user__email',
        'question__question_text_en',
        'selected_option__option_text_en',
    ]
    
    readonly_fields = ['answered_at']
    
    fieldsets = (
        (_('Assessment & Question'), {
            'fields': ('assessment', 'question')
        }),
        (_('Answer'), {
            'fields': ('selected_option', 'answer_text')
        }),
        (_('Multiple Choice'), {
            'fields': ('selected_options',),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('answered_at',),
        }),
    )
    
    ordering = ['assessment', 'question__sequence_order']
    
    autocomplete_fields = ['assessment', 'question', 'selected_option']
    
    filter_horizontal = ['selected_options']
    
    def assessment_id_display(self, obj):
        """Display assessment ID."""
        return f"#{obj.assessment.assessment_id}"
    assessment_id_display.short_description = _('Assessment')
    
    def user_email(self, obj):
        """Display user email."""
        return obj.assessment.user.email
    user_email.short_description = _('User')
    
    def question_text(self, obj):
        """Display question text preview."""
        text = obj.question.question_text_en
        return f"Q{obj.question.sequence_order}: {text[:40]}..."
    question_text.short_description = _('Question')
    
    def selected_option_display(self, obj):
        """Display selected option."""
        if obj.selected_option:
            return obj.selected_option.option_text_en[:50]
        return '-'
    selected_option_display.short_description = _('Answer')
    
    def get_queryset(self, request):
        """Optimize with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('assessment', 'assessment__user', 'question', 'selected_option')
