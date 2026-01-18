"""
Learning roadmap and resource models
"""
from django.db import models
from django.conf import settings
from skills.models import Skill
from career.models import Role


class LearningRoadmap(models.Model):
    """
    Personalized learning roadmap for a user targeting a specific role
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_roadmaps'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='learning_roadmaps'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    completion_percentage = models.FloatField(
        default=0.0,
        help_text="Overall roadmap completion (0-100)"
    )
    estimated_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Estimated date to complete roadmap"
    )
    
    class Meta:
        db_table = 'learning_roadmaps'
        verbose_name = 'Learning Roadmap'
        verbose_name_plural = 'Learning Roadmaps'
        ordering = ['-created_date']
        unique_together = ['user', 'role']
    
    def __str__(self):
        return f"{self.user.email} - {self.role.title} Roadmap"
    
    def update_completion_percentage(self):
        """
        Calculate completion based on completed roadmap items
        """
        total_items = self.roadmap_items.count()
        if total_items == 0:
            self.completion_percentage = 0.0
        else:
            completed_items = self.roadmap_items.filter(status='completed').count()
            self.completion_percentage = (completed_items / total_items) * 100
        
        self.save(update_fields=['completion_percentage', 'last_updated'])
        return self.completion_percentage
    
    def get_next_skill(self):
        """Get the next skill to learn (pending items in order)"""
        return self.roadmap_items.filter(
            status='pending'
        ).order_by('sequence_order').first()
    
    def get_in_progress_skills(self):
        """Get skills currently being learned"""
        return self.roadmap_items.filter(status='in_progress')


class RoadmapItem(models.Model):
    """
    Individual skill in a learning roadmap
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    roadmap = models.ForeignKey(
        LearningRoadmap,
        on_delete=models.CASCADE,
        related_name='roadmap_items'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='roadmap_items'
    )
    sequence_order = models.IntegerField(
        help_text="Order in which to learn (1, 2, 3...)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    estimated_duration_weeks = models.IntegerField(
        default=4,
        help_text="Estimated weeks to learn this skill"
    )
    started_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'roadmap_items'
        verbose_name = 'Roadmap Item'
        verbose_name_plural = 'Roadmap Items'
        ordering = ['roadmap', 'sequence_order']
        unique_together = ['roadmap', 'skill']
    
    def __str__(self):
        return f"{self.roadmap.user.email} - {self.skill.name} (Step {self.sequence_order})"
    
    def mark_in_progress(self):
        """Mark this skill as currently being learned"""
        from django.utils import timezone
        self.status = 'in_progress'
        if not self.started_date:
            self.started_date = timezone.now()
        self.save(update_fields=['status', 'started_date'])
        
        # Update roadmap completion
        self.roadmap.update_completion_percentage()
    
    def mark_completed(self):
        """Mark this skill as completed"""
        from django.utils import timezone
        from skills.models import UserSkill, SkillLevel
        
        self.status = 'completed'
        self.completed_date = timezone.now()
        self.save(update_fields=['status', 'completed_date'])
        
        # Update user's skills (mark as learned)
        try:
            user_skill = UserSkill.objects.get(
                user=self.roadmap.user,
                skill=self.skill
            )
            user_skill.mark_as_learned()
        except UserSkill.DoesNotExist:
            # Create new UserSkill if doesn't exist
            beginner_level = SkillLevel.objects.filter(level_order=1).first()
            UserSkill.objects.create(
                user=self.roadmap.user,
                skill=self.skill,
                level=beginner_level,
                status='learned',
                self_assessed=True
            )
        
        # Update roadmap completion
        self.roadmap.update_completion_percentage()
    
    def get_recommended_resources(self):
        """Get recommended learning resources for this skill"""
        return self.roadmap_resources.select_related('resource')


class LearningResource(models.Model):
    """
    Learning resources (courses, tutorials, books, etc.)
    """
    RESOURCE_TYPES = [
        ('course', 'Course'),
        ('tutorial', 'Tutorial'),
        ('book', 'Book'),
        ('documentation', 'Documentation'),
        ('video', 'Video'),
        ('article', 'Article'),
        ('practice', 'Practice Platform'),
    ]
    
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='learning_resources'
    )
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    url = models.URLField(max_length=500)
    platform = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., Udemy, Coursera, YouTube, FreeCodeCamp"
    )
    is_free = models.BooleanField(default=False)
    duration_hours = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total duration in hours"
    )
    rating = models.FloatField(
        null=True,
        blank=True,
        help_text="Rating out of 5"
    )
    language = models.CharField(
        max_length=50,
        default='English',
        help_text="Language of the resource"
    )
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'learning_resources'
        verbose_name = 'Learning Resource'
        verbose_name_plural = 'Learning Resources'
        ordering = ['-rating', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.resource_type})"


class RoadmapResource(models.Model):
    """
    Links learning resources to specific roadmap items
    """
    roadmap_item = models.ForeignKey(
        RoadmapItem,
        on_delete=models.CASCADE,
        related_name='roadmap_resources'
    )
    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name='roadmap_assignments'
    )
    is_recommended = models.BooleanField(
        default=True,
        help_text="Is this resource recommended for this roadmap item?"
    )
    
    class Meta:
        db_table = 'roadmap_resources'
        verbose_name = 'Roadmap Resource'
        verbose_name_plural = 'Roadmap Resources'
        unique_together = ['roadmap_item', 'resource']
    
    def __str__(self):
        return f"{self.roadmap_item.skill.name} - {self.resource.title}"