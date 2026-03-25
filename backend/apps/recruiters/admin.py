from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import RecruiterSavedSearch, SavedCandidate


@admin.register(SavedCandidate)
class SavedCandidateAdmin(admin.ModelAdmin):
    list_display = ('saved_id', 'recruiter', 'candidate', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('recruiter__email', 'candidate__email', 'notes')
    raw_id_fields = ('recruiter', 'candidate')
    ordering = ('-created_at',)


@admin.register(RecruiterSavedSearch)
class RecruiterSavedSearchAdmin(admin.ModelAdmin):
    list_display = ('search_id', 'recruiter', 'name', 'updated_at')
    search_fields = ('recruiter__email', 'name')
    raw_id_fields = ('recruiter',)
    ordering = ('-updated_at',)
