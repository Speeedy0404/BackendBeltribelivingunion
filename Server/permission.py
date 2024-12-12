from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.methon in permissions.SAFE_METHODS:
            return True
        return bool(request.user in request.user.is_superuser)
