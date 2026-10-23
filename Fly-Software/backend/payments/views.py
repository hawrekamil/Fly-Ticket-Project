"""
Payments Views
==============
Handles Stripe webhook processing and cash payment confirmations.

The cash confirmation endpoint is the most critical path in the system.
It uses database row-locking (select_for_update) to prevent race conditions
between concurrent agent confirmations and automated expiry tasks.
"""

import logging

from asgiref.sync import async_to_sync
from django.db import transaction
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAgent
from flights.models import Order
from flights.serializers import OrderSerializer
from payments.models import Payment
from payments.serializers import ConfirmCashPaymentSerializer, PaymentSerializer
from services.duffel_client import DuffelAPIError, duffel_client

logger = logging.getLogger(__name__)


class StripeWebhookView(APIView):
    """
    POST /api/v1/payments/webhook/stripe/

    Stripe webhook endpoint.
    Handles payment_intent.succeeded events to trigger Duffel order creation.

    This endpoint verifies the webhook signature and is exempt from
    CSRF and session authentication.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        from services.stripe_client import verify_webhook_signature

        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = verify_webhook_signature(payload, sig_header)
        except Exception as e:
            logger.warning("Stripe webhook signature failed: %s", e)
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if event["type"] == "payment_intent.succeeded":
            self._handle_payment_succeeded(event)
        elif event["type"] == "payment_intent.payment_failed":
            self._handle_payment_failed(event)
        else:
            logger.info("Unhandled Stripe event type: %s", event["type"])

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    def _handle_payment_succeeded(self, event):
        """
        On successful Stripe payment:
        1. Find the Payment record by PaymentIntent ID.
        2. Call Duffel POST /air/orders (type=instant) to issue tickets.
        3. Transition order to confirmed.
        4. Queue confirmation email.
        """
        intent = event["data"]["object"]
        intent_id = intent["id"]
        metadata = intent.get("metadata", {})
        order_id = metadata.get("order_id")

        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
        except Payment.DoesNotExist:
            logger.error("No Payment found for Stripe intent %s", intent_id)
            return

        order = payment.order

        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order.id)

            if order.status != Order.Status.PENDING_PAYMENT:
                logger.warning(
                    "Order %s is not pending_payment (status=%s), skipping.",
                    order.id, order.status,
                )
                return

            # Create Duffel instant order
            duffel_offer_id = metadata.get("duffel_offer_id", "")
            if duffel_offer_id:
                try:
                    passengers = list(order.passengers.all())
                    duffel_passengers = [
                        {
                            "id": p.duffel_passenger_id,
                            "given_name": p.given_name,
                            "family_name": p.family_name,
                            "born_on": p.born_on.isoformat(),
                            "gender": p.gender,
                            "title": p.title,
                            "email": p.email,
                            "phone_number": p.phone_number,
                            "type": p.passenger_type,
                        }
                        for p in passengers
                    ]

                    duffel_response = async_to_sync(duffel_client.create_order)(
                        selected_offers=[duffel_offer_id],
                        passengers=duffel_passengers,
                        order_type="instant",
                        payments=[
                            {
                                "type": "balance",
                                "amount": str(order.total_amount),
                                "currency": order.total_currency,
                            }
                        ],
                    )

                    duffel_order = duffel_response.get("data", {})
                    order.duffel_order_id = duffel_order.get("id")
                    order.order_snapshot = duffel_response

                except DuffelAPIError as e:
                    logger.error(
                        "Duffel order creation failed for order %s: %s",
                        order.id, e,
                    )
                    payment.status = Payment.PaymentStatus.FAILED
                    payment.save(update_fields=["status", "updated_at"])
                    order.transition_status(Order.Status.FAILED)
                    return

            # Confirm order and payment
            payment.status = Payment.PaymentStatus.SUCCEEDED
            payment.raw_response = intent
            payment.save(update_fields=["status", "raw_response", "updated_at"])

            order.transition_status(Order.Status.CONFIRMED)

        # Queue confirmation email (outside transaction)
        async_task("flights.tasks.send_booking_confirmation", str(order.id))

        logger.info(
            "Stripe payment succeeded → order %s confirmed (ref=%s)",
            order.id, order.booking_reference,
        )

    def _handle_payment_failed(self, event):
        """Handle failed Stripe payment."""
        intent = event["data"]["object"]
        intent_id = intent["id"]

        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
        except Payment.DoesNotExist:
            return

        payment.status = Payment.PaymentStatus.FAILED
        payment.raw_response = intent
        payment.save(update_fields=["status", "raw_response", "updated_at"])

        order = payment.order
        if order.status == Order.Status.PENDING_PAYMENT:
            order.transition_status(Order.Status.FAILED)

        logger.warning(
            "Stripe payment failed for order %s (ref=%s)",
            order.id, order.booking_reference,
        )


class ConfirmCashPaymentView(APIView):
    """
    POST /api/v1/payments/confirm-cash/<order_id>/

    Desk agent endpoint to confirm cash receipt for a held order.

    This is the most critical path in the system. It uses:
    - select_for_update() row locking to prevent race conditions
    - Duffel POST /air/payments to finalize ticketing
    - Atomic transaction wrapping the entire operation

    Only accessible by users with 'agent' or 'admin' role.
    """

    permission_classes = [permissions.IsAuthenticated, IsAgent]
    serializer_class = ConfirmCashPaymentSerializer

    def post(self, request, order_id):
        serializer = ConfirmCashPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Row-lock the order to prevent concurrent modifications
                order = (
                    Order.objects
                    .select_for_update()
                    .select_related("offer_snapshot")
                    .get(id=order_id)
                )

                # Validate order state
                if order.status != Order.Status.HOLD_PENDING_CASH:
                    return Response(
                        {
                            "error": (
                                f"Order is not awaiting cash payment "
                                f"(current status: {order.get_status_display()})."
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                # Check if hold has expired
                if order.is_hold_expired:
                    order.transition_status(Order.Status.EXPIRED)
                    return Response(
                        {"error": "Hold has expired. The seat is no longer reserved."},
                        status=status.HTTP_410_GONE,
                    )

                # Call Duffel POST /air/payments to finalize ticketing
                try:
                    duffel_response = async_to_sync(duffel_client.create_payment)(
                        order_id=order.duffel_order_id,
                        amount=str(order.total_amount),
                        currency=order.total_currency,
                    )
                except DuffelAPIError as e:
                    logger.error(
                        "Duffel payment failed for order %s: %s",
                        order.id, e,
                    )
                    return Response(
                        {"error": f"Payment processing failed: {e}"},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )

                duffel_payment_data = duffel_response.get("data", {})

                # Create payment record
                payment = Payment.objects.create(
                    order=order,
                    payment_method=Payment.PaymentMethod.CASH,
                    duffel_payment_id=duffel_payment_data.get("id"),
                    amount=order.total_amount,
                    currency=order.total_currency,
                    status=Payment.PaymentStatus.SUCCEEDED,
                    confirmed_by=request.user,
                    raw_response=duffel_response,
                )

                # Transition order to confirmed
                order.transition_status(Order.Status.CONFIRMED)

                logger.info(
                    "Cash payment confirmed for order %s (ref=%s) by agent %s",
                    order.id, order.booking_reference, request.user.username,
                )

        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Queue confirmation email (outside transaction)
        async_task("flights.tasks.send_booking_confirmation", str(order.id))

        return Response(
            {
                "message": "Cash payment confirmed. Tickets have been issued.",
                "order": OrderSerializer(order).data,
                "payment": PaymentSerializer(payment).data,
            },
            status=status.HTTP_200_OK,
        )


class AgentOrderListView(APIView):
    """
    GET /api/v1/payments/hold-orders/

    List all orders in 'hold_pending_cash' status for desk agents.
    Only accessible by users with 'agent' or 'admin' role.
    """

    permission_classes = [permissions.IsAuthenticated, IsAgent]

    def get(self, request):
        orders = (
            Order.objects
            .filter(status=Order.Status.HOLD_PENDING_CASH)
            .select_related("user", "offer_snapshot")
            .prefetch_related("passengers")
            .order_by("hold_expires_at")  # Urgent first
        )

        serializer = OrderSerializer(orders, many=True)
        return Response(
            {
                "total": orders.count(),
                "orders": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
