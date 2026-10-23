"""
Flights Serializers
===================
DRF serializers for flight search, offer display, and booking.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from flights.models import OfferRequest, OfferSnapshot, Order, Passenger


class FlightSearchSerializer(serializers.Serializer):
    """
    Validates flight search input parameters.

    Used by the search view to build a Duffel offer request.
    """

    origin = serializers.CharField(
        max_length=50,
        min_length=2,
        help_text="Origin IATA airport code, city name, or country code (e.g., LHR, FRA, Germany, COUNTRY:DE).",
    )
    destination = serializers.CharField(
        max_length=50,
        min_length=2,
        help_text="Destination IATA airport code, city name, or country code (e.g., JFK, LON, England, COUNTRY:GB).",
    )
    departure_date = serializers.DateField(
        help_text="Departure date (YYYY-MM-DD).",
    )
    return_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Return date for round trips (YYYY-MM-DD).",
    )
    cabin_class = serializers.ChoiceField(
        choices=OfferRequest.CabinClass.choices,
        default="economy",
    )
    adult_count = serializers.IntegerField(min_value=1, max_value=9, default=1)
    child_count = serializers.IntegerField(min_value=0, max_value=9, default=0)
    infant_count = serializers.IntegerField(min_value=0, max_value=9, default=0)

    def validate_origin(self, value):
        return value.strip()

    def validate_destination(self, value):
        return value.strip()

    def validate(self, attrs):
        if attrs["departure_date"] < timezone.now().date():
            raise serializers.ValidationError(
                {"departure_date": "Departure date cannot be in the past."}
            )
        if attrs["origin"] == attrs["destination"]:
            raise serializers.ValidationError(
                {"destination": "Destination must differ from origin."}
            )
        if attrs.get("return_date") and attrs["return_date"] <= attrs["departure_date"]:
            raise serializers.ValidationError(
                {"return_date": "Return date must be after departure date."}
            )
        # Ensure total passengers <= 9 (standard airline limit)
        total = attrs["adult_count"] + attrs["child_count"] + attrs["infant_count"]
        if total > 9:
            raise serializers.ValidationError("Maximum 9 passengers per booking.")
        if attrs["infant_count"] > attrs["adult_count"]:
            raise serializers.ValidationError(
                "Number of infants cannot exceed number of adults."
            )
        return attrs


class OfferSnapshotSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying flight offers to the user."""

    is_expired = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    stops_description = serializers.SerializerMethodField()
    segments_details = serializers.SerializerMethodField()
    departure_time = serializers.SerializerMethodField()
    arrival_time = serializers.SerializerMethodField()
    baggage_allowance = serializers.SerializerMethodField()
    amenities_details = serializers.SerializerMethodField()
    fare_rules = serializers.SerializerMethodField()
    emissions_kg = serializers.SerializerMethodField()

    class Meta:
        model = OfferSnapshot
        fields = [
            "id",
            "duffel_offer_id",
            "airline_name",
            "airline_iata",
            "total_amount",
            "total_currency",
            "stops",
            "stops_description",
            "departure_time",
            "arrival_time",
            "duration_minutes",
            "cabin_class",
            "expires_at",
            "is_expired",
            "requires_instant_payment",
            "segments_details",
            "baggage_allowance",
            "amenities_details",
            "fare_rules",
            "emissions_kg",
            "raw_offer",
        ]
        read_only_fields = fields

    def get_departure_time(self, obj) -> str:
        """Return the local airport departure time string directly from first segment."""
        raw = obj.raw_offer or {}
        slices = raw.get("slices", [])
        if slices and slices[0].get("segments"):
            return slices[0]["segments"][0].get("departing_at") or ""
        return obj.departure_time.strftime("%Y-%m-%dT%H:%M:%S") if obj.departure_time else ""

    def get_arrival_time(self, obj) -> str:
        """Return the local airport arrival time string directly from last segment of first slice."""
        raw = obj.raw_offer or {}
        slices = raw.get("slices", [])
        if slices and slices[0].get("segments"):
            return slices[0]["segments"][-1].get("arriving_at") or ""
        return obj.arrival_time.strftime("%Y-%m-%dT%H:%M:%S") if obj.arrival_time else ""

    def get_duration_minutes(self, obj) -> int | None:
        """Convert duration to total minutes for frontend display."""
        if obj.duration:
            return int(obj.duration.total_seconds() / 60)
        return None

    def _format_iso_duration(self, raw_dur: str) -> str:
        """Format an ISO 8601 duration string like 'PT1H51M' to '1h 51m'."""
        if not raw_dur:
            return ""
        if isinstance(raw_dur, str) and raw_dur.startswith("PT"):
            import re
            h_m = re.search(r"(\d+)H", raw_dur)
            m_m = re.search(r"(\d+)M", raw_dur)
            parts = []
            if h_m:
                parts.append(f"{h_m.group(1)}h")
            if m_m:
                parts.append(f"{m_m.group(1)}m")
            return " ".join(parts) if parts else raw_dur
        return str(raw_dur)

    def get_stops_description(self, obj) -> str:
        """Return clear human-readable stops description with city names (e.g. Stop in Istanbul)."""
        if obj.stops == 0:
            return "Direct (Non-stop)"

        raw = obj.raw_offer or {}
        slices = raw.get("slices", [])
        stop_cities = []
        for sl in slices:
            segs = sl.get("segments", [])
            for seg in segs[:-1]:
                dest = seg.get("destination", {})
                city = dest.get("city_name") or dest.get("name") or dest.get("iata_code")
                iata = dest.get("iata_code", "")
                stop_cities.append(f"{city} ({iata})" if iata else str(city))

        if not stop_cities:
            return f"{obj.stops} stop{'s' if obj.stops > 1 else ''}"

        return f"{obj.stops} stop{'s' if obj.stops > 1 else ''} in " + ", ".join(stop_cities)

    def get_segments_details(self, obj) -> list[dict]:
        """Return detailed segment and layover information for expand views."""
        raw = obj.raw_offer or {}
        slices = raw.get("slices", [])
        parsed_slices = []

        for sl_idx, sl in enumerate(slices):
            segs = sl.get("segments", [])
            parsed_segs = []
            for idx, seg in enumerate(segs):
                orig = seg.get("origin", {})
                dest = seg.get("destination", {})
                m_carrier = seg.get("marketing_carrier", {}) or {}
                o_carrier = seg.get("operating_carrier", {}) or {}
                aircraft = seg.get("aircraft", {}) or {}

                # Compute layover if there is a subsequent segment
                layover_str = None
                if idx < len(segs) - 1:
                    try:
                        t1 = parse_datetime(seg.get("arriving_at"))
                        t2 = parse_datetime(segs[idx + 1].get("departing_at"))
                        if t1 and t2:
                            diff = int((t2 - t1).total_seconds() / 60)
                            h, m = divmod(diff, 60)
                            layover_city = dest.get("city_name") or dest.get("name") or dest.get("iata_code")
                            layover_str = f"{h}h {m}m layover in {layover_city}"
                    except Exception:
                        layover_str = None

                # Baggage details
                baggages = (seg.get("passengers") or [{}])[0].get("baggages", [])
                baggage_texts = []
                for b in baggages:
                    qty = b.get("quantity", 0)
                    b_type = b.get("type", "").replace("_", " ")
                    if qty > 0:
                        baggage_texts.append(f"{qty} {b_type}")

                flight_no = (
                    f"{m_carrier.get('iata_code', '')} {seg.get('marketing_carrier_flight_number', '')}".strip()
                    or seg.get("operating_carrier_flight_number", "")
                )

                parsed_segs.append({
                    "origin_name": orig.get("name", ""),
                    "origin_iata": orig.get("iata_code", ""),
                    "origin_city": orig.get("city_name", ""),
                    "origin_country": orig.get("iata_country_code", ""),
                    "origin_terminal": seg.get("origin_terminal"),
                    "destination_name": dest.get("name", ""),
                    "destination_iata": dest.get("iata_code", ""),
                    "destination_city": dest.get("city_name", ""),
                    "destination_country": dest.get("iata_country_code", ""),
                    "destination_terminal": seg.get("destination_terminal"),
                    "departing_at": seg.get("departing_at", ""),
                    "arriving_at": seg.get("arriving_at", ""),
                    "duration": self._format_iso_duration(seg.get("duration", "")),
                    "airline_name": m_carrier.get("name") or o_carrier.get("name") or obj.airline_name,
                    "airline_logo": m_carrier.get("logo_symbol_url") or o_carrier.get("logo_symbol_url"),
                    "flight_number": flight_no,
                    "aircraft": aircraft.get("name"),
                    "layover_after": layover_str,
                    "baggage_summary": ", ".join(baggage_texts) if baggage_texts else "Standard fare rules",
                })

            parsed_slices.append({
                "slice_index": sl_idx,
                "segments": parsed_segs,
            })

        return parsed_slices

    def get_baggage_allowance(self, obj) -> dict:
        """
        Extract detailed baggage allowance including kilograms, carry-on,
        and personal item specs.
        """
        raw = obj.raw_offer or {}
        slices = raw.get("slices", [])
        first_slice = slices[0] if slices else {}
        segments = first_slice.get("segments", [])
        first_seg = segments[0] if segments else {}
        passengers = first_seg.get("passengers", [{}])
        p0 = passengers[0] if passengers else {}
        baggages = p0.get("baggages", [])

        checked_qty = 0
        carry_on_qty = 0
        for b in baggages:
            b_type = b.get("type", "")
            qty = b.get("quantity", 0)
            if b_type == "checked":
                checked_qty += qty
            elif b_type == "carry_on":
                carry_on_qty += qty

        is_premium = (obj.cabin_class or "").lower() in ["business", "first", "premium_economy"]
        checked_weight = "32 kg (70 lbs)" if is_premium else "23 kg (50 lbs)"

        return {
            "checked_qty": checked_qty,
            "checked_weight": checked_weight,
            "checked_included": checked_qty > 0,
            "checked_text": f"{checked_qty}x Checked Bag (up to {checked_weight} each) included" if checked_qty > 0 else "No checked bag included (cabin baggage only)",
            "carry_on_qty": max(carry_on_qty, 1),
            "carry_on_weight": "8 kg (17.6 lbs)",
            "carry_on_dimensions": "55 x 40 x 23 cm",
            "carry_on_text": "1x Cabin Bag (up to 8 kg, max 55x40x23cm)",
            "personal_item_included": True,
            "personal_item_text": "1x Personal Item (laptop / handbag up to 4 kg)",
            "badge_summary": f"{checked_qty}x 23kg Bag" if checked_qty > 0 else "Cabin Bag (8kg)",
            "short_summary": f"{checked_qty}x 23kg Checked · 1x 8kg Cabin" if checked_qty > 0 else "1x 8kg Cabin Baggage (0 checked bags)",
        }

    def get_amenities_details(self, obj) -> dict:
        """
        Extract in-flight services: Wi-Fi, power outlets, seat pitch,
        meals/dining, and entertainment.
        """
        raw = obj.raw_offer or {}
        slices = raw.get("slices", [])
        first_slice = slices[0] if slices else {}
        segments = first_slice.get("segments", [])
        first_seg = segments[0] if segments else {}
        passengers = first_seg.get("passengers", [{}])
        p0 = passengers[0] if passengers else {}
        cabin = p0.get("cabin", {}) or {}
        amenities = cabin.get("amenities", {}) or {}

        wifi = amenities.get("wifi", {}) or {}
        power = amenities.get("power", {}) or {}
        seat = amenities.get("seat", {}) or {}

        # Wi-Fi status
        wifi_avail = wifi.get("available", False)
        wifi_cost = wifi.get("cost", "paid")
        if wifi_avail:
            wifi_text = "Free High-Speed Wi-Fi" if wifi_cost == "free" else "In-flight Wi-Fi (Paid)"
        else:
            wifi_text = "Wi-Fi on selected aircraft"

        # Power outlets
        power_avail = power.get("available", True)
        power_text = "In-seat USB & AC Power Outlets" if power_avail else "USB charging available"

        # Seat comfort & pitch
        pitch = seat.get("pitch")
        legroom = seat.get("legroom")
        if pitch:
            seat_text = f'{pitch}" Seat Pitch'
            if legroom and legroom != "n/a":
                seat_text += f" ({legroom.capitalize()} Legroom)"
        elif (obj.cabin_class or "").lower() == "business":
            seat_text = "Lie-flat Bed / Recliner (180°)"
        elif (obj.cabin_class or "").lower() == "premium_economy":
            seat_text = '38" Pitch (Extra Legroom Recliner)'
        else:
            seat_text = '30"-32" Pitch (Standard Reclining Seat)'

        # Meals & Catering based on class & duration
        dur_mins = self.get_duration_minutes(obj) or 120
        c_class = (obj.cabin_class or "").lower()
        if c_class in ["business", "first"]:
            meal_text = "Complimentary Multi-course Gourmet Dining & Premium Beverages"
        elif c_class == "premium_economy":
            meal_text = "Complimentary Hot Meal Service, Snacks & Drinks"
        elif dur_mins >= 240:
            meal_text = "Complimentary Hot Meals, Snacks & Beverages"
        else:
            meal_text = "Complimentary In-flight Beverages & Refreshment Snacks"

        # In-flight entertainment
        entertainment_text = "Seatback HD Touchscreen & In-flight Entertainment" if dur_mins >= 180 else "In-flight Streaming to Personal Devices"

        return {
            "wifi_available": wifi_avail,
            "wifi_text": wifi_text,
            "power_available": power_avail,
            "power_text": power_text,
            "seat_pitch": pitch,
            "seat_text": seat_text,
            "meal_text": meal_text,
            "entertainment_text": entertainment_text,
            "cabin_marketing_name": p0.get("cabin_class_marketing_name") or cabin.get("marketing_name") or obj.cabin_class,
        }

    def get_fare_rules(self, obj) -> dict:
        """Extract ticket change, refund, and flexibility conditions."""
        raw = obj.raw_offer or {}
        slices = raw.get("slices", [])
        first_slice = slices[0] if slices else {}
        slice_conds = first_slice.get("conditions", {}) or {}
        offer_conds = raw.get("conditions", {}) or {}

        # Change rules
        change_info = offer_conds.get("change_before_departure") or slice_conds.get("change_before_departure") or {}
        change_allowed = change_info.get("allowed", False)
        penalty_amt = change_info.get("penalty_amount")
        penalty_curr = change_info.get("penalty_currency") or obj.total_currency
        if change_allowed:
            if penalty_amt and float(penalty_amt) > 0:
                change_text = f"Changes allowed ({penalty_curr} {penalty_amt} fee)"
            else:
                change_text = "Free flight changes (no penalty fee)"
        else:
            change_text = "Non-changeable ticket"

        # Refund rules
        refund_info = offer_conds.get("refund_before_departure") or slice_conds.get("refund_before_departure") or {}
        refund_allowed = refund_info.get("allowed", False)
        r_penalty_amt = refund_info.get("penalty_amount")
        r_penalty_curr = refund_info.get("penalty_currency") or obj.total_currency
        if refund_allowed:
            if r_penalty_amt and float(r_penalty_amt) > 0:
                refund_text = f"Refundable ({r_penalty_curr} {r_penalty_amt} fee)"
            else:
                refund_text = "Fully refundable"
        else:
            refund_text = "Non-refundable ticket"

        seat_selection = slice_conds.get("advance_seat_selection")
        seat_text = "Advance Seat Selection available" if seat_selection else "Standard Seat Assignment at Check-in"

        return {
            "change_allowed": change_allowed,
            "change_text": change_text,
            "refund_allowed": refund_allowed,
            "refund_text": refund_text,
            "seat_selection_text": seat_text,
        }

    def get_emissions_kg(self, obj) -> int | None:
        """Extract carbon footprint emissions in kg CO2."""
        raw = obj.raw_offer or {}
        em = raw.get("total_emissions_kg")
        try:
            return int(em) if em is not None else None
        except (ValueError, TypeError):
            return None


