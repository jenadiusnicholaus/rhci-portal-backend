from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from auth_app.models import CustomUser
from auth_app.permissions import IsDonorOwner
from auth_app.exceptions import DonorProfileNotFoundException
from .models import DonorProfile, Donation, DonationReceipt
from .serializers import (
    DonorRegisterSerializer,
    DonorProfileSerializer,
    PublicDonorProfileSerializer
)
from patient.serializers import (
    DonationCreateSerializer,
    DonationSerializer,
    DonationDetailSerializer
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
        tags=['2. Donor Management (Private)'],
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
        tags=['2. Donor Management (Private)'],
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
        tags=['2. Donor Management (Private)'],
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
        tags=['3. Donor Management (Public)'],
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
        tags=['3. Donor Management (Public)'],
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


# ============ DONATION API VIEWS ============

class DonationCreateView(generics.CreateAPIView):
    """
    Create a new donation (public endpoint - supports anonymous and authenticated donations)
    """
    serializer_class = DonationCreateSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['4. Donations'],
        operation_summary="Create Donation",
        operation_description="""
        Create a new donation (anonymous or authenticated).
        
        **Anonymous Donations:**
        - Set is_anonymous=true
        - Provide anonymous_name and/or anonymous_email
        
        **Authenticated Donations:**
        - Login first and include JWT token
        - is_anonymous=false (default)
        
        **Patient Selection:**
        - Provide patient_id for patient-specific donation
        - Omit patient_id for general fund donation
        
        **Donation Types:**
        - ONE_TIME: Single donation
        - MONTHLY: Recurring monthly donation
        
        **Status:**
        - Initially created with status=PENDING
        - Update to COMPLETED after payment confirmation
        """,
        responses={
            201: openapi.Response(
                description="Donation created successfully",
                schema=DonationSerializer
            ),
            400: "Validation error"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create donation
        donation_data = serializer.validated_data
        
        # Add donor if authenticated
        if request.user.is_authenticated and not donation_data.get('is_anonymous'):
            donation_data['donor'] = request.user
        
        # Get patient if specified
        patient = None
        if donation_data.get('patient_id'):
            from patient.models import PatientProfile
            patient = PatientProfile.objects.get(id=donation_data.pop('patient_id'))
            donation_data['patient'] = patient
        
        # Capture IP and user agent
        donation_data['ip_address'] = self.get_client_ip(request)
        donation_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        # Create donation
        donation = Donation.objects.create(**donation_data)
        
        # Return response
        response_serializer = DonationSerializer(donation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MyDonationsView(generics.ListAPIView):
    """
    List authenticated donor's donations
    """
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['4. Donations'],
        operation_summary="My Donations",
        operation_description="""
        List all donations made by the authenticated user.
        
        **Filtering:**
        - Only shows donations by current user
        - Includes both one-time and recurring donations
        - Ordered by creation date (newest first)
        """,
        responses={
            200: openapi.Response(
                description="List of user's donations",
                schema=DonationSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Donation.objects.filter(donor=self.request.user).select_related('patient')


class DonationDetailView(generics.RetrieveAPIView):
    """
    Get donation details
    """
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        tags=['4. Donations'],
        operation_summary="Get Donation Details",
        operation_description="""
        Get detailed information about a specific donation.
        
        **Access:**
        - User can only view their own donations
        - Admins can view any donation
        """,
        responses={
            200: openapi.Response(
                description="Donation details",
                schema=DonationSerializer
            ),
            404: "Donation not found"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Donation.objects.all().select_related('patient', 'donor')
        return Donation.objects.filter(donor=self.request.user).select_related('patient')


# ============ ADMIN DONATION VIEWS ============

class AdminDonationListView(generics.ListAPIView):
    """
    Admin: List all donations
    """
    serializer_class = DonationDetailSerializer
    permission_classes = [IsAdminUser]
    queryset = Donation.objects.all().select_related('patient', 'donor').order_by('-created_at')
    
    @swagger_auto_schema(
        tags=['5. Admin - Donations'],
        operation_summary="List All Donations (Admin)",
        operation_description="""
        List all donations in the system.
        
        **Admin Only**
        
        **Filtering Options:**
        - Filter by status, donation_type, patient, etc.
        - Ordered by creation date (newest first)
        """,
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by status"),
            openapi.Parameter('donation_type', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by donation type"),
            openapi.Parameter('patient_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Filter by patient ID"),
        ],
        responses={
            200: openapi.Response(
                description="List of all donations",
                schema=DonationDetailSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        donation_type = self.request.query_params.get('donation_type')
        if donation_type:
            queryset = queryset.filter(donation_type=donation_type)
        
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset


class AdminDonationDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin: Get or update donation details
    """
    serializer_class = DonationDetailSerializer
    permission_classes = [IsAdminUser]
    queryset = Donation.objects.all().select_related('patient', 'donor')
    lookup_field = 'id'
    
    @swagger_auto_schema(
        tags=['5. Admin - Donations'],
        operation_summary="Get/Update Donation (Admin)",
        operation_description="""
        Get or update donation details.
        
        **Admin Only**
        
        **Updatable Fields:**
        - status (mark as COMPLETED, FAILED, etc.)
        - payment_method, transaction_id, payment_gateway
        - is_recurring_active (for recurring donations)
        - completed_at (auto-set when status=COMPLETED)
        """,
        responses={
            200: openapi.Response(
                description="Donation details",
                schema=DonationDetailSerializer
            ),
            404: "Donation not found"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['5. Admin - Donations'],
        operation_summary="Update Donation (Admin)",
        responses={
            200: openapi.Response(
                description="Donation updated successfully",
                schema=DonationDetailSerializer
            )
        }
    )
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Auto-set completed_at if status changes to COMPLETED
        if request.data.get('status') == 'COMPLETED' and instance.status != 'COMPLETED':
            request.data['completed_at'] = timezone.now()
        
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['5. Admin - Donations'],
        operation_summary="Update Donation (Admin)",
        responses={
            200: openapi.Response(
                description="Donation updated successfully",
                schema=DonationDetailSerializer
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Auto-set completed_at if status changes to COMPLETED
        if request.data.get('status') == 'COMPLETED' and instance.status != 'COMPLETED':
            request.data['completed_at'] = timezone.now()
        
        return super().patch(request, *args, **kwargs)


class PatientDonationsView(generics.ListAPIView):
    """
    List all donations for a specific patient (public)
    """
    serializer_class = DonationSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['4. Donations'],
        operation_summary="List Patient Donations",
        operation_description="""
        List all completed donations for a specific patient.
        
        **Public Access**
        
        **Note:**
        - Only shows COMPLETED donations
        - Anonymous donations show as "Anonymous"
        """,
        responses={
            200: openapi.Response(
                description="List of patient donations",
                schema=DonationSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return Donation.objects.filter(
            patient_id=patient_id,
            status='COMPLETED'
        ).select_related('donor').order_by('-completed_at')
