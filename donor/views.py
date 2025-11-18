from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from auth_app.models import CustomUser
from auth_app.permissions import IsDonorOwner
from auth_app.exceptions import DonorProfileNotFoundException
from .models import DonorProfile
from .serializers import (
    DonorRegisterSerializer,
    DonorProfileSerializer,
    PublicDonorProfileSerializer
)


class DonorRegisterView(generics.CreateAPIView):
    """
    Donor registration endpoint.
    Creates a new donor user account and donor profile.
    """
    queryset = CustomUser.objects.all()
    serializer_class = DonorRegisterSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['1. Authentication & Registration'],
        operation_summary="Register as Donor",
        operation_description="""
        Register a new donor account.
        
        **Process:**
        1. Creates user account with email/password
        2. Auto-creates donor profile
        3. Account is inactive until email verification
        
        **After Registration:**
        - Login with credentials to get JWT tokens
        - Complete profile via `/api/v1.0/auth/donor/profile/`
        """,
        responses={
            201: openapi.Response(
                description="Donor registered successfully",
                schema=DonorRegisterSerializer
            ),
            400: "Validation error - check email uniqueness and password strength"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DonorProfileView(generics.RetrieveUpdateAPIView):
    """
    Donor profile management (own profile only).
    Authenticated donors can view and update their own profile.
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [IsAuthenticated, IsDonorOwner]
    
    @swagger_auto_schema(
        tags=['3. Donor Management (Private)'],
        operation_summary="Get Own Donor Profile",
        operation_description="""
        Retrieve the authenticated donor's own profile.
        
        **Access:**
        - Requires authentication
        - Donor can only access their own profile
        """,
        responses={
            200: DonorProfileSerializer,
            401: "Authentication required",
            403: "Not authorized - donors can only access their own profile",
            404: "Donor profile not found"
        }
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['3. Donor Management (Private)'],
        operation_summary="Update Own Donor Profile",
        operation_description="""
        Update the authenticated donor's own profile.
        
        **Editable Fields:**
        - photo, full_name, short_bio
        - country, website, birthday, workplace
        - is_profile_private
        """,
        request_body=DonorProfileSerializer,
        responses={
            200: DonorProfileSerializer,
            400: "Validation error",
            401: "Authentication required",
            403: "Not authorized"
        }
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update Own Donor Profile (Full)",
        tags=['3. Donor Management (Private)'],
        operation_description="""
        Full update of the authenticated donor's profile.
        
        **Editable Fields:**
        - photo, full_name, short_bio
        - country, website, birthday, workplace
        - is_profile_private
        """,
        request_body=DonorProfileSerializer,
        responses={
            200: DonorProfileSerializer,
            400: "Validation error",
            401: "Authentication required",
            403: "Not authorized"
        }
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def get_object(self):
        try:
            return DonorProfile.objects.get(user=self.request.user)
        except DonorProfile.DoesNotExist:
            raise DonorProfileNotFoundException()


class PublicDonorProfileView(generics.RetrieveAPIView):
    """
    Public donor profile view (respects privacy settings).
    """
    serializer_class = PublicDonorProfileSerializer
    permission_classes = [AllowAny]
    queryset = DonorProfile.objects.filter(is_profile_private=False)
    lookup_field = 'id'
    
    @swagger_auto_schema(
        tags=['4. Donor Management (Public)'],
        operation_summary="View Public Donor Profile",
        operation_description="""
        View a donor's public profile (if not private).
        
        **Privacy:**
        - Only shows profiles where is_profile_private=False
        - Returns 404 if profile is private
        """,
        responses={
            200: PublicDonorProfileSerializer,
            404: "Donor not found or profile is private"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DonorProfileListView(generics.ListAPIView):
    """
    List all public donor profiles.
    """
    serializer_class = PublicDonorProfileSerializer
    permission_classes = [AllowAny]
    queryset = DonorProfile.objects.filter(is_profile_private=False)
    
    @swagger_auto_schema(
        tags=['4. Donor Management (Public)'],
        operation_summary="List Public Donor Profiles",
        operation_description="""
        Browse all public donor profiles.
        
        **Filtering:**
        - Only shows profiles where is_profile_private=False
        - Ordered by creation date (newest first)
        """,
        responses={
            200: openapi.Response(
                description="List of public donor profiles",
                schema=PublicDonorProfileSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
