"""
Serializers for CV upload and processing
"""
from rest_framework import serializers
from cvs.models import UploadedCV, CVExtractionLog


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