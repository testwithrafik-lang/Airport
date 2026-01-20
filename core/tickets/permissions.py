from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
   
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, "is_admin", False)
        )

class IsOwnerOrAdmin(BasePermission):
   
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_admin", False):
            return True

        return obj.passenger == request.user

class CanPayTicket(BasePermission):
   
    def has_object_permission(self, request, view, obj):
        return (
            obj.passenger == request.user and
            not obj.paid
        )
