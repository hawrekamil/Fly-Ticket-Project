# Backend Implementation

## Overview
The BookingSoft backend is a robust, production-grade RESTful API built with **Django** and **Django REST Framework (DRF)**. It is designed to interface with third-party providers (Duffel for flights, Stripe for payments) while maintaining strict local state machines for order lifecycle management.

## Architecture & Apps

### 1. Accounts App (`accounts`)
- **Custom User Model**: Extended Django's `AbstractUser` to support email-based authentication and role-based access control (RBAC).
- **Roles**:
  - `Customer`: Standard user, can search and book flights.
  - `Agent`: Can view pending cash holds and confirm payments in person.
  - `Admin`: Full system access.
- **Authentication**: JWT (JSON Web Tokens) via `djangorestframework-simplejwt` for secure, stateless API access.

### 2. Services Layer (`services`)
- **Duffel Client**: An asynchronous singleton wrapper (`duffel_client.py`) using `httpx` to interact with Duffel's REST API. Handles searching for flights, retrieving offers, and confirming bookings.
- **Stripe Client**: Manages payment intents and webhook signature verification for instant credit card processing.

### 3. Flights App (`flights`)
- **Models**:
  - `OfferRequest`: Tracks user search criteria (origin, destination, dates, passengers).
  - `OfferSnapshot`: Caches Duffel's volatile flight offers locally with expiration timestamps.
  - `Order`: The core booking model implementing a strict State Machine.
- **State Machine (`Order.Status`)**:
  - Enforces valid transitions via `ALLOWED_TRANSITIONS` (e.g., `PENDING_PAYMENT` -> `CONFIRMED`, `HOLD_PENDING_CASH` -> `CONFIRMED` or `EXPIRED`).
- **Background Tasks**: Integrates `django-q2` for asynchronous operations.
  - `expire_stale_hold_orders`: A cron job that transitions expired cash holds from `hold_pending_cash` to `expired`.
  - `send_order_confirmation_email`: Asynchronous email delivery using Django's console backend (for local dev).

### 4. Payments App (`payments`)
- **Models**: 
  - `Payment`: Records transaction details (Stripe ID, Duffel Payment ID, amounts, status).
- **Concurrency & Safety**:
  - The `ConfirmCashPaymentView` uses `select_for_update()` to apply row-level database locks. This prevents race conditions where an agent might try to confirm a cash payment at the exact moment a background task attempts to expire the hold.
- **Stripe Webhooks**: Listens for `payment_intent.succeeded` to automatically transition Orders to `CONFIRMED` and issue tickets via Duffel.

## Key Technical Decisions
- **Async to Sync**: Since Django's ORM is predominantly synchronous (and some DRF features don't fully support async yet), we utilized `asgiref.sync.async_to_sync` in the views to call the highly performant async Duffel client without blocking the event loop.
- **API Documentation**: Integrated `drf-spectacular` to automatically generate OpenAPI 3 schemas, accessible via Swagger UI at `/api/docs/`.
- **Testing**: A comprehensive test suite using `pytest-django`, fully mocking external API calls to Duffel and Stripe to ensure deterministic tests without network dependency.
