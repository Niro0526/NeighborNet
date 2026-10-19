from rest_framework import permissions
from apps.accounts.models import RoleChoices

class IsCoordinator(permissions.BasePermission):
    """Allows access only to approved Coordinators or superusers."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_coordinator
        )

class IsFoodProvider(permissions.BasePermission):
    """Allows access only to users with approved FOOD_PROVIDER role."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_food_provider or request.user.is_coordinator)
        )

class IsRecipient(permissions.BasePermission):
    """Allows access only to users with approved RECIPIENT role."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_recipient or request.user.is_coordinator)
        )

class IsVolunteer(permissions.BasePermission):
    """Allows access only to users with approved VOLUNTEER role."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_volunteer or request.user.is_coordinator)
        )

class HasApprovedRole(permissions.BasePermission):
    """Allows access if user has at least one approved role."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (len(request.user.get_approved_roles()) > 0 or request.user.is_superuser)
        )
