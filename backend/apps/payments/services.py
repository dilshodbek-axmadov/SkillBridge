import traceback

import stripe
from django.conf import settings
from django.utils import timezone

from .models import Customer, Subscription, Payment


stripe.api_key = settings.STRIPE_SECRET_KEY


# Customer
def get_or_create_customer(user):
    customer, created = Customer.objects.get_or_create(user=user)

    if not customer.stripe_customer_id:
        stripe_customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": user.id}
        )
        customer.stripe_customer_id = stripe_customer.id
        customer.save()

    return customer


# Subscription (Recruiter Pro)
def create_checkout_session(user, price_id, success_url, cancel_url):
    from .models import Customer
    
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=user,
        defaults={'stripe_customer_id': stripe.Customer.create(email=user.email).id}
    )
    
    # Determine payment type based on price_id
    payment_type = 'cv_download'  # You can make this dynamic based on price_id
    
    session = stripe.checkout.Session.create(
        customer=customer.stripe_customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={  # ← THIS IS THE KEY!
            'user_id': str(user.id),
            'payment_type': payment_type,
        }
    )
    
    return session.url


def cancel_subscription(user):
    try:
        subscription = Subscription.objects.get(user=user)
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        subscription.cancel_at_period_end = True
        subscription.save()
        return True
    except Subscription.DoesNotExist:
        return False


# One-time Payment (CV)
def create_payment_intent(
    user,
    amount,
    currency='usd',
    payment_type='cv_download',
    metadata=None,
    return_intent=False,
):
    customer = get_or_create_customer(user)

    stripe_metadata = {
        "user_id": user.id,
        "payment_type": payment_type,
    }
    if metadata:
        stripe_metadata.update(metadata)

    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),  # convert to cents
        currency=currency,
        customer=customer.stripe_customer_id,
        metadata=stripe_metadata,
    )

    payment = Payment.objects.create(
        user=user,
        stripe_payment_intent_id=intent.id,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        status=Payment.Status.PENDING,
        metadata=stripe_metadata,
    )

    if return_intent:
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": float(amount),
            "currency": currency,
            "payment_id": payment.id,
        }

    return intent.client_secret


def create_pro_subscription_checkout_session(user, success_url, cancel_url):
    """
    Create a Stripe Checkout Session (mode='subscription') for Recruiter Pro.

    Uses STRIPE_PRO_SUBSCRIPTION_PRICE_ID. Attaches user_id on BOTH session
    metadata and the underlying subscription metadata so the webhook can
    map customer.subscription.* events back to the Django user and flip
    User.recruiter_plan to PRO instantly.
    """
    customer = get_or_create_customer(user)
    price_id = getattr(settings, "STRIPE_PRO_SUBSCRIPTION_PRICE_ID", None)
    if not price_id:
        raise ValueError("STRIPE_PRO_SUBSCRIPTION_PRICE_ID is not configured")

    sub_metadata = {
        "user_id": str(user.id),
        "payment_type": "recruiter_pro_subscription",
    }

    session = stripe.checkout.Session.create(
        customer=customer.stripe_customer_id,
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        subscription_data={"metadata": sub_metadata},
        metadata=sub_metadata,
    )

    print(f"[SUBSCRIPTION CHECKOUT SESSION CREATED] id={session.id} metadata={sub_metadata}")

    return session.url


def create_cv_checkout_session(user, cv_id, success_url, cancel_url):
    """
    Create a Stripe Checkout Session for one-time CV download payment.

    Uses STRIPE_CV_DOWNLOAD_PRICE_ID configured in settings.
    """
    customer = get_or_create_customer(user)
    price_id = getattr(settings, "STRIPE_CV_DOWNLOAD_PRICE_ID", None)
    if not price_id:
        raise ValueError("STRIPE_CV_DOWNLOAD_PRICE_ID is not configured")

    cv_payment_metadata = {
        "user_id": str(user.id),
        "cv_id": str(cv_id),
        "payment_type": str(Payment.PaymentType.CV_DOWNLOAD.value),
    }

    session = stripe.checkout.Session.create(
        customer=customer.stripe_customer_id,
        mode="payment",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        payment_intent_data={"metadata": cv_payment_metadata},
        metadata=cv_payment_metadata,
    )

    print(f"[CHECKOUT SESSION CREATED] id={session.id} metadata={cv_payment_metadata}")

    return session.url


# Webhook handlers
def handle_payment_intent_succeeded(data):
    intent_id = data['id']

    try:
        payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
        payment.status = Payment.Status.SUCCEEDED
        payment.save()
    except Payment.DoesNotExist:
        pass


