"""
Serializers for Jobs API
"""
from rest_framework import serializers
from jobs.models import JobPosting, JobCategory, JobSkill, JobPostingCategory
from skills.serializers import SkillSerializer


class JobCategorySerializer(serializers.ModelSerializer):
    """Serializer for job categories"""
    
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description', 'external_id']


class JobSkillSerializer(serializers.ModelSerializer):
    """Serializer for job skills"""
    skill = SkillSerializer(read_only=True)
    importance_display = serializers.CharField(source='get_importance_level_display', read_only=True)
    
    class Meta:
        model = JobSkill
        fields = ['id', 'skill', 'is_required', 'importance_level', 'importance_display']


class JobPostingListSerializer(serializers.ModelSerializer):
    """Serializer for job listing (compact)"""
    work_type_display = serializers.CharField(source='get_work_type_display', read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    salary_range = serializers.SerializerMethodField()
    age_in_days = serializers.SerializerMethodField()
    is_fresh = serializers.SerializerMethodField()
    required_skills_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'external_id', 'title', 'company_name', 'location',
            'work_type', 'work_type_display', 'employment_type', 'employment_type_display',
            'salary_min', 'salary_max', 'salary_currency', 'salary_range',
            'experience_required', 'source_platform', 'published_at',
            'is_active', 'archived', 'premium', 'age_in_days', 'is_fresh',
            'required_skills_count'
        ]
    
    def get_salary_range(self, obj):
        return obj.get_salary_range()
    
    def get_age_in_days(self, obj):
        return obj.get_age_in_days()
    
    def get_is_fresh(self, obj):
        return obj.is_fresh()
    
    def get_required_skills_count(self, obj):
        return obj.job_skills.filter(is_required=True).count()


class JobPostingDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed job view"""
    work_type_display = serializers.CharField(source='get_work_type_display', read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    salary_range = serializers.SerializerMethodField()
    age_in_days = serializers.SerializerMethodField()
    is_fresh = serializers.SerializerMethodField()
    
    # Related data
    job_skills = JobSkillSerializer(many=True, read_only=True)
    categories = serializers.SerializerMethodField()
    required_skills = serializers.SerializerMethodField()
    optional_skills = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'external_id', 'title', 'company_name', 'company_id', 'company_size',
            'location', 'area_id', 'work_type', 'work_type_display',
            'employment_type', 'employment_type_display', 'experience_required',
            'salary_min', 'salary_max', 'salary_currency', 'salary_gross', 'salary_range',
            'source_platform', 'posting_url', 'alternate_url',
            'description_text', 'key_skills', 'professional_roles',
            'published_at', 'created_at', 'is_active', 'archived',
            'premium', 'has_test', 'response_letter_required',
            'age_in_days', 'is_fresh', 'job_skills', 'categories',
            'required_skills', 'optional_skills'
        ]
    
    def get_salary_range(self, obj):
        return obj.get_salary_range()
    
    def get_age_in_days(self, obj):
        return obj.get_age_in_days()
    
    def get_is_fresh(self, obj):
        return obj.is_fresh()
    
    def get_categories(self, obj):
        categories = obj.get_categories()
        return JobCategorySerializer(categories, many=True).data
    
    def get_required_skills(self, obj):
        required = obj.get_required_skills()
        return JobSkillSerializer(required, many=True).data
    
    def get_optional_skills(self, obj):
        optional = obj.job_skills.filter(is_required=False)
        return JobSkillSerializer(optional, many=True).data


class JobSearchSerializer(serializers.Serializer):
    """Serializer for job search parameters"""
    query = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    work_type = serializers.ChoiceField(
        choices=['remote', 'onsite', 'hybrid'],
        required=False
    )
    employment_type = serializers.ChoiceField(
        choices=['full_time', 'part_time', 'contract', 'internship', 'freelance'],
        required=False
    )
    min_salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    max_salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    skills = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of skill IDs"
    )
    category = serializers.IntegerField(required=False)
    is_fresh = serializers.BooleanField(required=False)
    premium_only = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        choices=['published_at', '-published_at', 'salary_min', '-salary_min', 'title', '-title'],
        required=False,
        default='-published_at'
    )


class JobMatchSerializer(serializers.Serializer):
    """Serializer for job matching results"""
    job = JobPostingListSerializer()
    match_percentage = serializers.FloatField()
    matching_skills_count = serializers.IntegerField()
    total_required_skills = serializers.IntegerField()
    matching_skills = serializers.ListField(child=serializers.CharField())
    missing_skills = serializers.ListField(child=serializers.CharField())


class JobStatisticsSerializer(serializers.Serializer):
    """Serializer for job statistics"""
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    fresh_jobs = serializers.IntegerField()
    jobs_by_work_type = serializers.DictField()
    jobs_by_location = serializers.DictField()
    average_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    salary_range = serializers.DictField()
    top_companies = serializers.ListField()
    jobs_with_salary = serializers.IntegerField()