"""
Payments Admin
==============
Django admin configuration for payment records.
"""

from django.contrib import admin
from django.utils.html import format_html

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order_ref", "payment_method", "amount", "currency",
        "status_badge", "confirmed_by", "created_at",
    )
    list_filter = ("payment_method", "status", "created_at")
    search_fields = (
        "stripe_payment_intent_id", "duffel_payment_id",
        "order__booking_reference",
    )
    readonly_fields = (
        "id", "stripe_payment_intent_id", "duffel_payment_id",
        "raw_response", "created_at", "updated_at",
    )

    @admin.display(description="Booking Ref")
    def order_ref(self, obj):
        return obj.order.booking_reference

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending": "#f59e0b",
            "succeeded": "#10b981",
            "failed": "#ef4444",
            "refunded": "#8b5cf6",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color:{}; color:#fff; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )
