"""
BookingSoft — Django Settings
=============================
Duffel-powered flight & hotel booking engine.
"""

import os
from pathlib import Path

from decouple import config, Csv

# =============================================================================
# Core Settings
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key-change-me-in-production")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,0.0.0.0,backend,frontend", cast=Csv())

ROOT_URLCONF = "bookingsoft.urls"

WSGI_APPLICATION = "bookingsoft.wsgi.application"

ASGI_APPLICATION = "bookingsoft.asgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Application Definition
# =============================================================================

INSTALLED_APPS = [
    # Django built-in
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "django_q",
    # Local apps
    "accounts.apps.AccountsConfig",
    "flights.apps.FlightsConfig",
    "payments.apps.PaymentsConfig",
    "hotels.apps.HotelsConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =============================================================================
# Custom User Model
# =============================================================================

AUTH_USER_MODEL = "accounts.User"

# =============================================================================
# Database
# =============================================================================
# SQLite for local development. Switch to PostgreSQL for production by
# uncommenting the PostgreSQL block and commenting out the SQLite block.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# PostgreSQL (production):
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": config("DB_NAME", default="bookingsoft"),
#         "USER": config("DB_USER", default="bookingsoft"),
#         "PASSWORD": config("DB_PASSWORD", default=""),
#         "HOST": config("DB_HOST", default="localhost"),
#         "PORT": config("DB_PORT", default="5432"),
#     }
# }

# =============================================================================
# Authentication & Password Validation
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# Internationalization
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# Static Files
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# Django REST Framework
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# =============================================================================
# DRF Spectacular (OpenAPI / Swagger)
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "BookingSoft API",
    "DESCRIPTION": "Duffel-powered flight & hotel booking engine API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# =============================================================================
# CORS & CSRF
# =============================================================================

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:80,http://localhost",
    cast=Csv(),
)
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=DEBUG, cast=bool)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost",
    cast=Csv(),
)

# =============================================================================
# Django-Q2 Task Queue
# =============================================================================

Q_CLUSTER = {
    "name": "bookingsoft",
    "workers": 2,
    "recycle": 500,
    "timeout": 120,
    "retry": 180,
    "orm": "default",  # Use PostgreSQL/SQLite as the broker via ORM
    "save_limit": 250,
    "queue_limit": 500,
    "bulk": 10,
    "catch_up": False,  # Don't run missed schedules on startup
}

# =============================================================================
# Duffel API Configuration
# =============================================================================

DUFFEL_API_TOKEN = config("DUFFEL_API_TOKEN", default="")
DUFFEL_BASE_URL = config("DUFFEL_BASE_URL", default="https://api.duffel.com")
DUFFEL_VERSION = config("DUFFEL_VERSION", default="v2")

# =============================================================================
# Stripe Configuration
# =============================================================================

STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")

# =============================================================================
# BookingSoft Business Configuration
# =============================================================================

# Supported currencies for booking display and processing
SUPPORTED_CURRENCIES = ["EUR", "USD"]

# Default currency for display when airline currency isn't in SUPPORTED_CURRENCIES
DEFAULT_CURRENCY = "EUR"

# Hold order expiry notification lead time (in hours)
HOLD_EXPIRY_NOTIFICATION_HOURS = 4

# =============================================================================
# Email Configuration
# =============================================================================

# Console backend for development — prints emails to stdout
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "bookings@bookingsoft.com"

# =============================================================================
# Logging
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "services.duffel_client": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "flights": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "payments": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
