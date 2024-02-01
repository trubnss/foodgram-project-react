from rest_framework import permissions


class CustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ["me", "subscriptions", "subscribe", "set_password"]:
            return request.user and request.user.is_authenticated
        elif (
            request.method in permissions.SAFE_METHODS
            or view.action == "create"
        ):
            return True
        else:
            return False