def handle_payment_intent_failed(data):
    intent_id = data['id']

    try:
        payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
        payment.status = Payment.Status.FAILED
        payment.save()
    except Payment.DoesNotExist:
        pass


def _extract_subscription_fields(sub_dict):
    """
    Pull defensively-parsed fields out of a Stripe Subscription payload.

    Handles the Stripe 2024+ API shape where current_period_start /
    current_period_end live on the subscription item, not the top-level
    object. Returns only keys that were successfully extracted (so we can
    pass them as defaults without overwriting existing values with None).
    """
    fields = {}
    if not isinstance(sub_dict, dict):
        return fields

    sub_id = sub_dict.get("id")
    if sub_id:
        fields["stripe_subscription_id"] = sub_id

    status = sub_dict.get("status")
    if status:
        fields["status"] = status

    fields["cancel_at_period_end"] = bool(sub_dict.get("cancel_at_period_end"))

    try:
        first_item = (sub_dict.get("items") or {}).get("data") or []
        first_item = first_item[0] if first_item else {}
    except Exception:
        first_item = {}

    try:
        price_id = (first_item.get("price") or {}).get("id")
        if price_id:
            fields["stripe_price_id"] = price_id
    except Exception:
        pass

    def _ts(*candidates):
        for value in candidates:
            if value:
                try:
                    return timezone.datetime.fromtimestamp(int(value), tz=timezone.utc)
                except Exception:
                    continue
        return None

    period_start = _ts(
        sub_dict.get("current_period_start"),
        first_item.get("current_period_start"),
    )
    period_end = _ts(
        sub_dict.get("current_period_end"),
        first_item.get("current_period_end"),
    )
    if period_start is not None:
        fields["current_period_start"] = period_start
    if period_end is not None:
        fields["current_period_end"] = period_end

    return fields


def _sync_recruiter_plan_from_subscription(user_id, status, cancel_at_period_end):
    """
    Keep User.recruiter_plan in sync with Stripe subscription state.

    Pro is granted while subscription is 'active' or 'trialing' and not flagged
    for hard cancellation (cancel_at_period_end handled by Stripe automatically
    when the period ends). Any terminal state flips back to free.
    """
    from apps.users.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        print(f"[SUBSCRIPTION SYNC] user {user_id} not found; skipping")
        return

    active_states = {"active", "trialing"}
    should_be_pro = status in active_states

    new_plan = User.RecruiterPlan.PRO if should_be_pro else User.RecruiterPlan.FREE
    if user.recruiter_plan != new_plan:
        user.recruiter_plan = new_plan
        user.save(update_fields=["recruiter_plan", "updated_at"])
        print(
            f"[SUBSCRIPTION SYNC] user={user_id} plan={new_plan} "
            f"(stripe_status={status}, cancel_at_period_end={cancel_at_period_end})"
        )


def _upsert_subscription_row(user_id, sub_dict):
    """
    Idempotent Subscription upsert. Only sets fields that are actually
    present in the Stripe payload, so we never overwrite a valid DB row
    with nulls when a partial event arrives.

    Returns the Subscription instance, or None if we couldn't save.
    """
    fields = _extract_subscription_fields(sub_dict)

    try:
        subscription = Subscription.objects.filter(user_id=user_id).first()
        if subscription is None:
            # For fresh inserts, we need stripe_subscription_id (it's UNIQUE NOT NULL).
            # If Stripe hasn't given us one, skip — the next event (e.g. the
            # verify call with an expanded subscription) will create the row.
            if not fields.get("stripe_subscription_id"):
                print(f"[SUBSCRIPTION SYNC] user={user_id} no stripe_subscription_id yet; deferring row create")
                return None
            subscription = Subscription.objects.create(user_id=user_id, **fields)
            print(f"[SUBSCRIPTION SYNC] created Subscription id={subscription.id} user={user_id}")
            return subscription

        updated = []
        for key, value in fields.items():
            if getattr(subscription, key, None) != value:
                setattr(subscription, key, value)
                updated.append(key)
        if updated:
            updated.append("updated_at")
            subscription.save(update_fields=updated)
            print(f"[SUBSCRIPTION SYNC] updated Subscription id={subscription.id} fields={updated}")
        return subscription
    except Exception as e:
        print(f"[SUBSCRIPTION SYNC] DB upsert failed for user={user_id}: {e}")
        traceback.print_exc()
        return None


