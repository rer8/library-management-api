from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Allow read access to any user; write access only to admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    """Allow object-level access only to the owner or admin."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return obj.user == request.user
