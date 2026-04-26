"""
Jobs App Services
=================
Job listing, filtering, and skill-based recommendation logic.
"""

import re
from datetime import timedelta

from django.db.models import Q, Case, When, IntegerField, Value, F
from django.utils import timezone

from apps.jobs.models import JobPosting
from apps.skills.models import UserSkill

# Only show jobs posted within the last 6 months
FRESHNESS_DAYS = 180


class JobService:
    """Service for listing, filtering, and recommending jobs."""

    def _fresh_active_jobs(self):
        """Public job search: live listings from the last freshness window."""
        cutoff = timezone.now() - timedelta(days=FRESHNESS_DAYS)
        return JobPosting.objects.filter(
            listing_status=JobPosting.ListingStatus.ACTIVE,
            posted_date__gte=cutoff,
        )

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
                Q(job_title__icontains=q)
                | Q(company_name__icontains=q)
                | Q(job_description__icontains=q)
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
        """Get a single job with full details; increments view counter for analytics."""
        cutoff = timezone.now() - timedelta(days=FRESHNESS_DAYS)
        try:
            job = (
                JobPosting.objects
                .prefetch_related('job_skills__skill')
                .get(
                    job_id=job_id,
                    listing_status=JobPosting.ListingStatus.ACTIVE,
                    posted_date__gte=cutoff,
                )
            )
        except JobPosting.DoesNotExist:
            return None

        JobPosting.objects.filter(pk=job.pk).update(view_count=F('view_count') + 1)
        job.refresh_from_db(fields=['view_count'])

        data = self._serialize_job(job)
        data['description'] = job.job_description
        data['view_count'] = job.view_count
        return data

    def _get_user_skill_ids(self, user):
        return set(UserSkill.objects.filter(user=user).values_list('skill_id', flat=True))

    def _get_current_job_position(self, user) -> str:
        try:
            profile = user.profile
        except Exception:
            return ''
        return (profile.current_job_position or '').strip()

    def _recommend_by_position(self, position: str, user_skill_ids: set, limit: int = 20):
        tokens = [token for token in re.split(r'[\s,./()_-]+', position) if len(token) >= 3][:5]

        position_filter = (
            Q(job_title__icontains=position)
            | Q(job_category__icontains=position)
            | Q(job_description__icontains=position)
        )
        for token in tokens:
            position_filter |= Q(job_title__icontains=token)
            position_filter |= Q(job_category__icontains=token)
            position_filter |= Q(job_description__icontains=token)

        base_qs = self._fresh_active_jobs().filter(position_filter).distinct()
        total = base_qs.count()

        candidates = (
            base_qs
            .annotate(
                exact_title_match=Case(
                    When(job_title__iexact=position, then=Value(100)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                title_contains_match=Case(
                    When(job_title__icontains=position, then=Value(40)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                category_contains_match=Case(
                    When(job_category__icontains=position, then=Value(20)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                description_contains_match=Case(
                    When(job_description__icontains=position, then=Value(10)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            .prefetch_related('job_skills__skill')
            .order_by(
                '-exact_title_match',
                '-title_contains_match',
                '-category_contains_match',
                '-description_contains_match',
                '-posted_date',
            )[:max(limit * 5, 60)]
        )

        jobs = []
        for job in candidates:
            data = self._serialize_job(job)

            if user_skill_ids:
                required_skills = list(job.job_skills.all())
                total_required = len(required_skills)
                if total_required > 0:
                    matched = [js.skill.name_en for js in required_skills if js.skill_id in user_skill_ids]
                    missing = [js.skill.name_en for js in required_skills if js.skill_id not in user_skill_ids]
                    data['match_percentage'] = round(len(matched) / total_required * 100)
                    data['matched_skills'] = matched
                    data['missing_skills'] = missing

            jobs.append(data)
            if len(jobs) >= limit:
                break

        return {'total': total, 'jobs': jobs}

    def _recommend_by_skills(self, user_skill_ids: set, limit: int = 20):
        if not user_skill_ids:
            return {'total': 0, 'jobs': []}

        candidates = (
            self._fresh_active_jobs()
            .filter(job_skills__skill_id__in=user_skill_ids)
            .distinct()
            .prefetch_related('job_skills__skill')
            .order_by('-posted_date')[:200]
        )

        scored = []
        for job in candidates:
            required_skills = list(job.job_skills.all())
            total_required = len(required_skills)
            if total_required == 0:
                continue

            matched = [js.skill.name_en for js in required_skills if js.skill_id in user_skill_ids]
            missing = [js.skill.name_en for js in required_skills if js.skill_id not in user_skill_ids]

            data = self._serialize_job(job)
            data['match_percentage'] = round(len(matched) / total_required * 100)
            data['matched_skills'] = matched
            data['missing_skills'] = missing
            scored.append(data)

        scored.sort(key=lambda x: (-x['match_percentage'], x.get('posted_date', '')))
        return {'total': len(scored), 'jobs': scored[:limit]}

    def recommend_jobs(self, user, limit: int = 20):
        """
        Dynamic recommendation priority:
        1) current_job_position
        2) user skills
        3) empty list
        """
        user_skill_ids = self._get_user_skill_ids(user)
        current_position = self._get_current_job_position(user)

        if current_position:
            return self._recommend_by_position(
                position=current_position,
                user_skill_ids=user_skill_ids,
                limit=limit,
            )

        if user_skill_ids:
            return self._recommend_by_skills(user_skill_ids=user_skill_ids, limit=limit)

        return {'total': 0, 'jobs': []}

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