def handle_subscription_event(data):
    """
    Handle customer.subscription.{created,updated,deleted}.

    Persists the Subscription row (best-effort) AND syncs User.recruiter_plan
    so access flips instantly after checkout success / cancellation. Any DB
    error is logged but does not re-raise — Stripe must receive a 200 or it
    retries indefinitely.
    """
    metadata = data.get('metadata') or {}
    user_id = metadata.get('user_id')
    status = data.get('status') or ''
    cancel_at_period_end = bool(data.get('cancel_at_period_end'))

    if not user_id:
        print("[SUBSCRIPTION SYNC] event missing user_id metadata; skipping")
        return

    _upsert_subscription_row(user_id, data)
    _sync_recruiter_plan_from_subscription(user_id, status, cancel_at_period_end)


def verify_and_sync_pro_subscription(*, user, session_id):
    """
    Server-side verification path used by the /payment/subscription/success page.

    Retrieves the Stripe Checkout Session directly (expanding the subscription),
    validates the session truly belongs to this user and was paid, then
    upserts Subscription and flips User.recruiter_plan to PRO.

    This is the primary, webhook-independent path — it guarantees access
    unlocks instantly even if Stripe CLI isn't forwarding events locally.

    Returns a dict:
        {"ok": bool, "is_pro": bool, "reason": str | None}
    """
    if not session_id:
        return {"ok": False, "is_pro": False, "reason": "missing session_id"}

    try:
        session = stripe.checkout.Session.retrieve(session_id, expand=["subscription"])
    except Exception as e:
        print(f"[VERIFY SUB] retrieve session failed: {e}")
        return {"ok": False, "is_pro": False, "reason": f"stripe error: {e}"}

    session_dict = session.to_dict() if hasattr(session, "to_dict") else dict(session)
    metadata = dict(session_dict.get("metadata") or {})
    mode = session_dict.get("mode")
    payment_status = session_dict.get("payment_status")
    customer_id = session_dict.get("customer")

    print(
        f"[VERIFY SUB] user={user.id} session={session_id} "
        f"mode={mode} payment_status={payment_status} metadata={metadata}"
    )

    if mode != "subscription":
        return {"ok": False, "is_pro": False, "reason": "session is not a subscription"}

    meta_user_id = str(metadata.get("user_id") or "")
    if meta_user_id and meta_user_id != str(user.id):
        return {"ok": False, "is_pro": False, "reason": "session does not belong to this user"}

    if payment_status not in ("paid", "no_payment_required"):
        return {"ok": False, "is_pro": False, "reason": f"payment_status={payment_status}"}

    subscription_obj = session_dict.get("subscription")
    if isinstance(subscription_obj, str):
        try:
            stripe_sub = stripe.Subscription.retrieve(subscription_obj).to_dict()
        except Exception as e:
            print(f"[VERIFY SUB] retrieve subscription failed: {e}")
            stripe_sub = None
    elif isinstance(subscription_obj, dict):
        stripe_sub = subscription_obj
    else:
        stripe_sub = None

    if not stripe_sub:
        # Fallback: still flip the user since Stripe confirmed paid; DB row will
        # be completed by the webhook when/if it arrives.
        _sync_recruiter_plan_from_subscription(user.id, "active", False)
        return {"ok": True, "is_pro": True, "reason": "flipped without DB row"}

    sub_status = stripe_sub.get("status") or "active"
    cancel_at_period_end = bool(stripe_sub.get("cancel_at_period_end"))

    # Flip the user first — DB row sync is secondary bookkeeping.
    _sync_recruiter_plan_from_subscription(user.id, sub_status, cancel_at_period_end)

    # Best-effort DB upsert. Failures are logged but don't break the verify flow.
    subscription = _upsert_subscription_row(user.id, stripe_sub)

    if customer_id:
        try:
            Customer.objects.filter(user=user).update(stripe_customer_id=customer_id)
        except Exception:
            pass

    print(
        f"[VERIFY SUB] done user={user.id} stripe_sub={stripe_sub.get('id')} "
        f"status={sub_status} db_row_id={getattr(subscription, 'id', None)}"
    )

    return {"ok": True, "is_pro": sub_status in ("active", "trialing"), "reason": None}


def handle_subscription_checkout_completed(session):
    """
    Called from checkout.session.completed when mode == 'subscription'.

    Grants Pro IMMEDIATELY by flipping User.recruiter_plan using session metadata
    (user_id). We don't create a Subscription row here because the dedicated
    customer.subscription.created webhook fires right after with the full
    period_start/period_end data; that handler persists the Subscription row.
    """
    metadata = dict(session.get('metadata') or {})
    user_id = metadata.get('user_id')
    subscription_id = session.get('subscription')
    if not user_id:
        print("[SUBSCRIPTION CHECKOUT] missing user_id metadata; skipping")
        return

    print(f"[SUBSCRIPTION CHECKOUT] user={user_id} subscription={subscription_id} -> PRO")
    _sync_recruiter_plan_from_subscription(user_id, "active", False)