from django.db import models
from django.utils import timezone
from skills.models import Skill


class JobCategory(models.Model):
    """
    Categories for organizing job postings
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # Add external_id for mapping to hh.uz professional_role IDs
    external_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="External ID from job platform (e.g., hh.uz professional_role id)"
    )
    
    class Meta:
        db_table = 'job_categories'
        verbose_name = 'Job Category'
        verbose_name_plural = 'Job Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_active_jobs_count(self):
        """Count active jobs in this category"""
        return self.job_posting_categories.filter(
            job_posting__is_active=True
        ).count()


class JobPosting(models.Model):
    """
    Job postings scraped from job platforms
    This is where all scraped job data is stored
    """
    WORK_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]
    
    PLATFORM_CHOICES = [
        ('hh.uz', 'hh.uz'),
        ('other', 'Other'),
    ]
    
    # External ID from API (IMPORTANT for preventing duplicates)
    external_id = models.CharField(
        max_length=100,
        help_text="Vacancy ID from the platform API"
    )
    
    # Basic Information
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    company_size = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., 1-10, 11-50, 51-200, etc."
    )
    
    # Company ID from API
    company_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Company ID from platform"
    )
    
    location = models.CharField(max_length=255)
    
    # Area information from API
    area_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Area/Region ID from platform"
    )
    
    # Job Type
    work_type = models.CharField(
        max_length=20,
        choices=WORK_TYPE_CHOICES,
        default='onsite'
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='full_time'
    )
    
    # Salary Information
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    salary_currency = models.CharField(
        max_length=10,
        default='UZS',
        help_text="Currency code: UZS, USD, EUR, etc."
    )
    
    # Salary gross flag
    salary_gross = models.BooleanField(
        default=False,
        help_text="True if salary is before taxes"
    )
    
    # Requirements
    experience_required = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., noExperience, between1And3, between3And6, moreThan6"
    )
    
    # Source Information
    source_platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES,
        default='hh.uz'
    )
    posting_url = models.URLField(
        max_length=500,
        help_text="Original job posting URL"
    )
    
    # Alternate URL
    alternate_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Human-readable URL from API"
    )
    
    # Description
    description_text = models.TextField(
        help_text="Full job description including requirements"
    )
    
    # Key skills from API (will be extracted separately)
    key_skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of key skills from API response"
    )
    
    # Professional roles
    professional_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="Professional role IDs from API"
    )
    
    # Status & Timestamps
    is_active = models.BooleanField(
        default=True,
        help_text="False if job posting is expired or removed"
    )
    
    # CHANGED: posted_date to published_at (matches API field name)
    published_at = models.DateTimeField(
        help_text="Date when job was originally published (from API)"
    )
    
    # Created at from API
    created_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When vacancy was created (from API)"
    )
    
    # Archived flag
    archived = models.BooleanField(
        default=False,
        help_text="True if vacancy is archived on platform"
    )
    
    scraped_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When this job was scraped by our system"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Last time this record was updated"
    )
    
    # Premium flag
    premium = models.BooleanField(
        default=False,
        help_text="True if this is a premium vacancy"
    )
    
    # Has test flag
    has_test = models.BooleanField(
        default=False,
        help_text="True if vacancy has test assignment"
    )
    
    # Response letter required
    response_letter_required = models.BooleanField(
        default=False,
        help_text="True if cover letter is required"
    )
    
    class Meta:
        db_table = 'job_postings'
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
        ordering = ['-published_at', '-scraped_date']
        
        # IMPORTANT: Composite unique constraint
        unique_together = ['external_id', 'source_platform']
        
        indexes = [
            models.Index(fields=['external_id', 'source_platform']),
            models.Index(fields=['source_platform']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-published_at']),
            models.Index(fields=['company_name']),
            models.Index(fields=['location']),
            models.Index(fields=['work_type']),
            models.Index(fields=['archived']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company_name}"
    
    def deactivate(self):
        """Mark job posting as inactive"""
        self.is_active = False
        self.save(update_fields=['is_active', 'last_updated'])
    
    def get_required_skills(self):
        """Get list of required skills for this job"""
        return self.job_skills.filter(is_required=True).select_related('skill')
    
    def get_all_skills(self):
        """Get all skills (required and optional) for this job"""
        return self.job_skills.all().select_related('skill')
    
    def get_salary_range(self):
        """Get formatted salary range string"""
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f} - {self.salary_max:,.0f} {self.salary_currency}"
        elif self.salary_min:
            return f"From {self.salary_min:,.0f} {self.salary_currency}"
        elif self.salary_max:
            return f"Up to {self.salary_max:,.0f} {self.salary_currency}"
        return "Not specified"
    
    def get_age_in_days(self):
        """Calculate how many days ago this job was posted"""
        if self.published_at:
            delta = timezone.now() - self.published_at
            return delta.days
        return None
    
    def is_fresh(self):
        """Check if job was posted within last 7 days"""
        age = self.get_age_in_days()
        return age is not None and age <= 7
    
    def get_categories(self):
        """Get all categories for this job"""
        return JobCategory.objects.filter(
            job_posting_categories__job_posting=self
        )


class JobSkill(models.Model):
    """
    Junction table linking job postings to required skills
    """
    IMPORTANCE_CHOICES = [
        ('critical', 'Critical'),
        ('important', 'Important'),
        ('nice_to_have', 'Nice to Have'),
    ]
    
    job_posting = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='job_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='job_skills'
    )
    is_required = models.BooleanField(
        default=True,
        help_text="True if skill is required, False if optional"
    )
    importance_level = models.CharField(
        max_length=20,
        choices=IMPORTANCE_CHOICES,
        default='important'
    )
    
    class Meta:
        db_table = 'job_skills'
        verbose_name = 'Job Skill'
        verbose_name_plural = 'Job Skills'
        unique_together = ['job_posting', 'skill']
        ordering = ['-is_required', 'importance_level']
        indexes = [
            models.Index(fields=['job_posting', 'skill']),
            models.Index(fields=['skill', 'is_required']),
        ]
    
    def __str__(self):
        required = "Required" if self.is_required else "Optional"
        return f"{self.job_posting.title} - {self.skill.name} ({required})"


class JobPostingCategory(models.Model):
    """
    Junction table linking job postings to categories
    A job can belong to multiple categories
    """
    job_posting = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='job_posting_categories'
    )
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.CASCADE,
        related_name='job_posting_categories'
    )
    
    class Meta:
        db_table = 'job_posting_categories'
        verbose_name = 'Job Posting Category'
        verbose_name_plural = 'Job Posting Categories'
        unique_together = ['job_posting', 'category']
    
    def __str__(self):
        return f"{self.job_posting.title} - {self.category.name}"