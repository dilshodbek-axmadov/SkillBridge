"""
Recruiter analytics — rich market + workspace + AI-matching aggregator.

Single entrypoint: get_recruiter_analytics(recruiter) -> dict
Returns a dashboard payload covering:
    - candidate_pool        (developers opted in to recruiters)
    - market_intelligence   (external job-market signal, mostly hh.uz)
    - my_jobs_performance   (recruiter's own postings)
    - predictions           (skill trend / competitor analysis)
    - ai_matching           (skill-overlap match between recruiter jobs and candidates)
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.analytics.models import SkillDemandSnapshot
from apps.jobs.models import JobApplication, JobPosting, JobSkill
from apps.skills.models import Skill, UserSkill
from apps.users.models import User, UserProfile


# ----------------------------- helpers -----------------------------

EXPERIENCE_LABELS = {
    'beginner': 'Beginner',
    'junior': 'Junior',
    'mid': 'Mid-level',
    'senior': 'Senior',
    'lead': 'Lead',
}


def _open_developer_qs():
    return User.objects.filter(
        user_type=User.UserType.DEVELOPER,
        profile__open_to_recruiters=True,
    )


def _normalize_location(raw: str | None) -> str:
    if not raw:
        return 'Unknown'
    val = raw.strip()
    if not val:
        return 'Unknown'
    # Take first comma-separated chunk for cleaner heatmap labels
    head = val.split(',')[0].strip()
    return head[:40] if head else 'Unknown'


def _percent(part: int, total: int) -> float:
    if not total:
        return 0.0
    return round((part / total) * 100, 1)


def _decimal_to_float(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    return val


# ------------------------- candidate pool --------------------------

def _candidate_pool() -> dict:
    open_devs = _open_developer_qs()
    total_open = open_devs.count()

    # Total candidates by desired role
    by_role_raw = (
        UserProfile.objects.filter(
            user__user_type=User.UserType.DEVELOPER,
            open_to_recruiters=True,
        )
        .exclude(desired_role__isnull=True)
        .exclude(desired_role='')
        .values('desired_role')
        .annotate(count=Count('profile_id'))
        .order_by('-count')[:12]
    )
    by_role = [{'role': r['desired_role'], 'count': r['count']} for r in by_role_raw]

    # Top 10 skills among candidates
    top_skills_raw = (
        UserSkill.objects.filter(
            user__user_type=User.UserType.DEVELOPER,
            user__profile__open_to_recruiters=True,
        )
        .values('skill_id', 'skill__name_en', 'skill__category')
        .annotate(count=Count('user_skill_id'))
        .order_by('-count')[:10]
    )
    top_skills = [
        {
            'skill_id': r['skill_id'],
            'skill': r['skill__name_en'],
            'category': r['skill__category'] or 'other',
            'count': r['count'],
        }
        for r in top_skills_raw
    ]

    # Experience level breakdown (with %)
    exp_raw = (
        open_devs.values('profile__experience_level')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    experience = []
    for row in exp_raw:
        level = row['profile__experience_level'] or 'beginner'
        experience.append({
            'level': level,
            'label': EXPERIENCE_LABELS.get(level, level.title()),
            'count': row['count'],
            'percentage': _percent(row['count'], total_open),
        })

    # Location distribution (heatmap-style list)
    loc_counts: dict[str, int] = defaultdict(int)
    profile_locations = UserProfile.objects.filter(
        user__user_type=User.UserType.DEVELOPER,
        open_to_recruiters=True,
    ).values_list('location', flat=True)
    for raw in profile_locations:
        loc_counts[_normalize_location(raw)] += 1
    locations = [
        {'location': k, 'count': v, 'percentage': _percent(v, total_open)}
        for k, v in sorted(loc_counts.items(), key=lambda kv: kv[1], reverse=True)
    ][:12]

    return {
        'total_open': total_open,
        'by_role': by_role,
        'top_skills': top_skills,
        'experience': experience,
        'locations': locations,
    }


# ----------------------- market intelligence -----------------------

def _market_intelligence(recruiter: User) -> dict:
    # Treat any non-self-posted job as "market"; hh.uz is the dominant source.
    market_jobs = JobPosting.objects.filter(
        is_active=True,
        listing_status=JobPosting.ListingStatus.ACTIVE,
    ).exclude(posted_by=recruiter)

    # Most in-demand skills (from market job postings)
    in_demand_raw = (
        JobSkill.objects.filter(job_posting__in=market_jobs)
        .values('skill_id', 'skill__name_en', 'skill__category')
        .annotate(job_count=Count('job_posting_id', distinct=True))
        .order_by('-job_count')[:15]
    )
    skill_ids = [r['skill_id'] for r in in_demand_raw]
    candidate_supply = dict(
        UserSkill.objects.filter(
            skill_id__in=skill_ids,
            user__user_type=User.UserType.DEVELOPER,
            user__profile__open_to_recruiters=True,
        )
        .values_list('skill_id')
        .annotate(c=Count('user_skill_id'))
        .values_list('skill_id', 'c')
    )
    in_demand_skills = []
    for r in in_demand_raw:
        sid = r['skill_id']
        in_demand_skills.append({
            'skill_id': sid,
            'skill': r['skill__name_en'],
            'category': r['skill__category'] or 'other',
            'job_count': r['job_count'],
            'candidate_count': candidate_supply.get(sid, 0),
        })

    # Average salary by role (market vs candidates' expectations)
    # Group by job_category. Candidate-side expectations are not yet collected.
    salary_rows = (
        market_jobs.exclude(job_category='')
        .filter(salary_min__isnull=False)
        .values('job_category')
        .annotate(
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
            job_count=Count('job_id'),
        )
        .order_by('-job_count')[:10]
    )
    salary_by_role = []
    for r in salary_rows:
        avg_min = _decimal_to_float(r['avg_min'])
        avg_max = _decimal_to_float(r['avg_max'])
        market_avg = None
        if avg_min is not None and avg_max is not None:
            market_avg = round((avg_min + avg_max) / 2, 2)
        elif avg_min is not None:
            market_avg = round(avg_min, 2)
        salary_by_role.append({
            'role': r['job_category'],
            'market_min': avg_min,
            'market_max': avg_max,
            'market_avg': market_avg,
            'candidate_expectation': None,  # not collected on profiles yet
            'job_count': r['job_count'],
        })

    # Skills gap — most demanded by jobs but candidates lack most.
    # Use a "shortage ratio" = candidate_count / job_count (lower = bigger gap).
    gap_raw = (
        JobSkill.objects.filter(job_posting__in=market_jobs)
        .values('skill_id', 'skill__name_en')
        .annotate(demand=Count('job_posting_id', distinct=True))
        .filter(demand__gte=3)
        .order_by('-demand')[:40]
    )
    gap_ids = [r['skill_id'] for r in gap_raw]
    supply_for_gap = dict(
        UserSkill.objects.filter(
            skill_id__in=gap_ids,
            user__user_type=User.UserType.DEVELOPER,
            user__profile__open_to_recruiters=True,
        )
        .values_list('skill_id')
        .annotate(c=Count('user_skill_id'))
        .values_list('skill_id', 'c')
    )
    gap_items = []
    for r in gap_raw:
        sid = r['skill_id']
        demand = r['demand']
        supply = supply_for_gap.get(sid, 0)
        # Gap score: scale 0..100, higher means harder to find supply
        ratio = supply / demand if demand else 0
        gap_score = round(max(0.0, min(100.0, (1 - ratio) * 100)), 1)
        gap_items.append({
            'skill_id': sid,
            'skill': r['skill__name_en'],
            'demand': demand,
            'supply': supply,
            'gap_score': gap_score,
        })
    gap_items.sort(key=lambda x: (x['gap_score'], x['demand']), reverse=True)
    skills_gap = gap_items[:10]

    # Competitor job postings — count by category (from market only).
    comp_rows = (
        market_jobs.exclude(job_category='')
        .values('job_category')
        .annotate(count=Count('job_id'))
        .order_by('-count')[:10]
    )
    competitor_postings = [
        {'role': r['job_category'], 'count': r['count']} for r in comp_rows
    ]

    return {
        'in_demand_skills': in_demand_skills,
        'salary_by_role': salary_by_role,
        'skills_gap': skills_gap,
        'competitor_postings': competitor_postings,
    }


# --------------------------- my jobs perf --------------------------

def _my_jobs_performance(recruiter: User) -> dict:
    now = timezone.now()
    my_jobs = JobPosting.objects.filter(posted_by=recruiter)
    active = my_jobs.filter(listing_status=JobPosting.ListingStatus.ACTIVE)

    total_views = int(active.aggregate(v=Sum('view_count'))['v'] or 0)
    total_apps = JobApplication.objects.filter(job_posting__posted_by=recruiter).count()

    # Per-job stats
    app_counts = dict(
        JobApplication.objects.filter(job_posting__posted_by=recruiter)
        .values_list('job_posting_id')
        .annotate(c=Count('application_id'))
        .values_list('job_posting_id', 'c')
    )

    jobs_payload = []
    for job in my_jobs.order_by('-posted_date')[:25]:
        applications = app_counts.get(job.job_id, 0)
        views = int(job.view_count or 0)
        rate = round((applications / views), 4) if views else None
        days = (now - job.posted_date).days if job.posted_date else None
        jobs_payload.append({
            'job_id': job.job_id,
            'title': job.job_title,
            'category': job.job_category or '—',
            'status': job.listing_status,
            'views': views,
            'applications': applications,
            'application_rate': rate,
            'days_since_posted': days,
            'posted_date': job.posted_date.date().isoformat() if job.posted_date else None,
        })

    best_job = None
    if jobs_payload:
        best = max(jobs_payload, key=lambda j: (j['applications'], j['views']))
        if best['applications'] > 0 or best['views'] > 0:
            best_job = best

    application_rate = round(total_apps / total_views, 4) if total_views else None

    return {
        'active_count': active.count(),
        'total_count': my_jobs.count(),
        'total_views': total_views,
        'total_applications': total_apps,
        'application_rate': application_rate,
        'best_job': best_job,
        'jobs': jobs_payload,
    }


# --------------------------- predictions ---------------------------

def _predictions(recruiter: User) -> dict:
    # Hot next quarter — pick latest 30d snapshot per skill, sort by demand_change_30d.
    # DB-agnostic: order by date desc, then dedup in Python.
    snaps = (
        SkillDemandSnapshot.objects
        .filter(period='30d', demand_change_30d__isnull=False)
        .select_related('skill')
        .order_by('-snapshot_date')[:500]
    )

    rising = []
    seen_skills = set()
    for snap in snaps:
        if snap.skill_id in seen_skills:
            continue
        seen_skills.add(snap.skill_id)
        rising.append({
            'skill_id': snap.skill_id,
            'skill': snap.skill.name_en,
            'category': snap.skill.category,
            'demand_change_30d': round(snap.demand_change_30d, 1),
            'demand_score': round(snap.demand_score or 0, 1),
            'job_count': snap.job_count,
        })
    rising.sort(key=lambda x: x['demand_change_30d'], reverse=True)
    next_quarter_hot = rising[:10]

    # Competitor analysis — top skills competitors hire for, excluding recruiter's own jobs.
    market_jobs = JobPosting.objects.filter(
        is_active=True,
        listing_status=JobPosting.ListingStatus.ACTIVE,
    ).exclude(posted_by=recruiter)
    competitor_skills = list(
        JobSkill.objects.filter(job_posting__in=market_jobs)
        .values('skill__name_en', 'skill__category')
        .annotate(count=Count('job_posting_id', distinct=True))
        .order_by('-count')[:10]
    )
    competitor_skills = [
        {
            'skill': r['skill__name_en'],
            'category': r['skill__category'] or 'other',
            'count': r['count'],
        }
        for r in competitor_skills
    ]

    return {
        'next_quarter_hot_skills': next_quarter_hot,
        'competitor_skills': competitor_skills,
    }


# --------------------------- AI matching ---------------------------

def _candidate_skill_map(candidate_user_ids: list[int]) -> dict[int, set[int]]:
    """Return {user_id: {skill_id, ...}} for all developers we'll match."""
    rows = UserSkill.objects.filter(user_id__in=candidate_user_ids).values_list('user_id', 'skill_id')
    out: dict[int, set[int]] = defaultdict(set)
    for uid, sid in rows:
        out[uid].add(sid)
    return out


