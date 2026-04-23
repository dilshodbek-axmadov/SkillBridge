"""
Centralized recruiter access rules.

Source of truth for plan-gated recruiter features. Views SHOULD NOT duplicate
rule logic; instead call the service methods here.

Plan rules (current product definition):
    Free plan:
      - max 1 job posting per rolling 30-day window
      - up to 10 developer profiles visible per search/filter request
      - no access to analytics (403 pro_required)

    Pro plan:
      - unlimited jobs (configurable soft cap via RECRUITER_PRO_JOBS_PER_30D)
      - full developer visibility
      - analytics access
"""

from datetime import timedelta

from django.utils import timezone

from apps.jobs.models import JobPosting


# --- Configurable limits (overridable via Django settings if needed) ---

FREE_JOBS_PER_30D = 1
FREE_DEVELOPER_VISIBILITY = 10

# Pro soft cap; None means effectively unlimited.
PRO_JOBS_PER_30D = None


def _is_pro(user) -> bool:
    """Staff behaves as Pro for testing purposes."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return bool(getattr(user, "is_recruiter_pro", False))


def _count_user_jobs_last_30d(user) -> int:
    since = timezone.now() - timedelta(days=30)
    return JobPosting.objects.filter(posted_by=user, posted_date__gte=since).count()


# =========================================================
# PUBLIC API
# =========================================================


def can_post_job(user) -> dict:
    """
    Return a dict describing whether the user can post a new job right now.

    Shape:
        {
            "allowed": bool,
            "reason": str | None,
            "code": str | None,
            "limit": int | None,
            "used": int,
            "remaining": int | None,
            "window_days": 30,
            "plan": "free" | "pro",
        }
    """
    pro = _is_pro(user)
    used = _count_user_jobs_last_30d(user)
    limit = PRO_JOBS_PER_30D if pro else FREE_JOBS_PER_30D
    remaining = None if limit is None else max(limit - used, 0)
    allowed = limit is None or used < limit

    return {
        "allowed": allowed,
        "reason": None if allowed else (
            "Free plan limit reached: 1 job posting per 30 days. Upgrade to Pro for unlimited."
        ),
        "code": None if allowed else "free_plan_job_limit",
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "window_days": 30,
        "plan": "pro" if pro else "free",
    }


def get_developer_visibility_limit(user):
    """
    Return the max number of developer rows this user may see per list response.
    None = unlimited.
    """
    if _is_pro(user):
        return None
    return FREE_DEVELOPER_VISIBILITY


def can_view_analytics(user) -> dict:
    """
    Return whether the user can view Recruiter Pro analytics.

    Shape:
        {"allowed": bool, "reason": str | None, "code": str | None, "plan": str}
    """
    pro = _is_pro(user)
    if pro:
        return {"allowed": True, "reason": None, "code": None, "plan": "pro"}
    return {
        "allowed": False,
        "reason": "Analytics are available on SkillBridge Recruiter Pro.",
        "code": "pro_required",
        "plan": "free",
    }


def get_recruiter_access_state(user) -> dict:
    """
    Aggregated snapshot for the frontend.
    Single source of truth; UI should never derive access from plan alone.
    """
    pro = _is_pro(user)
    jobs = can_post_job(user)
    analytics = can_view_analytics(user)
    dev_limit = get_developer_visibility_limit(user)

    return {
        "plan": "pro" if pro else "free",
        "is_pro": pro,
        "jobs": jobs,
        "analytics": analytics,
        "developer_visibility_limit": dev_limit,
        "upgrade_required": not pro,
    }
