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
    customer = get_or_create_customer(user)

    session = stripe.checkout.Session.create(
        customer=customer.stripe_customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
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
def create_payment_intent(user, amount, currency='usd', payment_type='cv_download'):
    customer = get_or_create_customer(user)

    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),  # convert to cents
        currency=currency,
        customer=customer.stripe_customer_id,
        metadata={
            "user_id": user.id,
            "payment_type": payment_type
        }
    )

    payment = Payment.objects.create(
        user=user,
        stripe_payment_intent_id=intent.id,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        status=Payment.Status.PENDING
    )

    return intent.client_secret


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


def handle_subscription_event(data):
    user_id = data['metadata'].get('user_id')
    stripe_subscription_id = data['id']

    if not user_id:
        return

    subscription, _ = Subscription.objects.get_or_create(user_id=user_id)

    subscription.stripe_subscription_id = stripe_subscription_id
    subscription.stripe_price_id = data['items']['data'][0]['price']['id']
    subscription.status = data['status']

    subscription.current_period_start = timezone.datetime.fromtimestamp(
        data['current_period_start'], tz=timezone.utc
    )
    subscription.current_period_end = timezone.datetime.fromtimestamp(
        data['current_period_end'], tz=timezone.utc
    )

    subscription.cancel_at_period_end = data['cancel_at_period_end']
    subscription.save()