"""
Flights Admin
=============
Django admin configuration for flight booking models.
"""

from django.contrib import admin
from django.utils.html import format_html

from flights.models import OfferRequest, OfferSnapshot, Order, Passenger


class OfferSnapshotInline(admin.TabularInline):
    """Inline display of offer snapshots within an OfferRequest."""

    model = OfferSnapshot
    extra = 0
    readonly_fields = (
        "duffel_offer_id", "airline_name", "airline_iata",
        "total_amount", "total_currency", "stops",
        "departure_time", "arrival_time", "expires_at",
    )
    can_delete = False
    show_change_link = True


@admin.register(OfferRequest)
class OfferRequestAdmin(admin.ModelAdmin):
    list_display = (
        "duffel_id", "origin", "destination", "departure_date",
        "cabin_class", "adult_count", "user", "created_at",
    )
    list_filter = ("cabin_class", "created_at")
    search_fields = ("duffel_id", "origin", "destination", "user__username")
    readonly_fields = ("id", "duffel_id", "raw_response", "created_at")
    inlines = [OfferSnapshotInline]


@admin.register(OfferSnapshot)
class OfferSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "duffel_offer_id", "airline_name", "total_amount",
        "total_currency", "stops", "departure_time", "expires_at",
        "requires_instant_payment",
    )
    list_filter = ("airline_iata", "cabin_class", "requires_instant_payment")
    search_fields = ("duffel_offer_id", "airline_name")
    readonly_fields = ("id", "raw_offer", "created_at")


class PassengerInline(admin.TabularInline):
    """Inline display of passengers within an Order."""

    model = Passenger
    extra = 0
    readonly_fields = (
        "duffel_passenger_id", "given_name", "family_name",
        "born_on", "gender", "title", "email", "phone_number",
        "passenger_type",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference", "status_badge", "order_type",
        "total_amount", "total_currency", "user",
        "hold_expires_at", "created_at",
    )
    list_filter = ("status", "order_type", "created_at")
    search_fields = ("booking_reference", "duffel_order_id", "user__username")
    readonly_fields = (
        "id", "booking_reference", "duffel_order_id", "order_snapshot",
        "confirmed_at", "expired_at", "cancelled_at", "created_at", "updated_at",
    )
    inlines = [PassengerInline]

    @admin.display(description="Status")
    def status_badge(self, obj):
        """Display order status with color-coded badge."""
        colors = {
            "pending_payment": "#f59e0b",    # Amber
            "hold_pending_cash": "#3b82f6",  # Blue
            "confirmed": "#10b981",          # Green
            "expired": "#6b7280",            # Gray
            "failed": "#ef4444",             # Red
            "cancelled": "#8b5cf6",          # Purple
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color:{}; color:#fff; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = (
        "given_name", "family_name", "passenger_type",
        "email", "order",
    )
    list_filter = ("passenger_type",)
    search_fields = ("given_name", "family_name", "email")
