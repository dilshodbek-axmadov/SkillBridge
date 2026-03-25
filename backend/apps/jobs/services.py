"""
Jobs App Services
=================
Job listing, filtering, and skill-based recommendation logic.
"""

from datetime import timedelta

from django.db.models import Q, Count, Case, When, IntegerField, Value, F
from django.utils import timezone

from apps.jobs.models import JobPosting, JobSkill
from apps.skills.models import UserSkill

# Only show jobs posted within the last 6 months
FRESHNESS_DAYS = 180


class JobService:
    """Service for listing, filtering, and recommending jobs."""

    def _fresh_active_jobs(self):
        """Base queryset: active jobs posted within last 6 months."""
        cutoff = timezone.now() - timedelta(days=FRESHNESS_DAYS)
        return JobPosting.objects.filter(is_active=True, posted_date__gte=cutoff)

    def list_jobs(self, filters: dict, limit: int = 20, offset: int = 0):
        """
        List active jobs with optional filters.

        Supported filters:
        - q: search query (title, company, description)
        - category: job_category
        - experience: experience_required
        - employment_type: full_time, part_time, project
        - location: location substring
        - is_remote: true/false
        - salary_min: minimum salary floor
        - sort: posted_date (default), salary_max, salary_min
        """

        qs = self._fresh_active_jobs()

        q = filters.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(job_title__icontains=q) |
                Q(company_name__icontains=q) |
                Q(job_description__icontains=q)
            )

        category = filters.get('category')
        if category:
            qs = qs.filter(job_category__icontains=category)

        experience = filters.get('experience')
        if experience and experience != 'all':
            qs = qs.filter(experience_required=experience)

        employment = filters.get('employment_type')
        if employment and employment != 'all':
            qs = qs.filter(employment_type=employment)

        location = filters.get('location')
        if location and location != 'all':
            qs = qs.filter(location__icontains=location)

        is_remote = filters.get('is_remote')
        if is_remote == 'true':
            qs = qs.filter(is_remote=True)

        salary_min = filters.get('salary_min')
        if salary_min:
            try:
                qs = qs.filter(salary_max__gte=int(salary_min))
            except (ValueError, TypeError):
                pass

        # Sorting
        sort = filters.get('sort', 'posted_date')
        if sort == 'salary_max':
            qs = qs.order_by(F('salary_max').desc(nulls_last=True))
        elif sort == 'salary_min':
            qs = qs.order_by(F('salary_min').desc(nulls_last=True))
        else:
            qs = qs.order_by('-posted_date')

        total = qs.count()
        jobs = qs.select_related().prefetch_related('job_skills__skill')[offset:offset + limit]

        return {
            'total': total,
            'jobs': [self._serialize_job(job) for job in jobs],
        }

    def get_job_detail(self, job_id: int):
        """Get a single job with full details."""
        try:
            job = (
                JobPosting.objects
                .prefetch_related('job_skills__skill')
                .get(job_id=job_id, is_active=True)
            )
        except JobPosting.DoesNotExist:
            return None

        data = self._serialize_job(job)
        data['description'] = job.job_description
        return data

    def recommend_jobs(self, user, limit: int = 20):
        """
        Recommend jobs based on user's skills.

        Algorithm:
        1. Get user's skill IDs.
        2. For each active job, count how many of its required skills
           the user possesses (matched) vs total required.
        3. Compute match_percentage = matched / total_required * 100.
        4. Return jobs sorted by match_percentage desc, then posted_date desc.
        """

        user_skill_ids = set(
            UserSkill.objects.filter(user=user)
            .values_list('skill_id', flat=True)
        )

        if not user_skill_ids:
            # No skills — fall back to recent jobs
            return self.list_jobs({}, limit=limit)

        # Get jobs that have at least one skill in common
        jobs_with_match = (
            self._fresh_active_jobs()
            .filter(job_skills__skill_id__in=user_skill_ids)
            .distinct()
            .prefetch_related('job_skills__skill')
            .order_by('-posted_date')[:200]  # pool
        )

        scored = []
        for job in jobs_with_match:
            required_skills = list(job.job_skills.all())
            total = len(required_skills)
            if total == 0:
                continue

            matched_ids = []
            missing = []
            for js in required_skills:
                if js.skill_id in user_skill_ids:
                    matched_ids.append(js.skill.name_en)
                else:
                    missing.append(js.skill.name_en)

            match_pct = round(len(matched_ids) / total * 100)

            data = self._serialize_job(job)
            data['match_percentage'] = match_pct
            data['matched_skills'] = matched_ids
            data['missing_skills'] = missing

            scored.append(data)

        # Sort by match%, then by most recent
        scored.sort(key=lambda x: (-x['match_percentage'], x.get('posted_date', '')))

        return {
            'total': len(scored),
            'jobs': scored[:limit],
        }

    def get_filter_options(self):
        """Get available filter values from active jobs."""
        active = self._fresh_active_jobs()

        categories = list(
            active
            .exclude(job_category='')
            .values_list('job_category', flat=True)
            .distinct()
            .order_by('job_category')
        )

        locations = list(
            active
            .exclude(location='')
            .values_list('location', flat=True)
            .distinct()
            .order_by('location')
        )

        return {
            'categories': categories,
            'locations': locations,
            'experience_levels': [
                {'value': c[0], 'label': str(c[1])}
                for c in JobPosting.EXPERIENCE_CHOICES
            ],
            'employment_types': [
                {'value': c[0], 'label': str(c[1])}
                for c in JobPosting.EMPLOYMENT_CHOICES
            ],
        }

    def _serialize_job(self, job):
        skills = []
        for js in job.job_skills.all():
            skills.append({
                'skill_id': js.skill_id,
                'name': js.skill.name_en,
                'importance': js.importance,
            })

        return {
            'job_id': job.job_id,
            'job_title': job.job_title,
            'company_name': job.company_name,
            'job_category': job.job_category,
            'experience_required': job.experience_required,
            'employment_type': job.employment_type,
            'salary_min': float(job.salary_min) if job.salary_min else None,
            'salary_max': float(job.salary_max) if job.salary_max else None,
            'salary_currency': job.salary_currency,
            'location': job.location,
            'is_remote': job.is_remote,
            'posted_date': job.posted_date.isoformat() if job.posted_date else None,
            'job_url': job.job_url,
            'skills': skills,
        }
