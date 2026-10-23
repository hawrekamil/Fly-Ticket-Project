"""
Flights Background Tasks
========================
Django-Q2 scheduled tasks for order lifecycle management.

These tasks run as background workers and handle:
- Expiring stale hold orders past their Duffel deadline.
- Notifying customers/staff about expiring hold orders.
- Sending booking confirmation emails.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from flights.models import Order

logger = logging.getLogger(__name__)


def expire_stale_hold_orders():
    """
    Sweep and expire hold orders that have passed their Duffel hold deadline.

    This task should be scheduled to run every 5 minutes via Django-Q2.
    It queries for orders in 'hold_pending_cash' status whose
    hold_expires_at has elapsed, and transitions them to 'expired'.

    Schedule configuration (run via Django admin or management command):
        Schedule.objects.create(
            func='flights.tasks.expire_stale_hold_orders',
            schedule_type=Schedule.MINUTES,
            minutes=5,
            name='expire-stale-hold-orders',
        )
    """
    now = timezone.now()
    stale_orders = Order.objects.filter(
        status=Order.Status.HOLD_PENDING_CASH,
        hold_expires_at__lt=now,
    )

    count = 0
    for order in stale_orders:
        try:
            order.transition_status(Order.Status.EXPIRED)
            count += 1
            logger.info(
                "Hold order expired: %s (ref=%s, expired_at=%s)",
                order.id, order.booking_reference, order.hold_expires_at,
            )
        except ValueError as e:
            logger.error(
                "Failed to expire order %s: %s",
                order.id, e,
            )

    if count > 0:
        logger.info("Expired %d stale hold order(s).", count)

    return f"Expired {count} order(s)"


def notify_expiring_cash_hold():
    """
    Alert customers and staff about hold orders expiring within N hours.

    This task should be scheduled to run every hour via Django-Q2.
    It finds hold orders expiring within HOLD_EXPIRY_NOTIFICATION_HOURS
    (default: 4 hours) and sends notification emails.
    """
    lead_hours = getattr(settings, "HOLD_EXPIRY_NOTIFICATION_HOURS", 4)
    now = timezone.now()
    threshold = now + timezone.timedelta(hours=lead_hours)

    expiring_orders = Order.objects.filter(
        status=Order.Status.HOLD_PENDING_CASH,
        hold_expires_at__gt=now,
        hold_expires_at__lte=threshold,
    ).select_related("user")

    count = 0
    for order in expiring_orders:
        try:
            remaining = order.hold_expires_at - now
            hours_left = remaining.total_seconds() / 3600

            send_mail(
                subject=f"⚠️ Booking {order.booking_reference} — Expiring Soon",
                message=(
                    f"Dear {order.user.get_full_name() or order.user.username},\n\n"
                    f"Your flight booking {order.booking_reference} is being held "
                    f"and will expire in approximately {hours_left:.1f} hours.\n\n"
                    f"Amount due: {order.total_amount} {order.total_currency}\n"
                    f"Deadline: {order.hold_expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                    f"Please visit our desk to complete your payment before the deadline.\n\n"
                    f"— BookingSoft"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=True,
            )
            count += 1
            logger.info(
                "Expiry notification sent for order %s (ref=%s, expires in %.1f hours)",
                order.id, order.booking_reference, hours_left,
            )
        except Exception as e:
            logger.error(
                "Failed to send expiry notification for order %s: %s",
                order.id, e,
            )

    return f"Notified {count} expiring order(s)"


def send_booking_confirmation(order_id: str):
    """
    Send a booking confirmation email after successful payment.

    This is queued as an async task to avoid blocking the HTTP response.

    Args:
        order_id: UUID string of the confirmed order.
    """
    try:
        order = Order.objects.select_related("user", "offer_snapshot").get(id=order_id)
    except Order.DoesNotExist:
        logger.error("Cannot send confirmation — order %s not found.", order_id)
        return f"Order {order_id} not found"

    if order.status != Order.Status.CONFIRMED:
        logger.warning(
            "Skipping confirmation email for order %s — status is %s",
            order_id, order.status,
        )
        return f"Order {order_id} not confirmed"

    offer = order.offer_snapshot

    send_mail(
        subject=f"✅ Booking Confirmed — {order.booking_reference}",
        message=(
            f"Dear {order.user.get_full_name() or order.user.username},\n\n"
            f"Your flight booking has been confirmed!\n\n"
            f"Booking Reference: {order.booking_reference}\n"
            f"Route: {offer.airline_name} ({offer.airline_iata})\n"
            f"Departure: {offer.departure_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"Total Paid: {order.total_amount} {order.total_currency}\n"
            f"Payment Method: {order.get_order_type_display()}\n\n"
            f"Thank you for booking with BookingSoft!\n\n"
            f"— BookingSoft"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )

    logger.info(
        "Booking confirmation sent for order %s (ref=%s)",
        order_id, order.booking_reference,
    )
    return f"Confirmation sent for {order.booking_reference}"
