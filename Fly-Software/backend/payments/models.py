"""
Payments Models
===============
Payment records for tracking both Stripe and cash transactions.
"""

import uuid

from django.conf import settings
from django.db import models


class Payment(models.Model):
    """
    Tracks a payment attempt/completion for an order.

    Links both Stripe PaymentIntents and cash desk confirmations
    to their associated Order records.
    """

    class PaymentMethod(models.TextChoices):
        STRIPE = "stripe", "Credit Card (Stripe)"
        CASH = "cash", "Cash at Desk"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        "flights.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
    )

    # Stripe-specific
    stripe_payment_intent_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        unique=True,
        help_text="Stripe PaymentIntent ID (pi_*).",
    )

    # Duffel-specific (for hold order payments)
    duffel_payment_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Duffel payment ID (pay_*).",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=15,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )

    # Cash confirmation tracking
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_payments",
        help_text="Agent who confirmed cash payment.",
    )

    # Audit data
    raw_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw Stripe or Duffel payment response for auditing.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_payment_method_display()} — {self.amount} {self.currency} "
            f"({self.get_status_display()}) [{self.order.booking_reference}]"
        )
