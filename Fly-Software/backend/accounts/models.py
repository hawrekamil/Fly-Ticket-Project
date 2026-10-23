"""
Accounts Models
===============
Custom User model with role-based access control (RBAC).

Roles:
    - customer: Regular end-user who searches and books flights.
    - agent: Ticketing desk staff who can confirm cash payments.
    - admin: Full system access including user management.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import CustomUserManager


class User(AbstractUser):
    """
    Extended User model with role-based access control.

    Extends Django's AbstractUser to add:
    - Role field for RBAC (customer, agent, admin)
    - Phone number for booking contact details
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        AGENT = "agent", "Ticketing Agent"
        ADMIN = "admin", "Administrator"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
        help_text="Determines the user's access level within the system.",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Contact phone number for booking notifications.",
    )

    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_agent(self):
        """Check if user has agent-level access (agent or admin)."""
        return self.role in (self.Role.AGENT, self.Role.ADMIN)

    @property
    def is_admin_role(self):
        """Check if user has administrator role."""
        return self.role == self.Role.ADMIN
