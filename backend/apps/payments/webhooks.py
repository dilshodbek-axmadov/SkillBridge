import json
import traceback
from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


def _cents_to_decimal(cents):
    try:
        n = int(cents or 0)
    except Exception:
        n = 0
    return (Decimal(n) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _coerce_pi_id(value):
    """PaymentIntent in JSON is either a string id or an expanded object."""
    if not value:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id")
    return None


def _record_cv_payment(*, payment_intent_id, user_id, amount_cents, currency, metadata, status):
    """Create or update the Payment row for a CV download."""
    if not payment_intent_id:
        print("[STRIPE WEBHOOK] no payment_intent_id; skipping")
        return None
    if not user_id:
        print("[STRIPE WEBHOOK] no user_id in metadata; skipping")
        return None

    payment_type = metadata.get("payment_type") or Payment.PaymentType.CV_DOWNLOAD.value

    payment, created = Payment.objects.get_or_create(
        stripe_payment_intent_id=payment_intent_id,
        defaults={
            "user_id": user_id,
            "amount": _cents_to_decimal(amount_cents),
            "currency": currency or "usd",
            "payment_type": payment_type,
            "status": status,
            "metadata": metadata,
        },
    )

    if not created:
        payment.status = status
        merged = dict(payment.metadata or {})
        merged.update(metadata)
        payment.metadata = merged
        payment.save(update_fields=["status", "metadata", "updated_at"])

    print(
        f"[STRIPE WEBHOOK] Payment {'created' if created else 'updated'}: "
        f"id={payment.id} user_id={user_id} intent={payment_intent_id} status={status}"
    )
    return payment


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    # Verify signature (but use the raw JSON body for actual data extraction).
    try:
        stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError as e:
        print(f"[STRIPE WEBHOOK] bad signature: {e}")
        return HttpResponse(status=400)
    except ValueError as e:
        print(f"[STRIPE WEBHOOK] bad payload: {e}")
        return HttpResponse(status=400)

    # Parse to a plain dict. Avoids any StripeObject attribute-access pitfalls.
    try:
        event = json.loads(payload.decode("utf-8"))
    except Exception as e:
        print(f"[STRIPE WEBHOOK] json decode failed: {e}")
        return HttpResponse(status=400)

    event_type = event.get("type") or "unknown"
    data = (event.get("data") or {}).get("object") or {}

    print(f"[STRIPE WEBHOOK] received: {event_type}")

    # =========================================================
    # CHECKOUT SESSION COMPLETED
    # Route by mode: 'payment' -> CV one-time; 'subscription' -> recruiter pro.
    # =========================================================
    if event_type == "checkout.session.completed":
        try:
            session_id = data.get("id")
            mode = data.get("mode") or "payment"
            metadata = dict(data.get("metadata") or {})
            payment_intent_id = _coerce_pi_id(data.get("payment_intent"))
            amount_total = data.get("amount_total") or 0
            currency = data.get("currency") or "usd"

            print(
                f"[STRIPE WEBHOOK] checkout.session.completed session={session_id} "
                f"mode={mode} pi={payment_intent_id} metadata={metadata}"
            )

            if mode == "subscription":
                # Recruiter Pro subscription purchase – grant access immediately.
                from .services import handle_subscription_checkout_completed
                handle_subscription_checkout_completed(data)
                return HttpResponse(status=200)

            # Default: one-time CV payment flow.
            metadata["checkout_session_id"] = session_id or ""

            _record_cv_payment(
                payment_intent_id=payment_intent_id,
                user_id=metadata.get("user_id"),
                amount_cents=amount_total,
                currency=currency,
                metadata=metadata,
                status=Payment.Status.SUCCEEDED,
            )
        except Exception as e:
            print(f"[STRIPE WEBHOOK] checkout.session.completed error: {e}")
            traceback.print_exc()
        return HttpResponse(status=200)

    # =========================================================
    # PAYMENT INTENT SUCCEEDED (backup path)
    # =========================================================
    if event_type == "payment_intent.succeeded":
        try:
            intent_id = data.get("id")
            metadata = dict(data.get("metadata") or {})
            amount = data.get("amount_received") or data.get("amount") or 0
            currency = data.get("currency") or "usd"

            print(
                f"[STRIPE WEBHOOK] payment_intent.succeeded intent={intent_id} "
                f"metadata={metadata}"
            )

            _record_cv_payment(
                payment_intent_id=intent_id,
                user_id=metadata.get("user_id"),
                amount_cents=amount,
                currency=currency,
                metadata=metadata,
                status=Payment.Status.SUCCEEDED,
            )
        except Exception as e:
            print(f"[STRIPE WEBHOOK] payment_intent.succeeded error: {e}")
            traceback.print_exc()
        return HttpResponse(status=200)

    # =========================================================
    # PAYMENT INTENT FAILED
    # =========================================================
    if event_type == "payment_intent.payment_failed":
        try:
            intent_id = data.get("id")
            metadata = dict(data.get("metadata") or {})
            amount = data.get("amount") or 0
            currency = data.get("currency") or "usd"

            _record_cv_payment(
                payment_intent_id=intent_id,
                user_id=metadata.get("user_id"),
                amount_cents=amount,
                currency=currency,
                metadata=metadata,
                status=Payment.Status.FAILED,
            )
        except Exception as e:
            print(f"[STRIPE WEBHOOK] payment_intent.payment_failed error: {e}")
            traceback.print_exc()
        return HttpResponse(status=200)

    # =========================================================
    # SUBSCRIPTIONS (unchanged)
    # =========================================================
    if event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        try:
            from .services import handle_subscription_event
            handle_subscription_event(data)
        except Exception as e:
            print(f"[STRIPE WEBHOOK] subscription handler error: {e}")
            traceback.print_exc()
        return HttpResponse(status=200)

    return HttpResponse(status=200)
