"""
Serializers for CV upload, generation, and management
"""
from rest_framework import serializers
from .models import (
    UploadedCV, CVExtractionLog, UserCV, CVSection,
    WorkExperience, Education, Project, ProjectSkill
)
from skills.models import Skill


# Uploaded CV Serializers

class UploadedCVSerializer(serializers.ModelSerializer):
    """Serializer for uploaded CVs"""

    class Meta:
        model = UploadedCV
        fields = [
            'id', 'original_filename', 'file_type', 'upload_date',
            'processing_status', 'extracted_data_json'
        ]
        read_only_fields = ['upload_date', 'processing_status', 'extracted_data_json']


class CVUploadSerializer(serializers.Serializer):
    """Serializer for CV file upload"""
    cv_file = serializers.FileField(required=True)

    def validate_cv_file(self, value):
        """Validate CV file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB")

        # Check file extension
        allowed_extensions = ['pdf', 'docx']
        file_extension = value.name.split('.')[-1].lower()

        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )

        return value


class CVExtractionResultSerializer(serializers.Serializer):
    """Serializer for CV extraction results"""
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    skills = serializers.ListField(child=serializers.CharField())
    job_titles = serializers.ListField(child=serializers.CharField())
    experience_level = serializers.CharField()
    education = serializers.ListField(child=serializers.DictField())
    skills_count = serializers.IntegerField()
    confidence_score = serializers.FloatField()


class CVExtractionLogSerializer(serializers.ModelSerializer):
    """Serializer for CV extraction logs"""

    class Meta:
        model = CVExtractionLog
        fields = [
            'id', 'extraction_date', 'skills_extracted_count',
            'confidence_score', 'errors_json'
        ]
        read_only_fields = ['extraction_date']


# Work Experience Serializers

class WorkExperienceSerializer(serializers.ModelSerializer):
    """Serializer for work experience"""
    duration = serializers.CharField(source='get_duration', read_only=True)

    class Meta:
        model = WorkExperience
        fields = [
            'id', 'company_name', 'position_title', 'start_date', 'end_date',
            'is_current', 'description', 'location', 'duration'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """Validate work experience data"""
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError(
                "Cannot have end_date if currently working here"
            )
        if not data.get('is_current') and not data.get('end_date'):
            raise serializers.ValidationError(
                "End date is required if not currently working here"
            )
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError(
                    "End date cannot be before start date"
                )
        return data


class WorkExperienceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating work experience"""

    class Meta:
        model = WorkExperience
        fields = [
            'company_name', 'position_title', 'start_date', 'end_date',
            'is_current', 'description', 'location'
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Education Serializers

class EducationSerializer(serializers.ModelSerializer):
    """Serializer for education"""

    class Meta:
        model = Education
        fields = [
            'id', 'institution_name', 'degree', 'field_of_study',
            'start_date', 'end_date', 'grade', 'description'
        ]
        read_only_fields = ['id']


class EducationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating education"""

    class Meta:
        model = Education
        fields = [
            'institution_name', 'degree', 'field_of_study',
            'start_date', 'end_date', 'grade', 'description'
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Project Serializers

class ProjectSkillSerializer(serializers.ModelSerializer):
    """Serializer for project skills"""
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = ProjectSkill
        fields = ['id', 'skill', 'skill_name']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for projects"""
    skills = ProjectSkillSerializer(source='project_skills', many=True, read_only=True)
    skill_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'project_url', 'github_url', 'technologies_used',
            'skills', 'skill_ids'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        skill_ids = validated_data.pop('skill_ids', [])
        validated_data['user'] = self.context['request'].user
        project = Project.objects.create(**validated_data)

        # Add skills
        for skill_id in skill_ids:
            try:
                skill = Skill.objects.get(id=skill_id)
                ProjectSkill.objects.create(project=project, skill=skill)
            except Skill.DoesNotExist:
                pass

        return project

    def update(self, instance, validated_data):
        skill_ids = validated_data.pop('skill_ids', None)
        instance = super().update(instance, validated_data)

        if skill_ids is not None:
            # Clear existing skills and add new ones
            instance.project_skills.all().delete()
            for skill_id in skill_ids:
                try:
                    skill = Skill.objects.get(id=skill_id)
                    ProjectSkill.objects.create(project=instance, skill=skill)
                except Skill.DoesNotExist:
                    pass

        return instance


# CV Section Serializers

class CVSectionSerializer(serializers.ModelSerializer):
    """Serializer for CV sections"""
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)

    class Meta:
        model = CVSection
        fields = [
            'id', 'section_type', 'section_type_display',
            'content_json', 'display_order'
        ]
        read_only_fields = ['id']


class CVSectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CV sections"""

    class Meta:
        model = CVSection
        fields = ['section_type', 'content_json', 'display_order']


# User CV Serializers

class UserCVListSerializer(serializers.ModelSerializer):
    """Serializer for listing user CVs"""
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = UserCV
        fields = [
            'id', 'template_type', 'template_type_display',
            'created_date', 'last_updated', 'is_primary',
            'file_path', 'sections_count'
        ]

    def get_sections_count(self, obj):
        return obj.cv_sections.count()


class UserCVDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user CV view"""
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    sections = CVSectionSerializer(source='cv_sections', many=True, read_only=True)

    class Meta:
        model = UserCV
        fields = [
            'id', 'template_type', 'template_type_display',
            'created_date', 'last_updated', 'is_primary',
            'file_path', 'sections'
        ]


class UserCVCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user CV"""

    class Meta:
        model = UserCV
        fields = ['template_type', 'is_primary']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        cv = super().create(validated_data)

        # If set as primary, unset others
        if cv.is_primary:
            UserCV.objects.filter(
                user=cv.user, is_primary=True
            ).exclude(id=cv.id).update(is_primary=False)

        return cv


class UserCVUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user CV"""

    class Meta:
        model = UserCV
        fields = ['template_type', 'is_primary']


# CV Generation Serializers

class PersonalDetailsSerializer(serializers.Serializer):
    """Serializer for personal details step"""
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)
    github_url = serializers.URLField(required=False, allow_blank=True)
    portfolio_url = serializers.URLField(required=False, allow_blank=True)


class ProfessionalSummarySerializer(serializers.Serializer):
    """Serializer for professional summary step"""
    summary = serializers.CharField(max_length=2000)
    current_role = serializers.CharField(max_length=100, required=False, allow_blank=True)
    experience_level = serializers.ChoiceField(
        choices=['junior', 'mid', 'senior'],
        required=False
    )


class SkillsInputSerializer(serializers.Serializer):
    """Serializer for skills step"""
    skill_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of skill IDs to include in CV"
    )
    custom_skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="List of custom skill names not in database"
    )


class LanguageSerializer(serializers.Serializer):
    """Serializer for language entry"""
    language = serializers.CharField(max_length=50)
    proficiency = serializers.ChoiceField(
        choices=['native', 'fluent', 'advanced', 'intermediate', 'basic']
    )


class LanguagesInputSerializer(serializers.Serializer):
    """Serializer for languages step"""
    languages = LanguageSerializer(many=True)


class CertificationSerializer(serializers.Serializer):
    """Serializer for certification entry"""
    name = serializers.CharField(max_length=255)
    issuer = serializers.CharField(max_length=255)
    issue_date = serializers.DateField()
    expiry_date = serializers.DateField(required=False, allow_null=True)
    credential_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    credential_url = serializers.URLField(required=False, allow_blank=True)


class CertificationsInputSerializer(serializers.Serializer):
    """Serializer for certifications step"""
    certifications = CertificationSerializer(many=True)


class CVGenerationOptionsSerializer(serializers.Serializer):
    """Serializer for CV generation options"""
    template_type = serializers.ChoiceField(
        choices=['modern', 'classic', 'minimal', 'professional', 'creative'],
        default='modern'
    )
    include_photo = serializers.BooleanField(default=False)
    include_summary = serializers.BooleanField(default=True)
    include_experience = serializers.BooleanField(default=True)
    include_education = serializers.BooleanField(default=True)
    include_skills = serializers.BooleanField(default=True)
    include_projects = serializers.BooleanField(default=True)
    include_certifications = serializers.BooleanField(default=True)
    include_languages = serializers.BooleanField(default=True)
    set_as_primary = serializers.BooleanField(default=False)


class AutoGenerateCVSerializer(serializers.Serializer):
    """Serializer for auto-generating CV from profile"""
    template_type = serializers.ChoiceField(
        choices=['modern', 'classic', 'minimal', 'professional', 'creative'],
        default='modern'
    )
    set_as_primary = serializers.BooleanField(default=False)


# CV Preview/Export Serializers

class CVPreviewSerializer(serializers.Serializer):
    """Serializer for CV preview data"""
    personal_details = serializers.DictField()
    summary = serializers.CharField(allow_null=True)
    experience = WorkExperienceSerializer(many=True)
    education = EducationSerializer(many=True)
    skills = serializers.ListField(child=serializers.DictField())
    projects = ProjectSerializer(many=True)
    certifications = serializers.ListField(child=serializers.DictField())
    languages = serializers.ListField(child=serializers.DictField())
    template_type = serializers.CharField()


class CVExportSerializer(serializers.Serializer):
    """Serializer for CV export options"""
    cv_id = serializers.IntegerField()
    format = serializers.ChoiceField(
        choices=['pdf', 'docx'],
        default='pdf'
    )


# CV Templates Serializer

class CVTemplateSerializer(serializers.Serializer):
    """Serializer for available CV templates"""
    template_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    preview_image_url = serializers.URLField(allow_null=True)
    is_premium = serializers.BooleanField(default=False)


# CV Builder Progress Serializer

class CVBuilderProgressSerializer(serializers.Serializer):
    """Serializer for tracking CV builder progress"""
    current_step = serializers.IntegerField()
    total_steps = serializers.IntegerField()
    completed_steps = serializers.ListField(child=serializers.CharField())
    next_step = serializers.CharField(allow_null=True)
    personal_details_complete = serializers.BooleanField()
    summary_complete = serializers.BooleanField()
    experience_complete = serializers.BooleanField()
    education_complete = serializers.BooleanField()
    skills_complete = serializers.BooleanField()
    projects_complete = serializers.BooleanField()
    certifications_complete = serializers.BooleanField()
    languages_complete = serializers.BooleanField()
