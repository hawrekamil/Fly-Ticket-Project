"""
Flights Models
==============
Core data models for the flight booking lifecycle.

Models:
    OfferRequest — A flight search query and its Duffel response.
    OfferSnapshot — A cached snapshot of a single fare offer.
    Order — A flight booking with state-machine lifecycle.
    Passenger — Traveler details linked to an order.
"""

import string
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


def generate_booking_reference():
    """
    Generate a human-readable booking reference.

    Format: FLY-XXXXXX (uppercase alphanumeric, 6 chars).
    Example: FLY-A1B2C3
    """
    chars = string.ascii_uppercase + string.digits
    code = get_random_string(length=6, allowed_chars=chars)
    return f"FLY-{code}"


class OfferRequest(models.Model):
    """
    Represents a flight search query sent to the Duffel API.

    Stores the search parameters and the raw Duffel response for auditing
    and debugging. Each OfferRequest produces multiple OfferSnapshots.
    """

    class CabinClass(models.TextChoices):
        ECONOMY = "economy", "Economy"
        PREMIUM_ECONOMY = "premium_economy", "Premium Economy"
        BUSINESS = "business", "Business"
        FIRST = "first", "First"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    duffel_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Duffel offer request ID (orq_*).",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offer_requests",
        help_text="User who initiated the search (null for anonymous).",
    )

    # Search parameters
    origin = models.CharField(max_length=50, help_text="Origin IATA airport or country code.")
    destination = models.CharField(max_length=50, help_text="Destination IATA airport or country code.")
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True, help_text="For round-trip searches.")
    cabin_class = models.CharField(
        max_length=20,
        choices=CabinClass.choices,
        default=CabinClass.ECONOMY,
    )
    adult_count = models.PositiveIntegerField(default=1)
    child_count = models.PositiveIntegerField(default=0)
    infant_count = models.PositiveIntegerField(default=0)

    # Raw Duffel API response (JSONB in PostgreSQL, JSON in SQLite)
    raw_response = models.JSONField(
        default=dict,
        help_text="Full Duffel offer_request response for auditing.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Offer Request"
        verbose_name_plural = "Offer Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.origin}→{self.destination} ({self.departure_date}) [{self.duffel_id}]"


class OfferSnapshot(models.Model):
    """
    A cached snapshot of a single flight offer from Duffel.

    Preserves the exact fare details shown to the customer at the time of
    search. The raw_offer JSONB column stores the complete Duffel offer
    payload including baggage, segments, and pricing breakdowns.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    duffel_offer_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Duffel offer ID (off_*).",
    )
    offer_request = models.ForeignKey(
        OfferRequest,
        on_delete=models.CASCADE,
        related_name="offers",
    )

    # Denormalized fields for fast filtering and display
    airline_name = models.CharField(max_length=200, help_text="Marketing carrier name.")
    airline_iata = models.CharField(max_length=3, help_text="Marketing carrier IATA code.")
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total fare amount.",
    )
    total_currency = models.CharField(max_length=3, help_text="ISO 4217 currency code.")
    stops = models.PositiveIntegerField(default=0, help_text="Number of stops (0 = direct).")
    departure_time = models.DateTimeField(help_text="First segment departure time.")
    arrival_time = models.DateTimeField(help_text="Last segment arrival time.")
    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Total journey duration.",
    )
    cabin_class = models.CharField(max_length=20)

    # Audit data
    raw_offer = models.JSONField(
        default=dict,
        help_text="Full Duffel offer payload (pricing, segments, baggage).",
    )
    expires_at = models.DateTimeField(
        help_text="Offer expiration timestamp from Duffel.",
    )
    requires_instant_payment = models.BooleanField(
        default=True,
        help_text="Whether this offer requires immediate payment (no hold).",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Offer Snapshot"
        verbose_name_plural = "Offer Snapshots"
        ordering = ["total_amount"]
        indexes = [
            models.Index(fields=["duffel_offer_id"]),
            models.Index(fields=["total_amount"]),
            models.Index(fields=["departure_time"]),
        ]

    def __str__(self):
        return (
            f"{self.airline_iata} {self.total_amount} {self.total_currency} "
            f"({self.stops} stops) [{self.duffel_offer_id}]"
        )

    @property
    def is_expired(self):
        """Check if this offer has passed its expiration time."""
        return timezone.now() >= self.expires_at


class Order(models.Model):
    """
    A flight booking order with a state-machine lifecycle.

    Supports two flows:
    - Instant: Customer pays online → order confirmed immediately.
    - Hold: Seat held without payment → customer pays cash at desk.

    Status transitions are enforced via the transition_status() method.
    """

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending Payment"
        HOLD_PENDING_CASH = "hold_pending_cash", "Hold — Pending Cash"
        CONFIRMED = "confirmed", "Confirmed"
        EXPIRED = "expired", "Expired"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    class OrderType(models.TextChoices):
        INSTANT = "instant", "Instant (Online Payment)"
        HOLD = "hold", "Hold (Cash Payment)"

    # Valid state transitions
    ALLOWED_TRANSITIONS = {
        Status.PENDING_PAYMENT: [Status.CONFIRMED, Status.FAILED, Status.CANCELLED],
        Status.HOLD_PENDING_CASH: [Status.CONFIRMED, Status.EXPIRED, Status.CANCELLED],
        # Terminal states — no outgoing transitions
        Status.CONFIRMED: [],
        Status.EXPIRED: [],
        Status.FAILED: [],
        Status.CANCELLED: [],
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    duffel_order_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Duffel order ID (ord_*). Null until Duffel order is created.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    offer_snapshot = models.ForeignKey(
        OfferSnapshot,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    booking_reference = models.CharField(
        max_length=20,
        unique=True,
        default=generate_booking_reference,
        help_text="Human-readable booking reference (e.g., FLY-A1B2C3).",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )
    order_type = models.CharField(
        max_length=10,
        choices=OrderType.choices,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_currency = models.CharField(max_length=3)

    # Hold-specific fields
    hold_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Duffel hold expiration timestamp. Only set for hold orders.",
    )

    # Audit snapshots
    order_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Full Duffel order response at time of creation.",
    )

    # Timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "hold_expires_at"]),
            models.Index(fields=["booking_reference"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return (
            f"{self.booking_reference} — {self.get_status_display()} "
            f"({self.total_amount} {self.total_currency})"
        )

    def transition_status(self, new_status: str) -> None:
        """
        Transition the order to a new status, enforcing the state machine.

        Args:
            new_status: Target status value.

        Raises:
            ValueError: If the transition is not allowed.
        """
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition: {self.status} → {new_status}. "
                f"Allowed: {allowed}"
            )

        now = timezone.now()
        self.status = new_status

        if new_status == self.Status.CONFIRMED:
            self.confirmed_at = now
        elif new_status == self.Status.EXPIRED:
            self.expired_at = now
        elif new_status == self.Status.CANCELLED:
            self.cancelled_at = now

        self.save(update_fields=["status", "confirmed_at", "expired_at", "cancelled_at", "updated_at"])

    @property
    def is_hold_expired(self):
        """Check if a hold order has passed its expiration deadline."""
        if self.order_type != self.OrderType.HOLD or not self.hold_expires_at:
            return False
        return timezone.now() >= self.hold_expires_at

    @property
    def hold_time_remaining(self):
        """Return remaining time before hold expiration, or None if not applicable."""
        if self.order_type != self.OrderType.HOLD or not self.hold_expires_at:
            return None
        remaining = self.hold_expires_at - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)


class Passenger(models.Model):
    """
    Traveler details for a booked order.

    Captures the passenger information submitted to Duffel at booking time.
    """

    class PassengerType(models.TextChoices):
        ADULT = "adult", "Adult"
        CHILD = "child", "Child"
        INFANT_WITHOUT_SEAT = "infant_without_seat", "Infant (without seat)"

    class Gender(models.TextChoices):
        MALE = "m", "Male"
        FEMALE = "f", "Female"

    class Title(models.TextChoices):
        MR = "mr", "Mr"
        MRS = "mrs", "Mrs"
        MS = "ms", "Ms"
        MISS = "miss", "Miss"
        DR = "dr", "Dr"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="passengers",
    )
    duffel_passenger_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Duffel passenger ID (pas_*).",
    )

    given_name = models.CharField(max_length=100)
    family_name = models.CharField(max_length=100)
    born_on = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    title = models.CharField(max_length=5, choices=Title.choices)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    passenger_type = models.CharField(
        max_length=25,
        choices=PassengerType.choices,
        default=PassengerType.ADULT,
    )

    class Meta:
        verbose_name = "Passenger"
        verbose_name_plural = "Passengers"

    def __str__(self):
        return f"{self.title.upper()} {self.given_name} {self.family_name} ({self.get_passenger_type_display()})"
