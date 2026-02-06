"""
CV App Models
=============
backend/apps/cv/models.py

AI-powered CV generation and management.
Supports multiple templates and languages.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class CV(models.Model):
    """
    User's CV/Resume.
    Can have multiple CVs with different templates/languages.
    """
    
    TEMPLATE_CHOICES = [
        ('modern', _('Modern')),
        ('classic', _('Classic')),
        ('creative', _('Creative')),
        ('minimalist', _('Minimalist')),
        ('professional', _('Professional')),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ru', _('Russian')),
        ('uz', _('Uzbek')),
    ]
    
    cv_id = models.AutoField(primary_key=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cvs',
        verbose_name=_('user')
    )
    
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('CV title for your reference (e.g., "Software Engineer CV")')
    )
    
    template_type = models.CharField(
        _('template type'),
        max_length=20,
        choices=TEMPLATE_CHOICES,
        default='modern'
    )
    
    language_code = models.CharField(
        _('language'),
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    
    is_default = models.BooleanField(
        _('default CV'),
        default=False,
        help_text=_('Set as default CV for job applications')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        db_table = 'cvs'
        ordering = ['-is_default', '-updated_at']
        verbose_name = _('CV')
        verbose_name_plural = _('CVs')
    
    def __str__(self):
        default_label = ' [DEFAULT]' if self.is_default else ''
        return f"{self.user.username} - {self.title}{default_label}"
    
    def save(self, *args, **kwargs):
        """Ensure only one default CV per user."""
        if self.is_default:
            # Set all other CVs of this user to non-default
            CV.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(
                cv_id=self.cv_id
            ).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_sections_by_order(self):
        """Get CV sections ordered by display_order."""
        return self.cv_sections.filter(is_visible=True).order_by('display_order')


class CVSection(models.Model):
    """
    Individual sections of a CV.
    Each section contains structured JSON data.
    """
    
    SECTION_TYPE_CHOICES = [
        ('personal_info', _('Personal Information')),
        ('summary', _('Professional Summary')),
        ('experience', _('Work Experience')),
        ('education', _('Education')),
        ('skills', _('Skills')),
        ('projects', _('Projects')),
        ('certifications', _('Certifications')),
        ('languages', _('Languages')),
        ('awards', _('Awards & Achievements')),
    ]
    
    section_id = models.AutoField(primary_key=True)
    
    cv = models.ForeignKey(
        CV,
        on_delete=models.CASCADE,
        related_name='cv_sections',
        verbose_name=_('CV')
    )
    
    section_type = models.CharField(
        _('section type'),
        max_length=20,
        choices=SECTION_TYPE_CHOICES
    )
    
    content = models.JSONField(
        _('content'),
        help_text=_('Section content in JSON format')
    )
    
    display_order = models.PositiveIntegerField(
        _('display order'),
        default=0,
        help_text=_('Order in which section appears in CV')
    )
    
    is_visible = models.BooleanField(
        _('visible'),
        default=True,
        help_text=_('Show/hide this section in CV')
    )
    
    class Meta:
        db_table = 'cv_sections'
        unique_together = [('cv', 'section_type')]
        ordering = ['cv', 'display_order']
        verbose_name = _('CV section')
        verbose_name_plural = _('CV sections')
    
    def __str__(self):
        return f"{self.cv.title} - {self.get_section_type_display()}"


"""
Example CVSection.content JSON structures:

SUMMARY:
{
    "text": "Experienced software engineer with 5+ years..."
}

EXPERIENCE:
{
    "positions": [
        {
            "title": "Senior Developer",
            "company": "TechCorp",
            "location": "Tashkent, UZ",
            "start_date": "2020-01",
            "end_date": "2023-05",
            "current": false,
            "responsibilities": [
                "Led team of 5 developers",
                "Implemented microservices architecture"
            ],
            "achievements": [
                "Reduced deployment time by 40%"
            ]
        }
    ]
}

EDUCATION:
{
    "degrees": [
        {
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "institution": "TUIT",
            "location": "Tashkent, UZ",
            "start_date": "2015-09",
            "end_date": "2019-06",
            "gpa": "3.8",
            "honors": "Cum Laude"
        }
    ]
}

SKILLS:
{
    "categories": [
        {
            "name": "Programming Languages",
            "skills": ["Python", "JavaScript", "Java"]
        },
        {
            "name": "Frameworks",
            "skills": ["Django", "React", "Node.js"]
        }
    ]
}

PROJECTS:
{
    "projects": [
        {
            "name": "E-commerce Platform",
            "description": "Full-stack web application...",
            "technologies": ["Django", "React", "PostgreSQL"],
            "github_url": "https://github.com/user/project",
            "live_url": "https://demo.example.com",
            "highlights": [
                "Built RESTful API",
                "Implemented payment integration"
            ]
        }
    ]
}

CERTIFICATIONS:
{
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "date": "2022-08",
            "credential_id": "ABC123XYZ",
            "url": "https://..."
        }
    ]
}

LANGUAGES:
{
    "languages": [
        {
            "language": "English",
            "proficiency": "Native / Fluent / Professional / Basic"
        },
        {
            "language": "Russian",
            "proficiency": "Professional"
        }
    ]
}

AWARDS:
{
    "awards": [
        {
            "title": "Employee of the Year",
            "issuer": "TechCorp",
            "date": "2022-12",
            "description": "Recognized for outstanding contributions..."
        }
    ]
}
"""