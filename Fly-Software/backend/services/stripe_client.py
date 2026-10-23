"""
Stripe Client Helpers
=====================
Utility functions for Stripe payment processing.

Wraps the Stripe Python SDK to provide a clean interface for:
- Creating PaymentIntents for flight booking checkout.
- Verifying webhook signatures.
"""

import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

# Configure Stripe with our secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(
    amount_cents: int,
    currency: str,
    metadata: dict | None = None,
) -> stripe.PaymentIntent:
    """
    Create a Stripe PaymentIntent for a flight booking.

    Args:
        amount_cents: Amount in the smallest currency unit (e.g., cents for EUR/USD).
        currency: ISO 4217 currency code (lowercase, e.g., 'eur', 'usd').
        metadata: Optional dict of metadata to attach to the intent
                  (e.g., order_id, user_id).

    Returns:
        Stripe PaymentIntent object.

    Raises:
        stripe.error.StripeError: On any Stripe API failure.
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency.lower(),
            metadata=metadata or {},
            automatic_payment_methods={"enabled": True},
        )
        logger.info(
            "Stripe PaymentIntent created: %s (amount=%d %s)",
            intent.id, amount_cents, currency,
        )
        return intent
    except stripe.error.StripeError as e:
        logger.error("Stripe PaymentIntent creation failed: %s", e)
        raise


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """
    Verify a Stripe webhook signature and return the event.

    Args:
        payload: Raw request body bytes.
        sig_header: Value of the 'Stripe-Signature' header.

    Returns:
        Verified Stripe Event object.

    Raises:
        stripe.error.SignatureVerificationError: If the signature is invalid.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        logger.info("Stripe webhook verified: %s (type=%s)", event.id, event.type)
        return event
    except stripe.error.SignatureVerificationError as e:
        logger.warning("Stripe webhook signature verification failed: %s", e)
        raise


def get_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
    """
    Retrieve a PaymentIntent by ID.

    Args:
        payment_intent_id: Stripe PaymentIntent ID (pi_*).

    Returns:
        Stripe PaymentIntent object.
    """
    return stripe.PaymentIntent.retrieve(payment_intent_id)
