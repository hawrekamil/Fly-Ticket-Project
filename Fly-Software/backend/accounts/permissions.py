"""
Accounts Permissions
====================
Custom DRF permission classes for role-based access control.
"""

from rest_framework.permissions import BasePermission


class IsAgent(BasePermission):
    """
    Allow access only to users with agent or admin role.

    Used to guard staff-only endpoints like cash payment confirmation
    and the desk agent dashboard.
    """

    message = "Access restricted to ticketing agents and administrators."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("agent", "admin")
        )


class IsAdmin(BasePermission):
    """
    Allow access only to users with admin role.

    Used to guard system administration endpoints.
    """

    message = "Access restricted to administrators."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )
