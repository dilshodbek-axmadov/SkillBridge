"""
CV Service
==========
Business logic for CV creation, auto-population, and template management.
"""

from django.db import transaction
from apps.cv.models import CV, CVSection
from apps.users.models import UserProfile
from apps.skills.models import UserSkill
from apps.projects.models import UserProject
from apps.learning.models import LearningRoadmap, RoadmapItem


# CV Template definitions
CV_TEMPLATES = {
    'modern': {
        'name': 'Modern',
        'sections_order': [
            'personal_info', 'summary', 'skills', 'experience',
            'projects', 'education', 'certifications', 'languages',
        ],
        'description': 'Clean, modern layout with skills highlighted first.',
    },
    'classic': {
        'name': 'Classic',
        'sections_order': [
            'personal_info', 'summary', 'experience', 'education',
            'skills', 'projects', 'certifications', 'languages',
        ],
        'description': 'Traditional CV format with experience first.',
    },
    'creative': {
        'name': 'Creative',
        'sections_order': [
            'personal_info', 'summary', 'projects', 'skills',
            'experience', 'education', 'certifications', 'awards', 'languages',
        ],
        'description': 'Portfolio-focused layout with projects highlighted.',
    },
}


class CVService:
    """Service for CV management and auto-population."""

    def __init__(self, user):
        self.user = user

    def create_cv(self, title, template_type='modern', language_code='en',
                  is_default=False, sections=None):
        """
        Create a new CV with optional sections.

        Args:
            title: CV title
            template_type: Template to use
            language_code: CV language
            is_default: Set as default CV
            sections: List of dicts with section_type, content, display_order
        """
        with transaction.atomic():
            cv = CV.objects.create(
                user=self.user,
                title=title,
                template_type=template_type,
                language_code=language_code,
                is_default=is_default,
            )

            if sections:
                for idx, section_data in enumerate(sections):
                    CVSection.objects.create(
                        cv=cv,
                        section_type=section_data['section_type'],
                        content=section_data.get('content', {}),
                        display_order=section_data.get('display_order', idx),
                        is_visible=section_data.get('is_visible', True),
                    )

        return cv

    def auto_populate(self, cv_id=None, template_type='modern',
                      title=None, language_code='en'):
        """
        Create or populate a CV from the user's profile data.

        Pulls data from:
        - UserProfile (personal info, summary)
        - UserSkill (skills section)
        - UserProject (completed projects)
        - LearningRoadmap completed items
        """
        with transaction.atomic():
            if cv_id:
                cv = CV.objects.get(cv_id=cv_id, user=self.user)
                # Clear existing sections
                cv.cv_sections.all().delete()
            else:
                cv = CV.objects.create(
                    user=self.user,
                    title=title or f"{self.user.full_name} - CV",
                    template_type=template_type,
                    language_code=language_code,
                )

            template = CV_TEMPLATES.get(template_type, CV_TEMPLATES['modern'])
            sections_order = template['sections_order']

            for order, section_type in enumerate(sections_order):
                content = self._build_section_content(section_type)
                if content:
                    CVSection.objects.create(
                        cv=cv,
                        section_type=section_type,
                        content=content,
                        display_order=order,
                        is_visible=True,
                    )

        return cv

    def _build_section_content(self, section_type):
        """Build section content from user data."""
        builders = {
            'personal_info': self._build_personal_info,
            'summary': self._build_summary,
            'skills': self._build_skills,
            'experience': self._build_experience,
            'education': self._build_education,
            'projects': self._build_projects,
            'certifications': self._build_certifications,
            'languages': self._build_languages,
            'awards': self._build_awards,
        }
        builder = builders.get(section_type)
        if builder:
            return builder()
        return {}

    def _build_personal_info(self):
        """Build personal info from User and UserProfile."""
        data = {
            'full_name': self.user.full_name,
            'email': self.user.email,
            'phone': self.user.phone or '',
        }
        try:
            profile = self.user.profile
            data.update({
                'location': profile.location or '',
                'current_position': profile.current_job_position or '',
                'github_url': profile.github_url or '',
                'linkedin_url': profile.linkedin_url or '',
                'portfolio_url': profile.portfolio_url or '',
            })
        except UserProfile.DoesNotExist:
            pass
        return data

    def _build_summary(self):
        """Build summary from profile bio and desired role."""
        text = ''
        try:
            profile = self.user.profile
            if profile.bio:
                text = profile.bio
            elif profile.desired_role:
                text = (
                    f"Aspiring {profile.desired_role} with a passion for "
                    f"technology and continuous learning."
                )
        except UserProfile.DoesNotExist:
            pass
        return {'text': text}

    def _build_skills(self):
        """Build skills from UserSkill records, grouped by category."""
        user_skills = UserSkill.objects.filter(
            user=self.user
        ).select_related('skill').order_by('-is_primary', 'skill__category')

        if not user_skills.exists():
            return {}

        categories = {}
        for us in user_skills:
            cat_display = us.skill.get_category_display()
            if cat_display not in categories:
                categories[cat_display] = []
            categories[cat_display].append(us.skill.name_en)

        return {
            'categories': [
                {'name': name, 'skills': skills}
                for name, skills in categories.items()
            ]
        }

    def _build_experience(self):
        """Return empty experience for user to fill manually."""
        return {'positions': []}

    def _build_education(self):
        """Return empty education for user to fill manually."""
        return {'degrees': []}

    def _build_projects(self):
        """Build projects from completed UserProject records."""
        user_projects = UserProject.objects.filter(
            user=self.user,
            status='completed',
        ).select_related('project')

        if not user_projects.exists():
            # Also check in-progress projects
            user_projects = UserProject.objects.filter(
                user=self.user,
                status='in_progress',
            ).select_related('project')

        projects = []
        for up in user_projects[:5]:  # Limit to 5 projects
            project_skills = [
                ps.skill.name_en
                for ps in up.project.project_skills.select_related('skill').all()
            ]
            projects.append({
                'name': up.project.title,
                'description': up.project.description[:300] if up.project.description else '',
                'technologies': project_skills,
                'github_url': up.github_url or '',
                'live_url': up.live_demo_url or '',
                'highlights': [],
            })

        return {'projects': projects}

    def _build_certifications(self):
        """Return empty certifications for user to fill."""
        return {'certifications': []}

    def _build_languages(self):
        """Build languages from user's preferred language."""
        languages = []
        lang_map = {'en': 'English', 'ru': 'Russian', 'uz': 'Uzbek'}
        pref = self.user.preferred_language
        if pref in lang_map:
            languages.append({
                'language': lang_map[pref],
                'proficiency': 'Native',
            })
        return {'languages': languages}

    def _build_awards(self):
        """Return empty awards for user to fill."""
        return {'awards': []}

    def update_sections(self, cv_id, sections_data):
        """
        Update CV sections (create/update/reorder).

        Args:
            cv_id: CV primary key
            sections_data: List of dicts with section_type, content,
                           display_order, is_visible
        """
        cv = CV.objects.get(cv_id=cv_id, user=self.user)

        with transaction.atomic():
            for section_data in sections_data:
                section_type = section_data['section_type']
                defaults = {
                    'content': section_data.get('content', {}),
                    'display_order': section_data.get('display_order', 0),
                    'is_visible': section_data.get('is_visible', True),
                }
                CVSection.objects.update_or_create(
                    cv=cv,
                    section_type=section_type,
                    defaults=defaults,
                )

        return cv

    def switch_template(self, cv_id, new_template_type):
        """
        Switch CV template and reorder sections accordingly.
        """
        cv = CV.objects.get(cv_id=cv_id, user=self.user)
        template = CV_TEMPLATES.get(new_template_type)
        if not template:
            raise ValueError(f"Unknown template: {new_template_type}")

        with transaction.atomic():
            cv.template_type = new_template_type
            cv.save(update_fields=['template_type'])

            # Reorder existing sections based on new template
            sections_order = template['sections_order']
            for section in cv.cv_sections.all():
                if section.section_type in sections_order:
                    section.display_order = sections_order.index(section.section_type)
                else:
                    section.display_order = len(sections_order)
                section.save(update_fields=['display_order'])

        return cv

    def get_cv_detail(self, cv_id):
        """Get CV with all sections ordered."""
        return CV.objects.prefetch_related(
            'cv_sections'
        ).get(cv_id=cv_id, user=self.user)

    def list_cvs(self):
        """List all user CVs."""
        from django.db.models import Count
        return CV.objects.filter(user=self.user).annotate(
            section_count=Count('cv_sections')
        )

    def delete_cv(self, cv_id):
        """Delete a CV."""
        cv = CV.objects.get(cv_id=cv_id, user=self.user)
        cv.delete()

    @staticmethod
    def get_available_templates():
        """Return available template definitions."""
        return {
            key: {
                'name': val['name'],
                'description': val['description'],
                'sections_order': val['sections_order'],
            }
            for key, val in CV_TEMPLATES.items()
        }
