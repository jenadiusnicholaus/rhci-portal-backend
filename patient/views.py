from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import random

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
        tags=['Authentication & Registration'],
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
        tags=['Patient Management (Private)'],
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
        tags=['Patient Management (Private)'],
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
        tags=['Patient Management (Private)'],
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


class RandomizedPatientListView(APIView):
    """
    Get randomized patients with pagination (1 patient per page).
    Each API call randomizes the order, so pagination returns different patients.
    """
    authentication_classes = []  # No authentication required
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Patient Discovery'],
        operation_summary="Get Randomized Patient (AI-Powered Discovery)",
        operation_description="""
        Discover patients in randomized order for engaging user experience.
        
        **Features:**
        - 🎲 Every API call randomizes patient order
        - 📄 1 patient per page for focused viewing
        - 🔄 Pagination support (but order changes each call)
        - ✅ Only shows verified, active patients needing funding
        
        **Use Case:**
        Perfect for homepage/discovery features where you want to show 
        different patients each time without predictable ordering.
        
        **Example Flow:**
        ```
        Call 1, Page 1: Patient #45
        Call 2, Page 1: Patient #12  (randomized!)
        Call 2, Page 2: Patient #78
        Call 3, Page 1: Patient #3   (randomized again!)
        ```
        """,
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number (1 patient per page)",
                type=openapi.TYPE_INTEGER,
                default=1
            )
        ],
        responses={
            200: openapi.Response(
                description='Randomized patient data',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total active patients'),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, description='Next page URL', nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, description='Previous page URL', nullable=True),
                        'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Current page number'),
                        'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total pages available'),
                        'patient': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Patient profile data',
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'age': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'diagnosis': openapi.Schema(type=openapi.TYPE_STRING),
                                'short_description': openapi.Schema(type=openapi.TYPE_STRING),
                                'funding_required': openapi.Schema(type=openapi.TYPE_STRING),
                                'funding_received': openapi.Schema(type=openapi.TYPE_STRING),
                                'funding_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                ),
                examples={
                    'application/json': {
                        'count': 15,
                        'next': 'http://api/patients/random/?page=2',
                        'previous': None,
                        'current_page': 1,
                        'total_pages': 15,
                        'patient': {
                            'id': 7,
                            'full_name': 'John Doe',
                            'age': 45,
                            'diagnosis': 'Cancer Treatment',
                            'short_description': 'Needs urgent surgery',
                            'funding_required': '1000.00',
                            'funding_received': '250.00',
                            'funding_percentage': 25.0,
                            'status': 'SEEKING_FUNDING'
                        }
                    }
                }
            ),
            404: 'No patients found'
        }
    )
    def get(self, request):
        # Get all published patients needing funding
        patients = PatientProfile.objects.filter(
            status__in=['PUBLISHED', 'AWAITING_FUNDING']
        ).select_related('user')
        
        total_count = patients.count()
        
        if total_count == 0:
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'current_page': 1,
                'total_pages': 0,
                'patient': None,
                'message': 'No patients available at this time'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get page number from query params
        page_number = int(request.query_params.get('page', 1))
        
        # Validate page number
        if page_number < 1:
            page_number = 1
        if page_number > total_count:
            page_number = total_count
        
        # Randomize the patient list (fresh random order each call!)
        patients_list = list(patients)
        random.shuffle(patients_list)
        
        # Get the patient for current page (1 per page)
        patient_index = page_number - 1
        patient = patients_list[patient_index]
        
        # Serialize patient data with request context for absolute URLs
        serializer = PatientProfileSerializer(patient, context={'request': request})
        
        # Build pagination URLs
        base_url = request.build_absolute_uri(request.path)
        next_url = f"{base_url}?page={page_number + 1}" if page_number < total_count else None
        previous_url = f"{base_url}?page={page_number - 1}" if page_number > 1 else None
        
        return Response({
            'count': total_count,
            'next': next_url,
            'previous': previous_url,
            'current_page': page_number,
            'total_pages': total_count,
            'patient': serializer.data
        }, status=status.HTTP_200_OK)