class PassengerInputSerializer(serializers.Serializer):
    """
    Validates passenger details submitted during booking.

    These details are sent to Duffel when creating an order.
    """

    given_name = serializers.CharField(max_length=100)
    family_name = serializers.CharField(max_length=100)
    born_on = serializers.DateField(help_text="YYYY-MM-DD")
    gender = serializers.ChoiceField(choices=Passenger.Gender.choices)
    title = serializers.ChoiceField(choices=Passenger.Title.choices)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    passenger_type = serializers.ChoiceField(
        choices=Passenger.PassengerType.choices,
        default="adult",
    )
    # Duffel passenger ID from the original offer request
    duffel_passenger_id = serializers.CharField(
        max_length=100,
        required=False,
        default="",
    )


class CreateOrderSerializer(serializers.Serializer):
    """
    Validates a flight booking request.

    The payment_method field determines the checkout flow:
    - 'stripe': Instant payment via Stripe PaymentIntent.
    - 'cash': Hold order for cash payment at desk.
    """

    offer_id = serializers.UUIDField(
        help_text="ID of the OfferSnapshot to book.",
    )
    passengers = PassengerInputSerializer(many=True, min_length=1)
    payment_method = serializers.ChoiceField(
        choices=[("stripe", "Credit Card (Stripe)"), ("cash", "Cash at Desk")],
        help_text="Payment method determines instant vs hold flow.",
    )

    def validate_offer_id(self, value):
        """Ensure the offer exists and hasn't expired."""
        try:
            offer = OfferSnapshot.objects.get(id=value)
        except OfferSnapshot.DoesNotExist:
            raise serializers.ValidationError("Offer not found.")
        if offer.is_expired:
            raise serializers.ValidationError(
                "This offer has expired. Please search for new flights."
            )
        # If cash payment is requested but the offer requires instant payment
        return value

    def validate(self, attrs):
        """Cross-field validation between offer and payment method."""
        offer = OfferSnapshot.objects.get(id=attrs["offer_id"])
        if attrs["payment_method"] == "cash" and offer.requires_instant_payment:
            raise serializers.ValidationError(
                {
                    "payment_method": (
                        "This offer requires instant payment and cannot be held "
                        "for cash. Please use credit card payment."
                    )
                }
            )
        attrs["offer"] = offer
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying order details."""

    passengers = serializers.SerializerMethodField()
    hold_time_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "booking_reference",
            "duffel_order_id",
            "status",
            "order_type",
            "total_amount",
            "total_currency",
            "hold_expires_at",
            "hold_time_remaining_seconds",
            "confirmed_at",
            "expired_at",
            "cancelled_at",
            "created_at",
            "updated_at",
            "passengers",
        ]
        read_only_fields = fields

    def get_passengers(self, obj):
        """Serialize passengers inline with the order."""
        passengers = obj.passengers.all()
        return [
            {
                "given_name": p.given_name,
                "family_name": p.family_name,
                "passenger_type": p.passenger_type,
                "email": p.email,
            }
            for p in passengers
        ]

    def get_hold_time_remaining_seconds(self, obj) -> int | None:
        """Remaining hold time in seconds, for countdown timers."""
        remaining = obj.hold_time_remaining
        if remaining is not None:
            return int(remaining.total_seconds())
        return None
