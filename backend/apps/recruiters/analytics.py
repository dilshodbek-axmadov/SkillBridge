"""
Aggregated metrics for Recruiter Pro analytics dashboard.
"""

from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from apps.jobs.models import JobApplication, JobPosting
from apps.recruiters.models import SavedCandidate
from apps.skills.models import UserSkill
from apps.users.models import User, UserProfile


def _open_developer_qs():
    return User.objects.filter(
        user_type=User.UserType.DEVELOPER,
        profile__open_to_recruiters=True,
    )


def get_recruiter_analytics(recruiter: User) -> dict:
    now = timezone.now()
    day_30 = now - timedelta(days=30)
    day_180 = now - timedelta(days=180)
    week_8 = now - timedelta(weeks=8)

    open_devs = _open_developer_qs()
    total_open = open_devs.count()

    by_experience = list(
        open_devs.values('profile__experience_level')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    by_desired_role = list(
        UserProfile.objects.filter(
            user__user_type=User.UserType.DEVELOPER,
            open_to_recruiters=True,
        )
        .exclude(desired_role__isnull=True)
        .exclude(desired_role='')
        .values('desired_role')
        .annotate(count=Count('profile_id'))
        .order_by('-count')[:15]
    )

    by_skill_category = list(
        UserSkill.objects.filter(
            user__user_type=User.UserType.DEVELOPER,
            user__profile__open_to_recruiters=True,
        )
        .values('skill__category')
        .annotate(count=Count('user_skill_id'))
        .order_by('-count')[:12]
    )

    top_skills = list(
        UserSkill.objects.filter(
            user__user_type=User.UserType.DEVELOPER,
            user__profile__open_to_recruiters=True,
        )
        .values('skill__name_en')
        .annotate(count=Count('user_skill_id'))
        .order_by('-count')[:20]
    )

    talent_trend = list(
        open_devs.filter(created_at__gte=day_180)
        .annotate(period=TruncMonth('created_at'))
        .values('period')
        .annotate(new_developers=Count('id'))
        .order_by('period')
    )
    for row in talent_trend:
        p = row.get('period')
        row['period'] = p.isoformat()[:7] if p else None

    # —— Recruiter workspace ——
    my_jobs = JobPosting.objects.filter(posted_by=recruiter)
    my_active = my_jobs.filter(listing_status=JobPosting.ListingStatus.ACTIVE)
    active_job_count = my_active.count()
    total_views = int(my_active.aggregate(v=Sum('view_count'))['v'] or 0)

    total_applications = JobApplication.objects.filter(job_posting__posted_by=recruiter).count()

    shortlist_total = SavedCandidate.objects.filter(recruiter=recruiter).count()
    shortlist_distinct = (
        SavedCandidate.objects.filter(recruiter=recruiter).values('candidate_id').distinct().count()
    )

    saves_30d = SavedCandidate.objects.filter(recruiter=recruiter, created_at__gte=day_30).count()

    shortlist_weekly = list(
        SavedCandidate.objects.filter(recruiter=recruiter, created_at__gte=week_8)
        .annotate(week_start=TruncWeek('created_at'))
        .values('week_start')
        .annotate(saves=Count('saved_id'))
        .order_by('week_start')
    )
    for row in shortlist_weekly:
        w = row.get('week_start')
        row['week'] = w.date().isoformat() if w else None
        row.pop('week_start', None)

    view_to_apply = round(total_applications / total_views, 4) if total_views else None
    apps_per_active_job = round(total_applications / active_job_count, 2) if active_job_count else None

    shortlist_to_apply = (
        round(total_applications / shortlist_distinct, 4) if shortlist_distinct else None
    )

    return {
        'market': {
            'total_developers_open': total_open,
            'by_experience_level': by_experience,
            'by_desired_role': by_desired_role,
            'by_skill_category': [{'category': r['skill__category'] or '—', 'count': r['count']} for r in by_skill_category],
            'top_skills': [{'skill': r['skill__name_en'], 'count': r['count']} for r in top_skills],
            'talent_pool_trend': talent_trend,
        },
        'search_performance': {
            'description': 'Activity derived from your saved shortlist (new saves signal discovery velocity).',
            'saves_last_30_days': saves_30d,
            'shortlist_candidates_distinct': shortlist_distinct,
            'shortlist_saves_total': shortlist_total,
            'weekly_shortlist_saves': shortlist_weekly,
            'market_index_size': total_open,
        },
        'response_rates': {
            'description': 'Engagement proxies from listing views and applications (no email tracking yet).',
            'applications_to_views_ratio': view_to_apply,
            'applications_per_active_job': apps_per_active_job,
            'applications_to_shortlisted_candidates_ratio': shortlist_to_apply,
        },
        'hiring_funnel': {
            'description': 'Your active postings and pipeline.',
            'stages': [
                {
                    'id': 'views',
                    'label': 'Views on active job posts',
                    'value': total_views,
                },
                {
                    'id': 'applications',
                    'label': 'Applications received',
                    'value': total_applications,
                },
                {
                    'id': 'shortlist',
                    'label': 'Candidates on your shortlist',
                    'value': shortlist_distinct,
                },
            ],
            'active_job_postings': active_job_count,
            'total_job_postings': my_jobs.count(),
        },
    }
