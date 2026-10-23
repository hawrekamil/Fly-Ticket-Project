"""
Accounts Admin
==============
Django admin configuration for the custom User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model with role field."""

    list_display = ("username", "email", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    # Add role and phone_number to the admin form
    fieldsets = BaseUserAdmin.fieldsets + (
        ("BookingSoft Profile", {
            "fields": ("role", "phone_number"),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("BookingSoft Profile", {
            "fields": ("email", "role", "phone_number"),
        }),
    )
