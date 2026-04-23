from django.urls import path

from .views import (
    CreateCheckoutSessionView,
    CreatePaymentIntentView,
    CancelSubscriptionView,
)
from .webhooks import stripe_webhook

urlpatterns = [
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel-subscription'),

    # Stripe webhook
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]
