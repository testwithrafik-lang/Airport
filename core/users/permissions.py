from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'ADMIN' or request.user.is_staff)

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and (request.user.role == 'ADMIN' or request.user.is_staff):
            return True
        
        if hasattr(obj, 'email'): 
            return obj == request.user
            
        return getattr(obj, 'passenger', None) == request.user