"""
Duffel API Client
=================
Async HTTP client for the Duffel REST API (v2).

Uses a singleton httpx.AsyncClient with connection pooling for
non-blocking I/O during airline inventory aggregations.

Usage:
    from services.duffel_client import duffel_client

    offers = await duffel_client.create_offer_request(
        slices=[{"origin": "LHR", "destination": "JFK", "departure_date": "2025-12-01"}],
        passengers=[{"type": "adult"}],
        cabin_class="economy",
    )
"""

import asyncio
import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class DuffelAPIError(Exception):
    """
    Raised when the Duffel API returns an error response.

    Attributes:
        status_code: HTTP status code from Duffel.
        errors: List of error objects from the Duffel response body.
        request_id: Duffel request ID for debugging.
    """

    def __init__(self, status_code: int, errors: list, request_id: str = ""):
        self.status_code = status_code
        self.errors = errors
        self.request_id = request_id
        # Build a human-readable message from the first error
        first_error = errors[0] if errors else {}
        message = first_error.get("message", f"Duffel API error (HTTP {status_code})")
        super().__init__(message)

    def __repr__(self):
        return (
            f"DuffelAPIError(status={self.status_code}, "
            f"request_id='{self.request_id}', errors={self.errors})"
        )


class DuffelClient:
    """
    Async Duffel REST API client.

    Maintains a persistent httpx.AsyncClient for connection pooling.
    All methods correspond to Duffel API v2 endpoints.
    """

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._client_loop: asyncio.AbstractEventLoop | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily initialize the httpx.AsyncClient bound to the current event loop."""
        current_loop = None
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if (
            self._client is None
            or self._client.is_closed
            or self._client_loop is not current_loop
        ):
            self._client_loop = current_loop
            self._client = httpx.AsyncClient(
                base_url=settings.DUFFEL_BASE_URL,
                headers={
                    "Authorization": f"Bearer {settings.DUFFEL_API_TOKEN}",
                    "Duffel-Version": settings.DUFFEL_VERSION,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10,
                ),
            )
        return self._client

    async def _request(
        self, method: str, path: str, json_data: dict | None = None
    ) -> dict:
        """
        Execute an HTTP request against the Duffel API.

        Handles error parsing and logging for all API calls.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path (e.g., '/air/offer_requests').
            json_data: Optional JSON body for POST/PATCH requests.

        Returns:
            Parsed JSON response body.

        Raises:
            DuffelAPIError: If the API returns a non-2xx status code.
        """
        client = self._get_client()

        logger.debug("Duffel %s %s", method, path)

        try:
            response = await client.request(method, path, json=json_data)
        except httpx.TimeoutException as e:
            logger.error("Duffel request timeout: %s %s — %s", method, path, e)
            raise DuffelAPIError(
                status_code=408,
                errors=[{"message": f"Request timed out: {e}", "type": "timeout"}],
            ) from e
        except httpx.HTTPError as e:
            logger.error("Duffel HTTP error: %s %s — %s", method, path, e)
            raise DuffelAPIError(
                status_code=0,
                errors=[{"message": f"HTTP error: {e}", "type": "connection_error"}],
            ) from e

        request_id = response.headers.get("x-request-id", "")

        if response.status_code >= 400:
            try:
                error_body = response.json()
                errors = error_body.get("errors", [])
            except Exception:
                errors = [{"message": response.text, "type": "unknown"}]

            logger.error(
                "Duffel API error: %s %s — HTTP %d — request_id=%s — %s",
                method, path, response.status_code, request_id, errors,
            )
            raise DuffelAPIError(
                status_code=response.status_code,
                errors=errors,
                request_id=request_id,
            )

        data = response.json()
        logger.debug(
            "Duffel %s %s — HTTP %d — request_id=%s",
            method, path, response.status_code, request_id,
        )
        return data

    # =========================================================================
    # Offer Requests — Flight Search
    # =========================================================================

    async def create_offer_request(
        self,
        slices: list[dict],
        passengers: list[dict],
        cabin_class: str = "economy",
        return_offers: bool = True,
    ) -> dict:
        """
        Search for flight offers.

        POST /air/offer_requests

        Args:
            slices: List of route slices, each with origin, destination,
                    and departure_date.
            passengers: List of passenger dicts with 'type' field
                        (adult, child, infant_without_seat).
            cabin_class: Cabin class (economy, premium_economy, business, first).
            return_offers: If True, returns offers inline (default for small searches).

        Returns:
            Full Duffel offer_request response including offers.
        """
        payload = {
            "data": {
                "slices": slices,
                "passengers": passengers,
                "cabin_class": cabin_class,
                "return_offers": return_offers,
            }
        }
        return await self._request("POST", "/air/offer_requests", json_data=payload)

    # =========================================================================
    # Offers — Fare Validation
    # =========================================================================

    async def get_offer(self, offer_id: str) -> dict:
        """
        Retrieve a single offer to validate pricing before checkout.

        GET /air/offers/{offer_id}

        Args:
            offer_id: Duffel offer ID (off_*).

        Returns:
            Full offer object with current pricing.
        """
        return await self._request("GET", f"/air/offers/{offer_id}")

    # =========================================================================
    # Orders — Booking
    # =========================================================================

    async def create_order(
        self,
        selected_offers: list[str],
        passengers: list[dict],
        order_type: str = "instant",
        payments: list[dict] | None = None,
    ) -> dict:
        """
        Create a flight booking order.

        POST /air/orders

        Supports two modes:
        - type='instant': Immediate ticketing with payment.
        - type='hold': Hold seat inventory without payment.

        Args:
            selected_offers: List of offer IDs to book.
            passengers: List of passenger details with name, DOB, contact info.
            order_type: 'instant' or 'hold'.
            payments: Payment details (required for instant, omitted for hold).

        Returns:
            Full Duffel order response.
        """
        payload: dict[str, Any] = {
            "data": {
                "type": order_type,
                "selected_offers": selected_offers,
                "passengers": passengers,
            }
        }

        # Only include payments for instant orders
        if order_type == "instant" and payments:
            payload["data"]["payments"] = payments

        return await self._request("POST", "/air/orders", json_data=payload)

    async def get_order(self, order_id: str) -> dict:
        """
        Retrieve a single order by ID.

        GET /air/orders/{order_id}

        Args:
            order_id: Duffel order ID (ord_*).

        Returns:
            Full order object.
        """
        return await self._request("GET", f"/air/orders/{order_id}")

    # =========================================================================
    # Payments — Paying for Held Orders
    # =========================================================================

    async def create_payment(
        self, order_id: str, amount: str, currency: str
    ) -> dict:
        """
        Pay for a previously held order before expiration.

        POST /air/payments

        Used in the cash-hold flow after an agent confirms cash receipt.

        Args:
            order_id: Duffel order ID (ord_*).
            amount: Payment amount as string (e.g., '450.00').
            currency: ISO 4217 currency code (e.g., 'EUR', 'USD').

        Returns:
            Payment confirmation response.
        """
        payload = {
            "data": {
                "order_id": order_id,
                "payment": {
                    "type": "balance",
                    "amount": amount,
                    "currency": currency,
                },
            }
        }
        return await self._request("POST", "/air/payments", json_data=payload)

    # =========================================================================
    # Places — Airport & City Autocomplete Suggestions
    # =========================================================================

    async def get_places_suggestions(self, query: str) -> list[dict]:
        """
        Search for places/airports by city name, airport name, or IATA code.

        GET /places/suggestions?query={query}

        Args:
            query: Search query (e.g. 'london', 'frankfurt', 'jfk').

        Returns:
            List of structured place objects with IATA codes and full names.
        """
        if not query or len(query.strip()) < 2:
            return []

        res = await self._request("GET", f"/places/suggestions?query={query.strip()}")
        data = res.get("data", [])
        results = []
        for item in data:
            iata = item.get("iata_code")
            if not iata:
                continue
            city_obj = item.get("city") or {}
            city_name = item.get("city_name") or city_obj.get("name") or item.get("name")
            name = item.get("name", "")
            country = item.get("iata_country_code", "")
            item_type = item.get("type", "airport")
            results.append({
                "iata_code": iata,
                "name": name,
                "city_name": city_name,
                "country": country,
                "type": item_type,
            })
        return results

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def close(self):
        """Close the underlying HTTP client and release connections."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("Duffel client connection pool closed.")


# Module-level singleton — import this in views and tasks
duffel_client = DuffelClient()
