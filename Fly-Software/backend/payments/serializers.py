"""
Payments Serializers
====================
"""

from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Read-only serializer for payment records."""

    order_booking_reference = serializers.CharField(
        source="order.booking_reference",
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_booking_reference",
            "payment_method",
            "amount",
            "currency",
            "status",
            "stripe_payment_intent_id",
            "duffel_payment_id",
            "confirmed_by",
            "created_at",
        ]
        read_only_fields = fields


class CreatePaymentIntentSerializer(serializers.Serializer):
    """Validates a request to create a Stripe PaymentIntent."""

    order_id = serializers.UUIDField(
        help_text="UUID of the order to pay for.",
    )


class ConfirmCashPaymentSerializer(serializers.Serializer):
    """Validates a cash payment confirmation by a desk agent."""

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional notes about the cash payment.",
    )
