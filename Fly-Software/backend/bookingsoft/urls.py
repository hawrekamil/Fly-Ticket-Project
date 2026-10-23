"""
BookingSoft — URL Configuration
================================
Root URL routing. All API endpoints are mounted under /api/v1/.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

def api_root_view(request):
    return JsonResponse({
        "status": "online",
        "service": "BookingSoft REST API v1",
        "endpoints": {
            "accounts": "/api/v1/accounts/",
            "flights": "/api/v1/flights/",
            "payments": "/api/v1/payments/",
            "docs": "/api/docs/",
            "schema": "/api/schema/"
        }
    })

urlpatterns = [
    # Root status endpoint
    path("", api_root_view, name="root"),
    path("api/v1/", api_root_view, name="api-v1-root"),

    # Django admin
    path("admin/", admin.site.urls),
    
    # API v1
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/flights/", include("flights.urls")),
    path("api/v1/payments/", include("payments.urls")),

    # API Documentation (OpenAPI)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # DRF browsable API auth (login/logout in browser)
    path("api-auth/", include("rest_framework.urls")),
]
