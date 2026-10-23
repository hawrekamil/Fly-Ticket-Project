"""
Order State Machine Tests
=========================
Tests for the Order model's status transition enforcement.
"""

import pytest
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from flights.models import OfferRequest, OfferSnapshot, Order, generate_booking_reference


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def offer_snapshot(db, user):
    """Create a test offer request and snapshot."""
    offer_request = OfferRequest.objects.create(
        duffel_id="orq_test_001",
        user=user,
        origin="LHR",
        destination="JFK",
        departure_date="2025-12-01",
        cabin_class="economy",
        adult_count=1,
    )
    return OfferSnapshot.objects.create(
        duffel_offer_id="off_test_001",
        offer_request=offer_request,
        airline_name="Test Airways",
        airline_iata="TA",
        total_amount=350.00,
        total_currency="EUR",
        stops=0,
        departure_time=timezone.now() + timedelta(days=30),
        arrival_time=timezone.now() + timedelta(days=30, hours=8),
        duration=timedelta(hours=8),
        cabin_class="economy",
        expires_at=timezone.now() + timedelta(hours=1),
        requires_instant_payment=False,
    )


@pytest.fixture
def pending_order(db, user, offer_snapshot):
    """Create an order in pending_payment status."""
    return Order.objects.create(
        user=user,
        offer_snapshot=offer_snapshot,
        order_type=Order.OrderType.INSTANT,
        status=Order.Status.PENDING_PAYMENT,
        total_amount=350.00,
        total_currency="EUR",
    )


@pytest.fixture
def hold_order(db, user, offer_snapshot):
    """Create an order in hold_pending_cash status."""
    return Order.objects.create(
        duffel_order_id="ord_test_001",
        user=user,
        offer_snapshot=offer_snapshot,
        order_type=Order.OrderType.HOLD,
        status=Order.Status.HOLD_PENDING_CASH,
        total_amount=350.00,
        total_currency="EUR",
        hold_expires_at=timezone.now() + timedelta(hours=24),
    )


class TestBookingReference:
    """Tests for booking reference generation."""

    def test_format(self):
        ref = generate_booking_reference()
        assert ref.startswith("FLY-")
        assert len(ref) == 10  # FLY- + 6 chars

    def test_uniqueness(self):
        refs = {generate_booking_reference() for _ in range(100)}
        assert len(refs) == 100  # All unique


class TestOrderStatusTransitions:
    """Tests for the Order state machine."""

    def test_pending_to_confirmed(self, pending_order):
        """Valid: pending_payment → confirmed."""
        pending_order.transition_status(Order.Status.CONFIRMED)
        assert pending_order.status == Order.Status.CONFIRMED
        assert pending_order.confirmed_at is not None

    def test_pending_to_failed(self, pending_order):
        """Valid: pending_payment → failed."""
        pending_order.transition_status(Order.Status.FAILED)
        assert pending_order.status == Order.Status.FAILED

    def test_pending_to_cancelled(self, pending_order):
        """Valid: pending_payment → cancelled."""
        pending_order.transition_status(Order.Status.CANCELLED)
        assert pending_order.status == Order.Status.CANCELLED
        assert pending_order.cancelled_at is not None

    def test_hold_to_confirmed(self, hold_order):
        """Valid: hold_pending_cash → confirmed."""
        hold_order.transition_status(Order.Status.CONFIRMED)
        assert hold_order.status == Order.Status.CONFIRMED
        assert hold_order.confirmed_at is not None

    def test_hold_to_expired(self, hold_order):
        """Valid: hold_pending_cash → expired."""
        hold_order.transition_status(Order.Status.EXPIRED)
        assert hold_order.status == Order.Status.EXPIRED
        assert hold_order.expired_at is not None

    def test_hold_to_cancelled(self, hold_order):
        """Valid: hold_pending_cash → cancelled."""
        hold_order.transition_status(Order.Status.CANCELLED)
        assert hold_order.status == Order.Status.CANCELLED

    def test_invalid_pending_to_expired(self, pending_order):
        """Invalid: pending_payment → expired (not allowed)."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            pending_order.transition_status(Order.Status.EXPIRED)

    def test_invalid_hold_to_failed(self, hold_order):
        """Invalid: hold_pending_cash → failed (not allowed)."""
        with pytest.raises(ValueError, match="Invalid status transition"):
            hold_order.transition_status(Order.Status.FAILED)

    def test_confirmed_is_terminal(self, pending_order):
        """Confirmed is a terminal state — no outgoing transitions."""
        pending_order.transition_status(Order.Status.CONFIRMED)
        with pytest.raises(ValueError, match="Invalid status transition"):
            pending_order.transition_status(Order.Status.CANCELLED)

    def test_expired_is_terminal(self, hold_order):
        """Expired is a terminal state."""
        hold_order.transition_status(Order.Status.EXPIRED)
        with pytest.raises(ValueError, match="Invalid status transition"):
            hold_order.transition_status(Order.Status.CONFIRMED)


class TestOrderHoldExpiry:
    """Tests for hold order expiration logic."""

    def test_hold_not_expired(self, hold_order):
        """Hold order with future expiration is not expired."""
        assert hold_order.is_hold_expired is False

    def test_hold_expired(self, hold_order):
        """Hold order with past expiration is expired."""
        hold_order.hold_expires_at = timezone.now() - timedelta(hours=1)
        hold_order.save()
        assert hold_order.is_hold_expired is True

    def test_hold_time_remaining(self, hold_order):
        """Should return positive timedelta when not expired."""
        remaining = hold_order.hold_time_remaining
        assert remaining is not None
        assert remaining.total_seconds() > 0

    def test_hold_time_remaining_expired(self, hold_order):
        """Should return zero timedelta when expired."""
        hold_order.hold_expires_at = timezone.now() - timedelta(hours=1)
        hold_order.save()
        remaining = hold_order.hold_time_remaining
        assert remaining == timedelta(0)

    def test_instant_order_not_applicable(self, pending_order):
        """Instant orders have no hold expiry."""
        assert pending_order.is_hold_expired is False
        assert pending_order.hold_time_remaining is None
