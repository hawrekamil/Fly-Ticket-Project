"""
Payments URL Configuration
==========================
"""

from django.urls import path

from payments.views import AgentOrderListView, ConfirmCashPaymentView, StripeWebhookView

app_name = "payments"

urlpatterns = [
    path("webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path(
        "confirm-cash/<uuid:order_id>/",
        ConfirmCashPaymentView.as_view(),
        name="confirm-cash",
    ),
    path("hold-orders/", AgentOrderListView.as_view(), name="hold-orders"),
]
