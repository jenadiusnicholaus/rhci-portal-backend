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
        tags=['Authentication & Registration'],
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
        tags=['Donor Management (Private)'],
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
        tags=['Donor Management (Private)'],
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
        tags=['Donor Management (Private)'],
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
        tags=['Donor Management (Public)'],
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
        tags=['Donor Management (Public)'],
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
        tags=['Donations'],
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
        tags=['Donations'],
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
        tags=['Donations'],
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
        tags=['Admin - Donations'],
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
        tags=['Admin - Donations'],
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
        tags=['Admin - Donations'],
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
        tags=['Admin - Donations'],
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
        tags=['Donations'],
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


# ============ ADMIN DONOR MANAGEMENT ============

class AdminDonorListView(generics.ListAPIView):
    """
    Admin endpoint to list all donor accounts.
    Includes search, filtering, and pagination.
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="🔴 [ADMIN] List All Donors",
        operation_description="**NEW ENDPOINT** - List all donor accounts with profile information. Supports search by name, email, or workplace. Filter by privacy status and verification status.",
        tags=['Admin - Donor Management'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by name, email, or workplace", type=openapi.TYPE_STRING),
            openapi.Parameter('is_verified', openapi.IN_QUERY, description="Filter by verification status (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_private', openapi.IN_QUERY, description="Filter by privacy status (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: DonorProfileSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = DonorProfile.objects.select_related('user', 'country_fk').all()
        
        # Search filter
        search = self.request.query_params.get('search', None)
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(workplace__icontains=search)
            )
        
        # Verification filter
        is_verified = self.request.query_params.get('is_verified', None)
        if is_verified is not None:
            is_verified_bool = is_verified.lower() == 'true'
            queryset = queryset.filter(user__is_verified=is_verified_bool)
        
        # Privacy filter
        is_private = self.request.query_params.get('is_private', None)
        if is_private is not None:
            is_private_bool = is_private.lower() == 'true'
            queryset = queryset.filter(is_profile_private=is_private_bool)
        
        return queryset.order_by('-created_at')


class AdminDonorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to view, update, or delete a donor account.
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="🔴 [ADMIN] Get Donor Details",
        operation_description="**NEW ENDPOINT** - Retrieve complete donor profile information including donation history and statistics.",
        tags=['Admin - Donor Management'],
        responses={
            200: DonorProfileSerializer,
            404: "Donor not found"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="🔴 [ADMIN] Update Donor Profile",
        operation_description="**NEW ENDPOINT** - Update donor profile information. Can modify all profile fields.",
        tags=['Admin - Donor Management'],
        responses={
            200: DonorProfileSerializer,
            400: "Validation error",
            404: "Donor not found"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="🔴 [ADMIN] Partial Update Donor",
        operation_description="**NEW ENDPOINT** - Partially update donor profile. Only provided fields will be updated.",
        tags=['Admin - Donor Management'],
        responses={
            200: DonorProfileSerializer,
            400: "Validation error",
            404: "Donor not found"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="🔴 [ADMIN] Delete Donor Account",
        operation_description="**NEW ENDPOINT** - Permanently delete a donor account and associated profile. This action cannot be undone.",
        tags=['Admin - Donor Management'],
        responses={
            204: "Donor deleted successfully",
            404: "Donor not found"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        return DonorProfile.objects.select_related('user', 'country_fk').all()


class AdminDonorActivationView(APIView):
    """
    Admin endpoint to activate/deactivate donor accounts.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="🔴 [ADMIN] Activate/Deactivate Donor",
        operation_description="**NEW ENDPOINT** - Activate or deactivate a donor account. Deactivated donors cannot login or make donations.",
        tags=['Admin - Donor Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['is_active'],
            properties={
                'is_active': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Set to true to activate, false to deactivate'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Activation status updated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'donor_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'donor_email': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            400: "Validation error",
            404: "Donor not found"
        }
    )
    def patch(self, request, id):
        """Update donor activation status"""
        from django.shortcuts import get_object_or_404
        
        # Get donor profile
        donor_profile = get_object_or_404(DonorProfile, id=id)
        
        # Validate input
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response(
                {'error': 'is_active field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user activation status
        donor_profile.user.is_active = is_active
        donor_profile.user.save(update_fields=['is_active'])
        
        return Response({
            'message': f'Donor account {"activated" if is_active else "deactivated"} successfully',
            'donor_id': donor_profile.id,
            'donor_email': donor_profile.user.email,
            'is_active': donor_profile.user.is_active
        }, status=status.HTTP_200_OK)


class AdminDonorStatsView(APIView):
    """
    Admin endpoint for donor statistics.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="🔴 [ADMIN] Donor Statistics",
        operation_description="**NEW ENDPOINT** - Get comprehensive donor statistics including total donors, verified donors, total donations, and top donors.",
        tags=['Admin - Donor Management'],
        responses={
            200: openapi.Response(
                description="Donor statistics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_donors': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'verified_donors': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_donors': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'private_profiles': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_donations': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_donated_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'top_donors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'donor_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'donor_email': openapi.Schema(type=openapi.TYPE_STRING),
                                    'total_donated': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'donation_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        from django.db.models import Count, Sum
        
        # Basic counts
        total_donors = DonorProfile.objects.count()
        verified_donors = DonorProfile.objects.filter(user__is_verified=True).count()
        active_donors = DonorProfile.objects.filter(user__is_active=True).count()
        private_profiles = DonorProfile.objects.filter(is_profile_private=True).count()
        
        # Donation stats
        total_donations = Donation.objects.filter(status='COMPLETED', donor__isnull=False).count()
        total_donated_amount = Donation.objects.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Top donors
        top_donors_data = Donation.objects.filter(
            status='COMPLETED',
            donor__isnull=False
        ).values(
            'donor__id',
            'donor__email',
            'donor__donor_profile__full_name'
        ).annotate(
            total_donated=Sum('amount'),
            donation_count=Count('id')
        ).order_by('-total_donated')[:10]
        
        top_donors = []
        for donor in top_donors_data:
            top_donors.append({
                'donor_name': donor['donor__donor_profile__full_name'] or 'N/A',
                'donor_email': donor['donor__email'],
                'total_donated': float(donor['total_donated']),
                'donation_count': donor['donation_count']
            })
        
        stats = {
            'total_donors': total_donors,
            'verified_donors': verified_donors,
            'active_donors': active_donors,
            'private_profiles': private_profiles,
            'total_donations': total_donations,
            'total_donated_amount': float(total_donated_amount),
            'top_donors': top_donors
        }
        
        return Response(stats)
