from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class AuthorAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return (
            user.is_authenticated and (
                obj.author == user or user.is_staff
            )
        )
