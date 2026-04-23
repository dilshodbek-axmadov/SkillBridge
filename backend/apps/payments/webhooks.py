import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .services import (
    handle_payment_intent_succeeded,
    handle_payment_intent_failed,
    handle_subscription_event,
)


stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    except ValueError:
        return HttpResponse(status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    # Payment events
    if event_type == "payment_intent.succeeded":
        handle_payment_intent_succeeded(data)

    elif event_type == "payment_intent.payment_failed":
        handle_payment_intent_failed(data)

    # Subscription events
    elif event_type in [
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ]:
        handle_subscription_event(data)

    return HttpResponse(status=200)