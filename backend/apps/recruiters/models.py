"""
Recruiter-specific marketplace models.

Keeps cross-user bookmarking and saved searches here so `users` and `jobs`
stay focused on auth and vacancies. Reuses `User` for both recruiter and
developer; job rows stay in `jobs.JobPosting`.
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _


class SavedCandidate(models.Model):
    """
    Recruiter shortlist entry: one row per (recruiter, developer) pair.
    Candidate must be a different user than the recruiter (enforced in DB).
    """

    saved_id = models.AutoField(primary_key=True)
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_candidates',
        verbose_name=_('recruiter'),
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_by_recruiters',
        verbose_name=_('candidate'),
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'recruiter_saved_candidates'
        ordering = ['-created_at']
        verbose_name = _('saved candidate')
        verbose_name_plural = _('saved candidates')
        constraints = [
            models.UniqueConstraint(
                fields=('recruiter', 'candidate'),
                name='uniq_recruiter_saved_candidate',
            ),
            models.CheckConstraint(
                check=~Q(recruiter_id=F('candidate_id')),
                name='saved_candidate_recruiter_ne_candidate',
            ),
        ]
        indexes = [
            models.Index(fields=['recruiter', '-created_at']),
        ]

    def __str__(self):
        return f'{self.recruiter_id} → {self.candidate_id}'


class RecruiterSavedSearch(models.Model):
    """
    Named filter preset for candidate search (filters stored as JSON).
    """

    search_id = models.AutoField(primary_key=True)
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recruiter_saved_searches',
        verbose_name=_('recruiter'),
    )
    name = models.CharField(_('name'), max_length=120)
    filters = models.JSONField(
        _('filters'),
        default=dict,
        help_text=_('Serialized search state, e.g. skills, location, experience.'),
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'recruiter_saved_searches'
        ordering = ['-updated_at']
        verbose_name = _('saved search')
        verbose_name_plural = _('saved searches')
        indexes = [
            models.Index(fields=['recruiter', '-updated_at']),
        ]

    def __str__(self):
        return f'{self.name} ({self.recruiter_id})'
