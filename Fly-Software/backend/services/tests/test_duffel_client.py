"""
Duffel Client Tests
===================
Tests for the async Duffel API client using respx to mock HTTP calls.
"""

import pytest
import respx
import httpx

from services.duffel_client import DuffelClient, DuffelAPIError


@pytest.fixture
def client():
    """Create a fresh DuffelClient for each test."""
    c = DuffelClient()
    yield c
    # Cleanup is handled by test teardown


@pytest.mark.asyncio
class TestDuffelClient:
    """Tests for DuffelClient methods."""

    @respx.mock
    async def test_create_offer_request_success(self, client, settings):
        """Test successful flight search."""
        settings.DUFFEL_API_TOKEN = "duffel_test_token"
        settings.DUFFEL_BASE_URL = "https://api.duffel.com"
        settings.DUFFEL_VERSION = "v2"

        mock_response = {
            "data": {
                "id": "orq_0000test",
                "offers": [
                    {
                        "id": "off_0000test",
                        "total_amount": "350.00",
                        "total_currency": "EUR",
                        "owner": {"name": "Duffel Airways", "iata_code": "ZZ"},
                        "slices": [],
                        "passengers": [{"id": "pas_0000test", "type": "adult"}],
                        "expires_at": "2025-12-01T12:00:00Z",
                        "payment_requirements": {"requires_instant_payment": False},
                    }
                ],
            }
        }

        respx.post("https://api.duffel.com/air/offer_requests").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await client.create_offer_request(
            slices=[{"origin": "LHR", "destination": "JFK", "departure_date": "2025-12-01"}],
            passengers=[{"type": "adult"}],
            cabin_class="economy",
        )

        assert result["data"]["id"] == "orq_0000test"
        assert len(result["data"]["offers"]) == 1
        assert result["data"]["offers"][0]["total_amount"] == "350.00"

    @respx.mock
    async def test_create_offer_request_api_error(self, client, settings):
        """Test error handling when Duffel returns an error."""
        settings.DUFFEL_API_TOKEN = "duffel_test_token"
        settings.DUFFEL_BASE_URL = "https://api.duffel.com"
        settings.DUFFEL_VERSION = "v2"

        error_response = {
            "errors": [
                {
                    "type": "invalid_request_error",
                    "message": "Origin not found",
                    "code": "not_found",
                }
            ]
        }

        respx.post("https://api.duffel.com/air/offer_requests").mock(
            return_value=httpx.Response(422, json=error_response)
        )

        with pytest.raises(DuffelAPIError) as exc_info:
            await client.create_offer_request(
                slices=[{"origin": "XXX", "destination": "JFK", "departure_date": "2025-12-01"}],
                passengers=[{"type": "adult"}],
            )

        assert exc_info.value.status_code == 422
        assert "Origin not found" in str(exc_info.value)

    @respx.mock
    async def test_get_offer_success(self, client, settings):
        """Test retrieving a single offer."""
        settings.DUFFEL_API_TOKEN = "duffel_test_token"
        settings.DUFFEL_BASE_URL = "https://api.duffel.com"
        settings.DUFFEL_VERSION = "v2"

        mock_response = {
            "data": {
                "id": "off_0000test",
                "total_amount": "350.00",
                "total_currency": "EUR",
            }
        }

        respx.get("https://api.duffel.com/air/offers/off_0000test").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await client.get_offer("off_0000test")
        assert result["data"]["total_amount"] == "350.00"

    @respx.mock
    async def test_create_hold_order(self, client, settings):
        """Test creating a hold order (no payment)."""
        settings.DUFFEL_API_TOKEN = "duffel_test_token"
        settings.DUFFEL_BASE_URL = "https://api.duffel.com"
        settings.DUFFEL_VERSION = "v2"

        mock_response = {
            "data": {
                "id": "ord_0000test",
                "payment_required_by": "2025-12-02T12:00:00Z",
            }
        }

        route = respx.post("https://api.duffel.com/air/orders").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await client.create_order(
            selected_offers=["off_0000test"],
            passengers=[
                {
                    "id": "pas_0000test",
                    "given_name": "John",
                    "family_name": "Doe",
                    "born_on": "1990-01-01",
                    "gender": "m",
                    "title": "mr",
                    "email": "john@example.com",
                    "phone_number": "+1234567890",
                    "type": "adult",
                }
            ],
            order_type="hold",
        )

        assert result["data"]["id"] == "ord_0000test"

        # Verify the request body has type=hold and no payments
        request_body = route.calls[0].request.content
        import json
        body = json.loads(request_body)
        assert body["data"]["type"] == "hold"
        assert "payments" not in body["data"]

    @respx.mock
    async def test_create_payment_for_hold(self, client, settings):
        """Test paying for a held order."""
        settings.DUFFEL_API_TOKEN = "duffel_test_token"
        settings.DUFFEL_BASE_URL = "https://api.duffel.com"
        settings.DUFFEL_VERSION = "v2"

        mock_response = {
            "data": {
                "id": "pay_0000test",
                "amount": "350.00",
                "currency": "EUR",
            }
        }

        respx.post("https://api.duffel.com/air/payments").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await client.create_payment(
            order_id="ord_0000test",
            amount="350.00",
            currency="EUR",
        )

        assert result["data"]["id"] == "pay_0000test"

    @respx.mock
    async def test_request_headers_include_auth_and_version(self, client, settings):
        """Verify correct Authorization and Duffel-Version headers."""
        settings.DUFFEL_API_TOKEN = "duffel_test_my_token"
        settings.DUFFEL_BASE_URL = "https://api.duffel.com"
        settings.DUFFEL_VERSION = "v2"

        # Force a new client to pick up the test token
        client._client = None

        route = respx.get("https://api.duffel.com/air/orders/ord_test").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        await client.get_order("ord_test")

        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer duffel_test_my_token"
        assert request.headers["duffel-version"] == "v2"
        assert request.headers["content-type"] == "application/json"
