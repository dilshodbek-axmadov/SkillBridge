"""
CV App Serializers
==================
Serializers for CV CRUD, auto-populate, and export endpoints.
"""

from rest_framework import serializers
from apps.cv.models import CV, CVSection


# --- CV Section Serializers ---

class CVSectionSerializer(serializers.ModelSerializer):
    """Full CV section serializer."""

    class Meta:
        model = CVSection
        fields = [
            'section_id', 'section_type', 'content',
            'display_order', 'is_visible',
        ]
        read_only_fields = ['section_id']


class CVSectionInputSerializer(serializers.Serializer):
    """Input serializer for creating/updating a CV section."""

    section_type = serializers.ChoiceField(
        choices=[c[0] for c in CVSection.SECTION_TYPE_CHOICES],
        help_text="Type of section.",
    )
    content = serializers.JSONField(
        default=dict,
        help_text="Section content as JSON.",
    )
    display_order = serializers.IntegerField(
        default=0,
        help_text="Display order (0-based).",
    )
    is_visible = serializers.BooleanField(
        default=True,
        help_text="Whether section is visible.",
    )


# --- CV Serializers ---

class CVListSerializer(serializers.ModelSerializer):
    """CV list serializer with section count."""

    section_count = serializers.SerializerMethodField()

    class Meta:
        model = CV
        fields = [
            'cv_id', 'title', 'template_type', 'language_code',
            'is_default', 'section_count', 'created_at', 'updated_at',
        ]

    def get_section_count(self, obj):
        return obj.cv_sections.count()


class CVDetailSerializer(serializers.ModelSerializer):
    """CV detail serializer with all sections."""

    sections = serializers.SerializerMethodField()

    class Meta:
        model = CV
        fields = [
            'cv_id', 'title', 'template_type', 'language_code',
            'is_default', 'sections', 'created_at', 'updated_at',
        ]

    def get_sections(self, obj):
        sections = obj.cv_sections.filter(
            is_visible=True
        ).order_by('display_order')
        return CVSectionSerializer(sections, many=True).data


# --- Request Serializers ---

class CreateCVRequestSerializer(serializers.Serializer):
    """Request serializer for creating a CV."""

    title = serializers.CharField(
        max_length=200,
        help_text="CV title (e.g., 'Software Engineer CV').",
    )
    template_type = serializers.ChoiceField(
        choices=[c[0] for c in CV.TEMPLATE_CHOICES],
        default='modern',
        help_text="CV template.",
    )
    language_code = serializers.ChoiceField(
        choices=[c[0] for c in CV.LANGUAGE_CHOICES],
        default='en',
        help_text="CV language.",
    )
    is_default = serializers.BooleanField(
        default=False,
        help_text="Set as default CV.",
    )
    sections = CVSectionInputSerializer(
        many=True,
        required=False,
        help_text="Optional initial sections.",
    )


class AutoPopulateRequestSerializer(serializers.Serializer):
    """Request serializer for auto-populating a CV from profile."""

    title = serializers.CharField(
        max_length=200,
        required=False,
        help_text="CV title. Auto-generated if not provided.",
    )
    template_type = serializers.ChoiceField(
        choices=[c[0] for c in CV.TEMPLATE_CHOICES],
        default='modern',
        help_text="CV template to use.",
    )
    language_code = serializers.ChoiceField(
        choices=[c[0] for c in CV.LANGUAGE_CHOICES],
        default='en',
        help_text="CV language.",
    )


class UpdateSectionsRequestSerializer(serializers.Serializer):
    """Request serializer for updating CV sections."""

    sections = CVSectionInputSerializer(
        many=True,
        help_text="Sections to create or update.",
    )


class SwitchTemplateRequestSerializer(serializers.Serializer):
    """Request serializer for switching CV template."""

    template_type = serializers.ChoiceField(
        choices=[c[0] for c in CV.TEMPLATE_CHOICES],
        help_text="New template to apply.",
    )


class ExportCVRequestSerializer(serializers.Serializer):
    """Query params serializer for CV export."""

    # NOTE: Do NOT use 'format' as field name — DRF reserves it for
    # content-negotiation (?format=json). Using 'export_format' instead.
    export_format = serializers.ChoiceField(
        choices=['pdf', 'docx'],
        default='pdf',
        help_text="Export format: pdf or docx.",
    )
