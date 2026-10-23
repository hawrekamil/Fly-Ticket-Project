"""
Flights Views
=============
API views for flight search, offer retrieval, and booking.

Search is implemented as an async view for non-blocking Duffel API calls.
Booking branches between instant (Stripe) and hold (cash) flows.
"""

import asyncio
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from flights.country_airports import (
    find_country,
    resolve_location_airports,
    search_country_suggestions,
)
from flights.models import OfferRequest, OfferSnapshot, Order, Passenger
from flights.serializers import (
    CreateOrderSerializer,
    FlightSearchSerializer,
    OfferSnapshotSerializer,
    OrderSerializer,
)
from services.duffel_client import DuffelAPIError, duffel_client

logger = logging.getLogger(__name__)


class FlightSearchView(APIView):
    """
    POST /api/v1/flights/search/

    Search for flight offers via the Duffel API.

    Accepts search parameters (origin, destination, dates, passengers),
    calls Duffel asynchronously, caches offers as OfferSnapshots,
    and returns results.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = FlightSearchSerializer

    def post(self, request):
        serializer = FlightSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Resolve origin and destination (handles countries, cities, and IATA codes)
        origin_airports, origin_label, is_origin_country = resolve_location_airports(data["origin"])
        dest_airports, dest_label, is_dest_country = resolve_location_airports(data["destination"])

        # Build route pairs (limit to top combinations for speed and reliability)
        route_pairs = []
        for o in origin_airports[:3]:
            for d in dest_airports[:2]:
                if (o, d) not in route_pairs and o != d:
                    route_pairs.append((o, d))

        if not route_pairs:
            route_pairs = [(origin_airports[0], dest_airports[0])]

        # Build passengers list
        passengers = []
        for _ in range(data["adult_count"]):
            passengers.append({"type": "adult"})
        for _ in range(data["child_count"]):
            passengers.append({"type": "child"})
        for _ in range(data["infant_count"]):
            passengers.append({"type": "infant_without_seat"})

        # Async fetcher for a single route pair
        async def fetch_route(orig_code: str, dest_code: str):
            slices = [
                {
                    "origin": orig_code,
                    "destination": dest_code,
                    "departure_date": data["departure_date"].isoformat(),
                }
            ]
            if data.get("return_date"):
                slices.append(
                    {
                        "origin": dest_code,
                        "destination": orig_code,
                        "departure_date": data["return_date"].isoformat(),
                    }
                )
            return await duffel_client.create_offer_request(
                slices=slices,
                passengers=passengers,
                cabin_class=data["cabin_class"],
            )

        async def fetch_all_routes():
            tasks = [fetch_route(o, d) for o, d in route_pairs]
            return await asyncio.gather(*tasks, return_exceptions=True)

        responses = async_to_sync(fetch_all_routes)()

        # Collect offers from all successful responses
        all_offers_data = []
        seen_offer_ids = set()
        primary_duffel_id = ""
        first_successful_response = None
        errors = []

        for resp in responses:
            if isinstance(resp, Exception):
                errors.append(str(resp))
                continue
            duffel_data = resp.get("data", {})
            if not primary_duffel_id and duffel_data.get("id"):
                primary_duffel_id = duffel_data.get("id")
            if not first_successful_response:
                first_successful_response = resp
            for offer in duffel_data.get("offers", []):
                off_id = offer.get("id")
                if off_id and off_id not in seen_offer_ids:
                    seen_offer_ids.add(off_id)
                    all_offers_data.append(offer)

        if not all_offers_data and errors and not first_successful_response:
            logger.error("All flight search routes failed: %s", errors)
            return Response(
                {"error": f"Flight search failed: {errors[0]}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Sort combined offers by total_amount ascending
        all_offers_data.sort(
            key=lambda x: float(x.get("total_amount", 999999))
        )

        # Save OfferRequest to database
        offer_request = OfferRequest.objects.create(
            duffel_id=primary_duffel_id or f"multi_{uuid.uuid4().hex[:16]}",
            user=request.user if request.user.is_authenticated else None,
            origin=data["origin"],
            destination=data["destination"],
            departure_date=data["departure_date"],
            return_date=data.get("return_date"),
            cabin_class=data["cabin_class"],
            adult_count=data["adult_count"],
            child_count=data["child_count"],
            infant_count=data["infant_count"],
            raw_response=first_successful_response or {},
        )

        # Parse and save individual offers as snapshots
        snapshots = []
        for offer in all_offers_data:
            try:
                snapshot = self._create_offer_snapshot(offer, offer_request)
                snapshots.append(snapshot)
            except Exception as e:
                logger.warning("Failed to parse offer %s: %s", offer.get("id"), e)
                continue

        # Serialize and return
        serialized = OfferSnapshotSerializer(snapshots, many=True).data

        return Response(
            {
                "offer_request_id": str(offer_request.id),
                "total_offers": len(snapshots),
                "origin_label": origin_label,
                "destination_label": dest_label,
                "is_country_search": is_origin_country or is_dest_country,
                "offers": serialized,
            },
            status=status.HTTP_200_OK,
        )

    def _create_offer_snapshot(
        self, offer_data: dict, offer_request: OfferRequest
    ) -> OfferSnapshot:
        """Parse a Duffel offer and create or update an OfferSnapshot record."""
        slices = offer_data.get("slices", [])
        first_slice = slices[0] if slices else {}
        segments = first_slice.get("segments", [])
        first_segment = segments[0] if segments else {}
        last_segment = segments[-1] if segments else first_segment

        # Extract carrier info from the first segment
        owner = offer_data.get("owner", {})
        airline_name = owner.get("name", "Unknown Airline")
        airline_iata = owner.get("iata_code", "??")

        # Calculate total stops across all slices
        total_stops = sum(len(s.get("segments", [])) - 1 for s in slices)

        # Parse departure and arrival times
        departure_str = first_segment.get("departing_at", "")
        arrival_str = last_segment.get("arriving_at", "")
        departure_time = parse_datetime(departure_str) or timezone.now()
        arrival_time = parse_datetime(arrival_str) or timezone.now()

        # Calculate duration
        duration = arrival_time - departure_time if arrival_time > departure_time else None

        # Parse expiration
        expires_str = offer_data.get("expires_at", "")
        expires_at = parse_datetime(expires_str) or (timezone.now() + timedelta(minutes=30))

        # Check payment requirements
        payment_reqs = offer_data.get("payment_requirements", {})
        requires_instant = payment_reqs.get("requires_instant_payment", True)

        snapshot, _ = OfferSnapshot.objects.update_or_create(
            duffel_offer_id=offer_data.get("id", ""),
            defaults={
                "offer_request": offer_request,
                "airline_name": airline_name,
                "airline_iata": airline_iata,
                "total_amount": Decimal(offer_data.get("total_amount", "0.00")),
                "total_currency": offer_data.get("total_currency", "EUR"),
                "stops": total_stops,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": duration,
                "cabin_class": first_slice.get("fare_brand_name") or offer_request.cabin_class or "economy",
                "raw_offer": offer_data,
                "expires_at": expires_at,
                "requires_instant_payment": requires_instant,
            },
        )
        return snapshot


class OfferDetailView(APIView):
    """
    GET /api/v1/flights/offers/<offer_id>/

    Retrieve a single offer snapshot with its full details.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, offer_id):
        try:
            snapshot = OfferSnapshot.objects.get(id=offer_id)
        except OfferSnapshot.DoesNotExist:
            return Response(
                {"error": "Offer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OfferSnapshotSerializer(snapshot)
        return Response(serializer.data)


class CreateOrderView(APIView):
    """
    POST /api/v1/flights/orders/

    Create a flight booking order.

    Branches between two flows based on payment_method:
    - 'stripe': Creates a pending order and returns a Stripe PaymentIntent
                client_secret for frontend card collection.
    - 'cash':   Creates a hold order via Duffel and returns hold expiration.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        offer = validated["offer"]
        payment_method = validated["payment_method"]
        passengers_data = validated["passengers"]

        if payment_method == "cash":
            return self._handle_cash_hold(request, offer, passengers_data)
        else:
            return self._handle_stripe_instant(request, offer, passengers_data)

    def _handle_cash_hold(self, request, offer, passengers_data):
        """
        Cash-hold flow:
        1. Call Duffel POST /air/orders with type=hold (no payment).
        2. Create Order record with status=hold_pending_cash.
        3. Return hold expiration to the customer.
        """
        duffel_passengers = self._build_duffel_passengers(passengers_data, offer)

        try:
            duffel_response = async_to_sync(duffel_client.create_order)(
                selected_offers=[offer.duffel_offer_id],
                passengers=duffel_passengers,
                order_type="hold",
            )
        except DuffelAPIError as e:
            logger.error("Duffel hold order creation failed: %s", e)
            return Response(
                {"error": f"Failed to hold seat: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        duffel_order = duffel_response.get("data", {})
        hold_expires_str = duffel_order.get("payment_required_by", "")
        hold_expires_at = parse_datetime(hold_expires_str)

        # Create order record
        order = Order.objects.create(
            duffel_order_id=duffel_order.get("id"),
            user=request.user,
            offer_snapshot=offer,
            order_type=Order.OrderType.HOLD,
            status=Order.Status.HOLD_PENDING_CASH,
            total_amount=offer.total_amount,
            total_currency=offer.total_currency,
            hold_expires_at=hold_expires_at,
            order_snapshot=duffel_response,
        )

        # Save passenger records
        self._save_passengers(order, passengers_data, duffel_order)

        serializer_data = OrderSerializer(order).data

        logger.info(
            "Hold order created: %s (ref=%s, expires=%s)",
            order.id, order.booking_reference, hold_expires_at,
        )

        return Response(
            {
                "message": "Seat held successfully. Please pay at the desk before the deadline.",
                "order": serializer_data,
            },
            status=status.HTTP_201_CREATED,
        )

    def _handle_stripe_instant(self, request, offer, passengers_data):
        """
        Stripe instant flow:
        1. Create Order record with status=pending_payment.
        2. Create Stripe PaymentIntent.
        3. Return client_secret for frontend card collection.

        The actual Duffel order is created later when the Stripe webhook
        confirms payment success.
        """
        from services.stripe_client import create_payment_intent

        # Create order record (Duffel order created after payment)
        order = Order.objects.create(
            user=request.user,
            offer_snapshot=offer,
            order_type=Order.OrderType.INSTANT,
            status=Order.Status.PENDING_PAYMENT,
            total_amount=offer.total_amount,
            total_currency=offer.total_currency,
        )

        # Save passenger records
        self._save_passengers(order, passengers_data)

        # Create Stripe PaymentIntent
        amount_cents = int(offer.total_amount * 100)
        try:
            intent = create_payment_intent(
                amount_cents=amount_cents,
                currency=offer.total_currency.lower(),
                metadata={
                    "order_id": str(order.id),
                    "booking_reference": order.booking_reference,
                    "duffel_offer_id": offer.duffel_offer_id,
                },
            )
        except Exception as e:
            logger.error("Stripe PaymentIntent creation failed: %s", e)
            order.transition_status(Order.Status.FAILED)
            return Response(
                {"error": f"Payment setup failed: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Store the intent ID for webhook reconciliation
        from payments.models import Payment

        Payment.objects.create(
            order=order,
            payment_method="stripe",
            stripe_payment_intent_id=intent.id,
            amount=offer.total_amount,
            currency=offer.total_currency,
            status="pending",
        )

        serializer_data = OrderSerializer(order).data

        logger.info(
            "Stripe order created: %s (ref=%s, intent=%s)",
            order.id, order.booking_reference, intent.id,
        )

        return Response(
            {
                "message": "Complete payment to confirm booking.",
                "order": serializer_data,
                "stripe_client_secret": intent.client_secret,
                "stripe_publishable_key": "pk_test_placeholder",
            },
            status=status.HTTP_201_CREATED,
        )

    def _build_duffel_passengers(self, passengers_data, offer):
        """Build the passenger list in Duffel's expected format."""
        duffel_passengers = []
        raw_offer = offer.raw_offer
        offer_passengers = raw_offer.get("passengers", [])

        for i, pax in enumerate(passengers_data):
            duffel_pax = {
                "given_name": pax["given_name"],
                "family_name": pax["family_name"],
                "born_on": pax["born_on"].isoformat(),
                "gender": pax["gender"],
                "title": pax["title"],
                "email": pax["email"],
                "phone_number": pax["phone_number"],
                "type": pax.get("passenger_type", "adult"),
            }
            # Map to Duffel passenger IDs from the offer
            if i < len(offer_passengers):
                duffel_pax["id"] = offer_passengers[i].get("id", "")
            elif pax.get("duffel_passenger_id"):
                duffel_pax["id"] = pax["duffel_passenger_id"]

            duffel_passengers.append(duffel_pax)

        return duffel_passengers

    def _save_passengers(self, order, passengers_data, duffel_order=None):
        """Create Passenger records linked to the order."""
        duffel_passengers = []
        if duffel_order:
            duffel_passengers = duffel_order.get("passengers", [])

        for i, pax_data in enumerate(passengers_data):
            duffel_pax_id = ""
            if i < len(duffel_passengers):
                duffel_pax_id = duffel_passengers[i].get("id", "")

            Passenger.objects.create(
                order=order,
                duffel_passenger_id=duffel_pax_id,
                given_name=pax_data["given_name"],
                family_name=pax_data["family_name"],
                born_on=pax_data["born_on"],
                gender=pax_data["gender"],
                title=pax_data["title"],
                email=pax_data["email"],
                phone_number=pax_data["phone_number"],
                passenger_type=pax_data.get("passenger_type", "adult"),
            )


class OrderListView(generics.ListAPIView):
    """
    GET /api/v1/flights/orders/

    List the current user's orders.
    """

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("passengers")


class OrderDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/flights/orders/<order_id>/

    Retrieve details of a specific order.
    Users can only view their own orders. Agents can view all orders.
    """

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_agent:
            return Order.objects.all().prefetch_related("passengers")
        return Order.objects.filter(user=user).prefetch_related("passengers")

    lookup_field = "id"


POPULAR_AIRPORTS = [
    {"iata_code": "LHR", "name": "Heathrow Airport", "city_name": "London", "country": "GB"},
    {"iata_code": "LGW", "name": "Gatwick Airport", "city_name": "London", "country": "GB"},
    {"iata_code": "STN", "name": "Stansted Airport", "city_name": "London", "country": "GB"},
    {"iata_code": "JFK", "name": "John F. Kennedy International Airport", "city_name": "New York", "country": "US"},
    {"iata_code": "EWR", "name": "Newark Liberty International Airport", "city_name": "New York", "country": "US"},
    {"iata_code": "FRA", "name": "Frankfurt Airport", "city_name": "Frankfurt", "country": "DE"},
    {"iata_code": "MUC", "name": "Munich Airport", "city_name": "Munich", "country": "DE"},
    {"iata_code": "BER", "name": "Berlin Brandenburg Airport", "city_name": "Berlin", "country": "DE"},
    {"iata_code": "CDG", "name": "Charles de Gaulle Airport", "city_name": "Paris", "country": "FR"},
    {"iata_code": "ORY", "name": "Orly Airport", "city_name": "Paris", "country": "FR"},
    {"iata_code": "AMS", "name": "Schiphol Airport", "city_name": "Amsterdam", "country": "NL"},
    {"iata_code": "DXB", "name": "Dubai International Airport", "city_name": "Dubai", "country": "AE"},
    {"iata_code": "DOH", "name": "Hamad International Airport", "city_name": "Doha", "country": "QA"},
    {"iata_code": "IST", "name": "Istanbul Airport", "city_name": "Istanbul", "country": "TR"},
    {"iata_code": "SAW", "name": "Sabiha Gokcen Airport", "city_name": "Istanbul", "country": "TR"},
    {"iata_code": "EBL", "name": "Erbil International Airport", "city_name": "Erbil", "country": "IQ"},
    {"iata_code": "BGW", "name": "Baghdad International Airport", "city_name": "Baghdad", "country": "IQ"},
    {"iata_code": "BSR", "name": "Basra International Airport", "city_name": "Basra", "country": "IQ"},
    {"iata_code": "ISU", "name": "Sulaimaniyah International Airport", "city_name": "Sulaimaniyah", "country": "IQ"},
    {"iata_code": "CAI", "name": "Cairo International Airport", "city_name": "Cairo", "country": "EG"},
    {"iata_code": "MAD", "name": "Adolfo Suarez Madrid-Barajas Airport", "city_name": "Madrid", "country": "ES"},
    {"iata_code": "BCN", "name": "Barcelona-El Prat Airport", "city_name": "Barcelona", "country": "ES"},
    {"iata_code": "FCO", "name": "Leonardo da Vinci Fiumicino Airport", "city_name": "Rome", "country": "IT"},
    {"iata_code": "MXP", "name": "Milan Malpensa Airport", "city_name": "Milan", "country": "IT"},
    {"iata_code": "VIE", "name": "Vienna International Airport", "city_name": "Vienna", "country": "AT"},
    {"iata_code": "ZRH", "name": "Zurich Airport", "city_name": "Zurich", "country": "CH"},
    {"iata_code": "GVA", "name": "Geneva Airport", "city_name": "Geneva", "country": "CH"},
    {"iata_code": "LAX", "name": "Los Angeles International Airport", "city_name": "Los Angeles", "country": "US"},
    {"iata_code": "ORD", "name": "O'Hare International Airport", "city_name": "Chicago", "country": "US"},
    {"iata_code": "MCO", "name": "Orlando International Airport", "city_name": "Orlando", "country": "US"},
    {"iata_code": "SFO", "name": "San Francisco International Airport", "city_name": "San Francisco", "country": "US"},
    {"iata_code": "MIA", "name": "Miami International Airport", "city_name": "Miami", "country": "US"},
    {"iata_code": "YYZ", "name": "Toronto Pearson International Airport", "city_name": "Toronto", "country": "CA"},
    {"iata_code": "HND", "name": "Tokyo Haneda Airport", "city_name": "Tokyo", "country": "JP"},
    {"iata_code": "NRT", "name": "Tokyo Narita Airport", "city_name": "Tokyo", "country": "JP"},
    {"iata_code": "SIN", "name": "Singapore Changi Airport", "city_name": "Singapore", "country": "SG"},
    {"iata_code": "BKK", "name": "Suvarnabhumi Airport", "city_name": "Bangkok", "country": "TH"},
    {"iata_code": "SYD", "name": "Sydney Kingsford Smith Airport", "city_name": "Sydney", "country": "AU"},
]


class AirportSuggestionsView(APIView):
    """
    GET /api/v1/flights/airports/suggestions/?q=...

    Returns airport & city suggestions matching a search query (full city name,
    airport name, or IATA code).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip().lower()
        if not query or len(query) < 2:
            return Response([])

        results = []
        seen_codes = set()

        # 1. Country suggestions first (e.g. Germany -> Germany (All Airports))
        country_matches = search_country_suggestions(query)
        for c in country_matches:
            results.append(c)
            seen_codes.add(c["iata_code"])

        # 2. If query matches a country directly (e.g. "Germany", "England"),
        # also include its major airports with full context
        country_obj = find_country(query)
        if country_obj:
            for apt in country_obj.get("airports", []):
                code = apt["iata_code"]
                if code not in seen_codes:
                    seen_codes.add(code)
                    results.append({
                        "iata_code": code,
                        "name": apt["name"],
                        "city_name": apt["city_name"],
                        "country": country_obj["name"],
                        "country_code": country_obj["country_code"],
                        "type": "airport",
                    })

        # 3. Try Duffel live places suggestions API
        try:
            duffel_sugg = async_to_sync(duffel_client.get_places_suggestions)(query)
            if duffel_sugg:
                for item in duffel_sugg:
                    code = item.get("iata_code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        results.append(item)
        except Exception as e:
            logger.warning("Duffel places suggestions failed: %s", e)

        # 4. Fallback to local POPULAR_AIRPORTS
        for a in POPULAR_AIRPORTS:
            code = a.get("iata_code")
            if code not in seen_codes:
                if (
                    query in a["city_name"].lower()
                    or query in a["name"].lower()
                    or query in code.lower()
                ):
                    seen_codes.add(code)
                    results.append(a)

        return Response(results)
