"""
CV generation and management models
"""
from django.db import models
from django.conf import settings
from skills.models import Skill


class UserCV(models.Model):
    """
    Generated CV for a user
    """
    TEMPLATE_CHOICES = [
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('minimal', 'Minimal'),
        ('professional', 'Professional'),
        ('creative', 'Creative'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cvs'
    )
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_CHOICES,
        default='modern'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the user's primary/active CV?"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to generated PDF/DOCX file"
    )
    
    class Meta:
        db_table = 'user_cvs'
        verbose_name = 'User CV'
        verbose_name_plural = 'User CVs'
        ordering = ['-created_date']
    
    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.user.email} - {self.get_template_type_display()}{primary}"
    
    def set_as_primary(self):
        """Set this CV as primary and unset others"""
        # Unset all other primary CVs for this user
        UserCV.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        # Set this one as primary
        self.is_primary = True
        self.save(update_fields=['is_primary'])
    
    def get_sections(self):
        """Get all sections for this CV"""
        return self.cv_sections.order_by('display_order')


class CVSection(models.Model):
    """
    Sections of a CV (Summary, Experience, Education, Skills, etc.)
    """
    SECTION_TYPES = [
        ('summary', 'Summary'),
        ('experience', 'Work Experience'),
        ('education', 'Education'),
        ('skills', 'Skills'),
        ('projects', 'Projects'),
        ('certifications', 'Certifications'),
        ('languages', 'Languages'),
        ('custom', 'Custom Section'),
    ]
    
    cv = models.ForeignKey(
        UserCV,
        on_delete=models.CASCADE,
        related_name='cv_sections'
    )
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    content_json = models.JSONField(
        help_text="Structured content for this section"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order in which to display sections"
    )
    
    class Meta:
        db_table = 'cv_sections'
        verbose_name = 'CV Section'
        verbose_name_plural = 'CV Sections'
        ordering = ['cv', 'display_order']
    
    def __str__(self):
        return f"{self.cv.user.email} - {self.get_section_type_display()}"


class WorkExperience(models.Model):
    """
    User's work experience history
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='work_experiences'
    )
    company_name = models.CharField(max_length=255)
    position_title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(
        default=False,
        help_text="Currently working here"
    )
    description = models.TextField(
        help_text="Job responsibilities and achievements"
    )
    location = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'work_experiences'
        verbose_name = 'Work Experience'
        verbose_name_plural = 'Work Experiences'
        ordering = ['-start_date']
    
    def __str__(self):
        current = " (Current)" if self.is_current else ""
        return f"{self.user.email} - {self.position_title} at {self.company_name}{current}"
    
    def get_duration(self):
        """Calculate duration of employment"""
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        end = self.end_date if self.end_date else date.today()
        delta = relativedelta(end, self.start_date)
        
        years = delta.years
        months = delta.months
        
        if years > 0 and months > 0:
            return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
        elif years > 0:
            return f"{years} year{'s' if years != 1 else ''}"
        elif months > 0:
            return f"{months} month{'s' if months != 1 else ''}"
        else:
            return "Less than a month"


class Education(models.Model):
    """
    User's education history
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='education'
    )
    institution_name = models.CharField(max_length=255)
    degree = models.CharField(
        max_length=255,
        help_text="e.g., Bachelor's, Master's, PhD"
    )
    field_of_study = models.CharField(
        max_length=255,
        help_text="e.g., Computer Science, Software Engineering"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(
        max_length=50,
        blank=True,
        help_text="GPA or grade"
    )
    description = models.TextField(
        blank=True,
        help_text="Achievements, activities, coursework"
    )
    
    class Meta:
        db_table = 'education'
        verbose_name = 'Education'
        verbose_name_plural = 'Education'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.degree} in {self.field_of_study}"


class Project(models.Model):
    """
    User's projects (personal, professional, or academic)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    project_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Live demo or project website"
    )
    github_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="GitHub repository"
    )
    technologies_used = models.JSONField(
        default=list,
        help_text="List of technologies/tools used"
    )
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class ProjectSkill(models.Model):
    """
    Links skills to projects
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='project_uses'
    )
    
    class Meta:
        db_table = 'project_skills'
        verbose_name = 'Project Skill'
        verbose_name_plural = 'Project Skills'
        unique_together = ['project', 'skill']
    
    def __str__(self):
        return f"{self.project.title} - {self.skill.name}"


class UploadedCV(models.Model):
    """
    CV files uploaded by users (for NLP extraction)
    """
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
    ]
    
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_cvs'
    )
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    upload_date = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS,
        default='pending'
    )
    extracted_data_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extracted data from CV (skills, experience, etc.)"
    )
    
    class Meta:
        db_table = 'uploaded_cvs'
        verbose_name = 'Uploaded CV'
        verbose_name_plural = 'Uploaded CVs'
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.original_filename} ({self.get_processing_status_display()})"
    
    def mark_processing(self):
        """Mark CV as being processed"""
        self.processing_status = 'processing'
        self.save(update_fields=['processing_status'])
    
    def mark_completed(self, extracted_data):
        """Mark CV processing as completed"""
        self.processing_status = 'completed'
        self.extracted_data_json = extracted_data
        self.save(update_fields=['processing_status', 'extracted_data_json'])
    
    def mark_failed(self):
        """Mark CV processing as failed"""
        self.processing_status = 'failed'
        self.save(update_fields=['processing_status'])


class CVExtractionLog(models.Model):
    """
    Logs for CV extraction process
    """
    uploaded_cv = models.ForeignKey(
        UploadedCV,
        on_delete=models.CASCADE,
        related_name='extraction_logs'
    )
    extraction_date = models.DateTimeField(auto_now_add=True)
    skills_extracted_count = models.IntegerField(default=0)
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence of extraction (0-1)"
    )
    errors_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Any errors or warnings during extraction"
    )
    
    class Meta:
        db_table = 'cv_extraction_logs'
        verbose_name = 'CV Extraction Log'
        verbose_name_plural = 'CV Extraction Logs'
        ordering = ['-extraction_date']
    
    def __str__(self):
        return f"{self.uploaded_cv.user.email} - {self.extraction_date.date()}"