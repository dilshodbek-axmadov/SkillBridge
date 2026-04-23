from django.contrib import admin
from .models import Customer, Subscription, Payment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "stripe_customer_id", "created_at")
    search_fields = ("user__email", "stripe_customer_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "stripe_subscription_id",
        "current_period_start",
        "current_period_end",
        "cancel_at_period_end",
    )
    list_filter = ("status", "cancel_at_period_end")
    search_fields = ("user__email", "stripe_subscription_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "payment_type",
        "amount",
        "currency",
        "status",
        "stripe_payment_intent_id",
        "created_at",
    )
    list_filter = ("status", "payment_type", "currency")
    search_fields = ("user__email", "stripe_payment_intent_id")
    readonly_fields = ("created_at", "updated_at")