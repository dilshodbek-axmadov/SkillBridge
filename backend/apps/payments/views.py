from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from django.conf import settings

from .serializers import (
    CreateCheckoutSessionSerializer,
    CreatePaymentIntentSerializer,
)
from .services import (
    create_checkout_session,
    create_payment_intent,
    cancel_subscription,
)


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        price_id = serializer.validated_data["price_id"]

        success_url = settings.STRIPE_SUCCESS_URL
        cancel_url = settings.STRIPE_CANCEL_URL

        checkout_url = create_checkout_session(
            user=request.user,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return Response({"checkout_url": checkout_url}, status=status.HTTP_200_OK)


class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_secret = create_payment_intent(
            user=request.user,
            amount=serializer.validated_data["amount"],
            currency=serializer.validated_data.get("currency", "usd"),
            payment_type=serializer.validated_data["payment_type"],
        )

        return Response({"client_secret": client_secret}, status=status.HTTP_200_OK)


class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        success = cancel_subscription(request.user)

        if not success:
            return Response(
                {"detail": "Subscription not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"detail": "Subscription will be canceled"}, status=status.HTTP_200_OK)