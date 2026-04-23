from rest_framework import serializers
from .models import Payment, Subscription


class CreateCheckoutSessionSerializer(serializers.Serializer):
    price_id = serializers.CharField()


class CreatePaymentIntentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    currency = serializers.CharField(default='usd')
    payment_type = serializers.ChoiceField(choices=Payment.PaymentType.choices)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('status', 'stripe_payment_intent_id', 'created_at', 'updated_at')


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = (
            'stripe_subscription_id',
            'status',
            'current_period_start',
            'current_period_end',
            'created_at',
            'updated_at',
        )