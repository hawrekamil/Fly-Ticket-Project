"""
Flights URL Configuration
=========================
"""

from django.urls import path

from flights.views import (
    AirportSuggestionsView,
    CreateOrderView,
    FlightSearchView,
    OfferDetailView,
    OrderDetailView,
    OrderListView,
)

app_name = "flights"

urlpatterns = [
    path("airports/suggestions/", AirportSuggestionsView.as_view(), name="airport-suggestions"),
    path("search/", FlightSearchView.as_view(), name="search"),
    path("offers/<uuid:offer_id>/", OfferDetailView.as_view(), name="offer-detail"),
    path("book/", CreateOrderView.as_view(), name="book"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<uuid:id>/", OrderDetailView.as_view(), name="order-detail"),
]
