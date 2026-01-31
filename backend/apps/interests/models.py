"""
Interests App Models
====================
backend/apps/interests/models.py

Stores user interests in multiple languages.
AI translates interests automatically.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Interest(models.Model):
    """
    Interest/hobby categories in multiple languages.
    AI auto-translates based on user input language.
    """
    
    CATEGORY_CHOICES = [
        ('tech', _('Technology')),
        ('design', _('Design')),
        ('management', _('Management')),
        ('business', _('Business')),
        ('creative', _('Creative')),
    ]
    
    interest_id = models.AutoField(primary_key=True)
    
    # Multilingual names
    name_en = models.CharField(
        _('name (English)'),
        max_length=100,
        unique=True
    )
    
    name_ru = models.CharField(
        _('name (Russian)'),
        max_length=100,
        blank=True
    )
    
    name_uz = models.CharField(
        _('name (Uzbek)'),
        max_length=100,
        blank=True
    )
    
    category = models.CharField(
        _('category'),
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'interests'
        ordering = ['category', 'name_en']
        verbose_name = _('interest')
        verbose_name_plural = _('interests')
    
    def __str__(self):
        return f"{self.name_en} ({self.get_category_display()})"
    
    def get_name(self, language_code='en'):
        """Get name in specific language."""
        if language_code == 'ru' and self.name_ru:
            return self.name_ru
        elif language_code == 'uz' and self.name_uz:
            return self.name_uz
        return self.name_en


class UserInterest(models.Model):
    """
    User's selected interests.
    Links users to their interests.
    """
    
    user_interest_id = models.AutoField(primary_key=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_interests',
        verbose_name=_('user')
    )
    
    interest = models.ForeignKey(
        Interest,
        on_delete=models.CASCADE,
        related_name='user_interests',
        verbose_name=_('interest')
    )
    
    added_at = models.DateTimeField(
        _('added at'),
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'user_interests'
        unique_together = [('user', 'interest')]
        ordering = ['-added_at']
        verbose_name = _('user interest')
        verbose_name_plural = _('user interests')
    
    def __str__(self):
        return f"{self.user.username} → {self.interest.name_en}"