"""Helpers to record user-facing activity for dashboard / history."""

from __future__ import annotations

from typing import Any, Dict, Optional


def log_user_activity(
    user,
    activity_type: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None,
    link_path: str = '',
):
    """
    Persist one activity row. Safe to call after successful operations only.
    """
    from .models import UserActivity

    return UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=(description or '')[:500],
        metadata=metadata or {},
        link_path=(link_path or '')[:200],
    )


__all__ = ['log_user_activity']
