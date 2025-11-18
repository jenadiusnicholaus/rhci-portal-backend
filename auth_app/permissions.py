from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'ADMIN' and
            request.user.is_staff
        )


class IsPatientOwner(BasePermission):
    """
    Custom permission to only allow patient to access their own profile.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsDonorOwner(BasePermission):
    """
    Custom permission to only allow donor to access their own profile.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
