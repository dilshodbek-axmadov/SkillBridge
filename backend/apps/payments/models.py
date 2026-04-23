from django.db import models
from django.conf import settings


User = settings.AUTH_USER_MODEL


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    stripe_customer_id = models.CharField(max_length=255, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_customers'

    def __str__(self):
        return f"{self.user} - {self.stripe_customer_id}"


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELED = 'canceled', 'Canceled'
        INCOMPLETE = 'incomplete', 'Incomplete'
        PAST_DUE = 'past_due', 'Past Due'
        TRIALING = 'trialing', 'Trialing'
        UNPAID = 'unpaid', 'Unpaid'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')

    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    stripe_price_id = models.CharField(max_length=255)

    status = models.CharField(max_length=50, choices=Status.choices)

    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()

    cancel_at_period_end = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'

    def __str__(self):
        return f"{self.user} - {self.status}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'

    class PaymentType(models.TextChoices):
        CV_DOWNLOAD = 'cv_download', 'CV Download'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')

    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)

    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=10, default='usd')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_type = models.CharField(max_length=50, choices=PaymentType.choices)

    metadata = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type']),
        ]

    def __str__(self):
        return f"{self.user} - {self.payment_type} - {self.status}"