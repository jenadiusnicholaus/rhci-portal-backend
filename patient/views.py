from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from auth_app.models import CustomUser
from auth_app.permissions import IsPatientOwner
from auth_app.exceptions import PatientProfileNotFoundException
from .models import PatientProfile
from .serializers import PatientRegisterSerializer, PatientProfileSerializer


class PatientRegisterView(generics.CreateAPIView):
    """
    Patient registration endpoint.
    Creates a new patient user account and patient profile.
    """
    queryset = CustomUser.objects.all()
    serializer_class = PatientRegisterSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['1. Authentication & Registration'],
        operation_summary="Register as Patient",
        operation_description="""
        Register a new patient account with profile information.
        
        **Process:**
        1. Creates user account with email/password
        2. Creates associated patient profile
        3. Profile requires admin verification before becoming public
        
        **After Registration:**
        - Account is inactive until email verification
        - Profile is not publicly visible until admin approval
        - Patient can login and manage their own profile
        """,
        responses={
            201: openapi.Response(
                description="Patient registered successfully",
                schema=PatientRegisterSerializer
            ),
            400: "Validation error - check email uniqueness and required fields"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PatientProfileView(generics.RetrieveUpdateAPIView):
    """
    Patient profile management (own profile only).
    Authenticated patients can view and update their own profile.
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated, IsPatientOwner]
    
    @swagger_auto_schema(
        tags=['5. Patient Management (Private)'],
        operation_summary="Get Own Patient Profile",
        operation_description="""
        Retrieve the authenticated patient's own profile.
        
        **Access:**
        - Requires authentication
        - Patient can only access their own profile
        
        **Returns:**
        - Complete patient profile with funding details
        - Timeline events
        - Cost breakdown
        """,
        responses={
            200: PatientProfileSerializer,
            401: "Authentication required",
            403: "Not authorized - patients can only access their own profile",
            404: "Patient profile not found"
        }
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['5. Patient Management (Private)'],
        operation_summary="Update Own Patient Profile",
        operation_description="""
        Update the authenticated patient's own profile.
        
        **Editable Fields:**
        - short_description
        - long_story
        - Other basic profile information
        
        **Not Editable:**
        - Funding amounts (admin only)
        - Status (admin only)
        - Medical details (admin only)
        """,
        request_body=PatientProfileSerializer,
        responses={
            200: PatientProfileSerializer,
            400: "Validation error",
            401: "Authentication required",
            403: "Not authorized"
        }
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update Own Patient Profile (Full)",
        tags=['5. Patient Management (Private)'],
        operation_description="""
        Full update of the authenticated patient's profile.
        
        **Editable Fields:**
        - short_description
        - long_story
        - Other basic profile information
        
        **Not Editable:**
        - Funding amounts (admin only)
        - Status (admin only)
        - Medical details (admin only)
        """,
        request_body=PatientProfileSerializer,
        responses={
            200: PatientProfileSerializer,
            400: "Validation error",
            401: "Authentication required",
            403: "Not authorized"
        }
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def get_object(self):
        try:
            return PatientProfile.objects.get(user=self.request.user)
        except PatientProfile.DoesNotExist:
            raise PatientProfileNotFoundException()