def _ai_matching(recruiter: User) -> dict:
    my_active = list(
        JobPosting.objects.filter(
            posted_by=recruiter,
            listing_status=JobPosting.ListingStatus.ACTIVE,
        ).order_by('-posted_date')[:8]
    )
    if not my_active:
        return {
            'top_candidates_per_job': [],
            'hardest_to_fill': [],
            'suggested_skills_per_job': [],
        }

    # Job → required skill ids
    job_skill_rows = JobSkill.objects.filter(
        job_posting_id__in=[j.job_id for j in my_active]
    ).values_list('job_posting_id', 'skill_id', 'skill__name_en')
    job_required: dict[int, set[int]] = defaultdict(set)
    skill_name: dict[int, str] = {}
    for jid, sid, name in job_skill_rows:
        job_required[jid].add(sid)
        skill_name[sid] = name

    # Candidate pool (open developers) — load skills once.
    open_devs = list(
        _open_developer_qs()
        .select_related('profile')
        .only('id', 'first_name', 'last_name', 'email', 'profile__desired_role', 'profile__experience_level')[:500]
    )
    cand_ids = [u.id for u in open_devs]
    cand_skills = _candidate_skill_map(cand_ids)
    cand_meta = {u.id: u for u in open_devs}

    top_candidates_per_job = []
    job_avg_match = []  # for hardest-to-fill

    for job in my_active:
        req = job_required.get(job.job_id, set())
        if not req:
            top_candidates_per_job.append({
                'job_id': job.job_id,
                'title': job.job_title,
                'required_skill_count': 0,
                'candidates': [],
                'note': 'No required skills attached to this job yet.',
            })
            continue

        scored = []
        for uid in cand_ids:
            sset = cand_skills.get(uid)
            if not sset:
                continue
            inter = len(req & sset)
            if inter == 0:
                continue
            pct = round((inter / len(req)) * 100, 1)
            scored.append((pct, inter, uid))

        scored.sort(reverse=True)
        top = scored[:5]
        top_candidates = []
        for pct, inter, uid in top:
            u = cand_meta[uid]
            top_candidates.append({
                'user_id': uid,
                'name': u.full_name,
                'email': u.email,
                'desired_role': getattr(u.profile, 'desired_role', None) if hasattr(u, 'profile') else None,
                'experience_level': getattr(u.profile, 'experience_level', None) if hasattr(u, 'profile') else None,
                'match_pct': pct,
                'matched_skills': inter,
                'required_skills': len(req),
            })
        top_candidates_per_job.append({
            'job_id': job.job_id,
            'title': job.job_title,
            'required_skill_count': len(req),
            'candidates': top_candidates,
        })

        # Hardest-to-fill: avg of top-10 match pct
        top10 = scored[:10]
        if top10:
            avg = round(sum(p for p, _, _ in top10) / len(top10), 1)
        else:
            avg = 0.0
        job_avg_match.append({
            'job_id': job.job_id,
            'title': job.job_title,
            'avg_top_match': avg,
            'matched_candidates': len(scored),
        })

    hardest_to_fill = sorted(job_avg_match, key=lambda x: x['avg_top_match'])[:5]

    # Suggested skills to add — for each job, look at most-demanded market skills
    # in the same job_category that are NOT in this job's required skills.
    suggested_skills_per_job = []
    for job in my_active:
        req = job_required.get(job.job_id, set())
        category = job.job_category
        if not category:
            suggested_skills_per_job.append({
                'job_id': job.job_id,
                'title': job.job_title,
                'missing_skills': [],
                'note': 'Set a job category to see skill suggestions.',
            })
            continue

        peer_jobs = JobPosting.objects.filter(
            is_active=True,
            listing_status=JobPosting.ListingStatus.ACTIVE,
            job_category=category,
        ).exclude(posted_by=recruiter)

        peer_skill_rows = (
            JobSkill.objects.filter(job_posting__in=peer_jobs)
            .exclude(skill_id__in=req)
            .values('skill_id', 'skill__name_en')
            .annotate(count=Count('job_posting_id', distinct=True))
            .order_by('-count')[:6]
        )
        missing = [
            {
                'skill_id': r['skill_id'],
                'skill': r['skill__name_en'],
                'demand': r['count'],
            }
            for r in peer_skill_rows
        ]
        suggested_skills_per_job.append({
            'job_id': job.job_id,
            'title': job.job_title,
            'missing_skills': missing,
        })

    return {
        'top_candidates_per_job': top_candidates_per_job,
        'hardest_to_fill': hardest_to_fill,
        'suggested_skills_per_job': suggested_skills_per_job,
    }


# ----------------------------- public ------------------------------

def get_recruiter_analytics(recruiter: User) -> dict:
    return {
        'generated_at': timezone.now().isoformat(),
        'candidate_pool': _candidate_pool(),
        'market_intelligence': _market_intelligence(recruiter),
        'my_jobs_performance': _my_jobs_performance(recruiter),
        'predictions': _predictions(recruiter),
        'ai_matching': _ai_matching(recruiter),
    }
