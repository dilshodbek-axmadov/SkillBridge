from apps.payments.models import Payment


def has_paid_for_cv(user, cv_id=None):
    qs = Payment.objects.filter(
        user=user,
        payment_type=Payment.PaymentType.CV_DOWNLOAD,
        status=Payment.Status.SUCCEEDED,
    )

    # If caller doesn't care about a specific CV, any successful CV_DOWNLOAD counts.
    if cv_id is None:
        return qs.exists()

    # CV-specific check via metadata. For legacy rows without cv_id metadata,
    # treat as paid (backward compatible).
    for p in qs.only('metadata'):
        meta = p.metadata or {}
        if 'cv_id' not in meta:
            return True
        if str(meta.get('cv_id')) == str(cv_id):
            return True
    return False


def can_download_cv(user, cv_id=None):
    if user.is_staff:
        return True

    if user.is_recruiter_pro:
        return True

    return has_paid_for_cv(user, cv_id)