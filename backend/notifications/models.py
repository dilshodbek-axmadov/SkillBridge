"""
User notifications and activity logging models
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class UserNotification(models.Model):
    """
    Notifications for users (new job matches, skill recommendations, etc.)
    """
    NOTIFICATION_TYPES = [
        ('skill_recommendation', 'Skill Recommendation'),
        ('job_match', 'Job Match'),
        ('roadmap_update', 'Roadmap Update'),
        ('skill_completed', 'Skill Completed'),
        ('new_trend', 'New Market Trend'),
        ('cv_generated', 'CV Generated'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional link to related content"
    )
    
    class Meta:
        db_table = 'user_notifications'
        verbose_name = 'User Notification'
        verbose_name_plural = 'User Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.user.email} - {self.title} ({status})"
    
    def mark_as_read(self):
        """Mark this notification as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    def mark_as_unread(self):
        """Mark this notification as unread"""
        if self.is_read:
            self.is_read = False
            self.save(update_fields=['is_read'])
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, link_url=''):
        """Helper method to create a notification"""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url
        )
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user"""
        return cls.objects.filter(user=user, is_read=False).count()


class UserActivityLog(models.Model):
    """
    Log user activities for analytics and debugging
    """
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('profile_update', 'Profile Update'),
        ('skill_added', 'Skill Added'),
        ('skill_completed', 'Skill Completed'),
        ('roadmap_created', 'Roadmap Created'),
        ('roadmap_updated', 'Roadmap Updated'),
        ('cv_generated', 'CV Generated'),
        ('cv_uploaded', 'CV Uploaded'),
        ('job_viewed', 'Job Viewed'),
        ('job_applied', 'Job Applied'),
        ('chat_started', 'Chat Started'),
        ('gap_analysis', 'Gap Analysis Performed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPES
    )
    activity_description = models.TextField(
        blank=True,
        help_text="Additional details about the activity"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="User's IP address"
    )
    
    # Optional: store metadata as JSON
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (e.g., skill_id, job_id, etc.)"
    )
    
    class Meta:
        db_table = 'user_activity_logs'
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} ({self.timestamp.date()})"
    
    @classmethod
    def log_activity(cls, user, activity_type, description='', ip_address=None, metadata=None):
        """Helper method to log an activity"""
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            activity_description=description,
            ip_address=ip_address,
            metadata=metadata or {}
        )
    
    @classmethod
    def get_user_activity_summary(cls, user, days=30):
        """Get summary of user activities for the last N days"""
        from datetime import timedelta
        from django.db.models import Count
        
        since = timezone.now() - timedelta(days=days)
        
        summary = cls.objects.filter(
            user=user,
            timestamp__gte=since
        ).values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return summary


class ScrapingLog(models.Model):
    """
    Log scraping activities 
    Tracks job scraping from hh.uz
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]
    
    platform_name = models.CharField(
        max_length=100,
        help_text="Platform scraped (e.g., hh.uz)"
    )
    scrape_date = models.DateTimeField(auto_now_add=True)
    jobs_scraped = models.IntegerField(
        default=0,
        help_text="Total jobs found"
    )
    jobs_added = models.IntegerField(
        default=0,
        help_text="New jobs added to database"
    )
    jobs_updated = models.IntegerField(
        default=0,
        help_text="Existing jobs updated"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success'
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error details if scraping failed"
    )
    
    class Meta:
        db_table = 'scraping_logs'
        verbose_name = 'Scraping Log'
        verbose_name_plural = 'Scraping Logs'
        ordering = ['-scrape_date']
    
    def __str__(self):
        return f"{self.platform_name} - {self.scrape_date.date()} ({self.get_status_display()})"