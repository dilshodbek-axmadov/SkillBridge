"""
Recruiter API serializers.
"""

from rest_framework import serializers

from apps.cv.models import CV
from apps.jobs.models import JobPosting
from apps.skills.models import UserSkill
from apps.users.models import User, UserProfile
from apps.recruiters.models import RecruiterSavedSearch, SavedCandidate


class CandidateCardSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    current_job_position = serializers.CharField(source='profile.current_job_position', allow_null=True)
    desired_role = serializers.CharField(source='profile.desired_role', allow_null=True)
    experience_level = serializers.CharField(source='profile.experience_level', allow_null=True)
    location = serializers.CharField(source='profile.location', allow_null=True)
    top_skills = serializers.SerializerMethodField()
    years_experience_total = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'current_job_position',
            'desired_role',
            'experience_level',
            'location',
            'top_skills',
            'years_experience_total',
            'created_at',
        ]

    def get_full_name(self, obj):
        return obj.full_name

    def get_top_skills(self, obj):
        skills = UserSkill.objects.filter(user=obj).select_related('skill').order_by('-is_primary', '-years_of_experience')[:8]
        return [s.skill.name_en for s in skills]

    def get_years_experience_total(self, obj):
        total = sum(s.years_of_experience for s in UserSkill.objects.filter(user=obj))
        return round(total, 1)


class CandidateProfileDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    cvs = serializers.SerializerMethodField()
    portfolio_projects = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'phone',
            'created_at',
            'profile',
            'skills',
            'cvs',
            'portfolio_projects',
        ]

    def get_full_name(self, obj):
        return obj.full_name

    def get_profile(self, obj):
        p = getattr(obj, 'profile', None)
        if not p:
            return {}
        return {
            'current_job_position': p.current_job_position,
            'desired_role': p.desired_role,
            'experience_level': p.experience_level,
            'bio': p.bio,
            'location': p.location,
            'github_url': p.github_url,
            'linkedin_url': p.linkedin_url,
            'portfolio_url': p.portfolio_url,
            'open_to_recruiters': p.open_to_recruiters,
        }

    def get_skills(self, obj):
        qs = UserSkill.objects.filter(user=obj).select_related('skill').order_by('-is_primary', 'skill__name_en')
        return [
            {
                'skill_id': s.skill_id,
                'name': s.skill.name_en,
                'category': s.skill.category,
                'proficiency_level': s.proficiency_level,
                'years_of_experience': s.years_of_experience,
                'is_primary': s.is_primary,
            }
            for s in qs
        ]

    def get_cvs(self, obj):
        cvs = CV.objects.filter(user=obj).order_by('-is_default', '-updated_at')
        return [
            {
                'cv_id': cv.cv_id,
                'title': cv.title,
                'language_code': cv.language_code,
                'template_type': cv.template_type,
                'is_default': cv.is_default,
                'updated_at': cv.updated_at,
            }
            for cv in cvs
        ]

    def get_portfolio_projects(self, obj):
        rows = obj.user_projects.select_related('project').filter(status='completed').order_by('-completed_at')[:10]
        return [
            {
                'project_id': up.project_id,
                'title': up.project.title,
                'target_role': up.project.target_role,
                'github_url': up.github_url,
                'live_demo_url': up.live_demo_url,
                'completed_at': up.completed_at,
            }
            for up in rows
        ]


class SavedCandidateSerializer(serializers.ModelSerializer):
    candidate = CandidateCardSerializer(read_only=True)
    candidate_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = SavedCandidate
        fields = ['saved_id', 'candidate', 'candidate_id', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['saved_id', 'created_at', 'updated_at', 'candidate']


class RecruiterSavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruiterSavedSearch
        fields = ['search_id', 'name', 'filters', 'created_at', 'updated_at']
        read_only_fields = ['search_id', 'created_at', 'updated_at']


class RecruiterJobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosting
        fields = [
            'job_id',
            'job_title',
            'company_name',
            'job_category',
            'job_description',
            'experience_required',
            'employment_type',
            'salary_min',
            'salary_max',
            'salary_currency',
            'location',
            'is_remote',
            'posted_date',
            'deadline_date',
            'job_url',
            'is_active',
            'source',
            'external_job_id',
            'updated_at',
        ]
        read_only_fields = ['job_id', 'source', 'external_job_id', 'updated_at']

