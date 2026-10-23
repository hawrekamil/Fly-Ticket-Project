"""
Accounts Auth Tests
===================
Tests for user registration, login, and RBAC permissions.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        username="customer1",
        email="customer@example.com",
        password="testpass123",
        role="customer",
    )


@pytest.fixture
def agent_user(db):
    return User.objects.create_user(
        username="agent1",
        email="agent@example.com",
        password="testpass123",
        role="agent",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin1",
        email="admin@example.com",
        password="testpass123",
    )


class TestUserModel:
    """Tests for the custom User model."""

    def test_create_customer(self, customer_user):
        assert customer_user.role == "customer"
        assert customer_user.is_agent is False
        assert customer_user.is_admin_role is False

    def test_create_agent(self, agent_user):
        assert agent_user.role == "agent"
        assert agent_user.is_agent is True
        assert agent_user.is_admin_role is False

    def test_create_admin(self, admin_user):
        assert admin_user.role == "admin"
        assert admin_user.is_agent is True
        assert admin_user.is_admin_role is True
        assert admin_user.is_staff is True
        assert admin_user.is_superuser is True

    def test_str_representation(self, customer_user):
        assert "customer1" in str(customer_user)
        assert "Customer" in str(customer_user)


@pytest.mark.django_db
class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, api_client):
        response = api_client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["user"]["role"] == "customer"
        assert User.objects.filter(username="newuser").exists()

    def test_register_password_mismatch(self, api_client):
        response = api_client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
                "password_confirm": "differentpass",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_register_duplicate_email(self, api_client, customer_user):
        response = api_client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "customer@example.com",
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    """Tests for user login endpoint."""

    def test_login_with_username(self, api_client, customer_user):
        response = api_client.post(
            reverse("accounts:login"),
            {"username": "customer1", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["user"]["username"] == "customer1"

    def test_login_with_email(self, api_client, customer_user):
        response = api_client.post(
            reverse("accounts:login"),
            {"username": "customer@example.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 200

    def test_login_invalid_credentials(self, api_client, customer_user):
        response = api_client.post(
            reverse("accounts:login"),
            {"username": "customer1", "password": "wrongpass"},
            format="json",
        )
        assert response.status_code == 400


class TestProfile:
    """Tests for user profile endpoint."""

    def test_profile_authenticated(self, api_client, customer_user):
        api_client.force_authenticate(user=customer_user)
        response = api_client.get(reverse("accounts:profile"))
        assert response.status_code == 200
        assert response.data["username"] == "customer1"

    def test_profile_unauthenticated(self, api_client):
        response = api_client.get(reverse("accounts:profile"))
        assert response.status_code == 403


class TestRBACPermissions:
    """Tests for role-based access control."""

    def test_customer_cannot_access_hold_orders(self, api_client, customer_user):
        api_client.force_authenticate(user=customer_user)
        response = api_client.get(reverse("payments:hold-orders"))
        assert response.status_code == 403

    def test_agent_can_access_hold_orders(self, api_client, agent_user):
        api_client.force_authenticate(user=agent_user)
        response = api_client.get(reverse("payments:hold-orders"))
        assert response.status_code == 200

    def test_admin_can_access_hold_orders(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(reverse("payments:hold-orders"))
        assert response.status_code == 200
