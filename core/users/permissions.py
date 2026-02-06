from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            getattr(request.user, 'role', None) == 'ADMIN' or request.user.is_staff
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and (
            getattr(request.user, 'role', None) == 'ADMIN' or request.user.is_staff
        ):
            return True
        return obj == request.user