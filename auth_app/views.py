from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    PatientRegisterSerializer, 
    LoginSerializer, UserSerializer, PatientProfileSerializer, CountryLookupSerializer
)
from .models import CustomUser
from .lookups import CountryLookup
from patient.models import PatientProfile, ExpenseTypeLookup
from patient.serializers import ExpenseTypeLookupSerializer
from .exceptions import (
    PatientProfileNotFoundException,
    InsufficientPermissionsException
)


class PatientRegisterView(generics.CreateAPIView):
    """
    Register a new patient account.
    
    Creates a patient user account with medical story. Profile must be approved by admin before becoming public.
    """
    serializer_class = PatientRegisterSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="🟠 Register as Patient",
        operation_description="**UPDATED** - Create a new patient account with personal details and medical story. Now supports multiple Base64-encoded images and YouTube video URL. No password required - uses phone number instead. Requires admin approval before publication.",
        tags=['Authentication & Registration'],
        responses={
            201: openapi.Response('Registration successful', UserSerializer),
            400: 'Bad Request - Validation errors'
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Patient registration successful. Check your email to verify.',
            'user': UserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    Login with email and password to obtain JWT tokens.
    
    Returns access and refresh tokens for authentication.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="User Login",
        operation_description="Authenticate with email and password to receive JWT access and refresh tokens.",
        tags=['Authentication & Registration'],
        responses={
            200: openapi.Response(
                'Login successful',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            401: 'Unauthorized - Invalid credentials',
            403: 'Forbidden - Email not verified or account inactive'
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate JWT tokens using SimpleJWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current authenticated user's basic profile (Admin only).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Get Current User Profile",
        operation_description="[ADMIN ONLY] Retrieve or update basic user information for the authenticated admin.",
        tags=['Admin - User Management'],
        responses={
            200: UserSerializer,
            401: 'Unauthorized'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Update Current User Profile",
        tags=['Admin - User Management'],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Update Current User Profile (Full)",
        tags=['Admin - User Management'],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    def get_object(self):
        return self.request.user


class PatientProfileView(generics.RetrieveUpdateAPIView):
    """
    Patient's own profile management (authenticated access only)
    GET: View own profile
    PATCH/PUT: Update own profile
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get My Patient Profile",
        operation_description="Retrieve the authenticated patient's complete profile including timeline and funding details.",
        tags=['Patient Management (Private)'],
        responses={
            200: PatientProfileSerializer,
            401: 'Unauthorized',
            403: 'Forbidden - Not a patient account'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update My Patient Profile",
        operation_description="Update patient profile story and basic details.",
        tags=['Patient Management (Private)'],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update My Patient Profile (Full)",
        operation_description="Update patient profile story and basic details (full update).",
        tags=['Patient Management (Private)'],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    def get_object(self):
        # Only patients can manage their own profile
        if self.request.user.user_type != 'PATIENT':
            raise InsufficientPermissionsException(
                detail="Only patients can access this endpoint. Please ensure you registered as a patient."
            )
        
        if not hasattr(self.request.user, 'patient_profile'):
            raise PatientProfileNotFoundException()
        
        return self.request.user.patient_profile


class PublicPatientProfileView(generics.RetrieveAPIView):
    """
    Public patient profile view (read-only)
    Anyone can view published patient profiles
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="View Patient Profile (Deprecated)",
        operation_description="This endpoint is deprecated. Use /api/auth/public/patients/{id}/ instead.",
        tags=['Patient Management (Public)'],
        deprecated=True,
        responses={
            200: PatientProfileSerializer,
            404: 'Not Found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        # Only show published or fully funded patients
        return PatientProfile.objects.filter(
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED', 'TREATMENT_COMPLETE']
        )


class PatientProfileListView(generics.ListAPIView):
    """
    List all published patient profiles for public viewing
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="List Patients (Deprecated)",
        operation_description="This endpoint is deprecated. Use /api/auth/public/patients/ instead for better filtering and pagination.",
        tags=['Patient Management (Public)'],
        deprecated=True,
        responses={
            200: PatientProfileSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        # Only show published, awaiting funding, or fully funded patients
        return PatientProfile.objects.filter(
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED']
        ).select_related('user')


class CountryLookupListView(generics.ListAPIView):
    """
    Get list of all available countries for selection.
    """
    serializer_class = CountryLookupSerializer
    permission_classes = [AllowAny]
    queryset = CountryLookup.objects.filter(is_active=True)
    
    @swagger_auto_schema(
        operation_summary="Get Countries List",
        operation_description="Retrieve list of all available countries for user selection.",
        tags=['Lookups'],
        responses={
            200: CountryLookupSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExpenseTypeLookupListView(generics.ListAPIView):
    """
    Get list of all available expense types for treatment cost breakdowns.
    """
    serializer_class = ExpenseTypeLookupSerializer
    permission_classes = [AllowAny]
    queryset = ExpenseTypeLookup.objects.filter(is_active=True)
    
    @swagger_auto_schema(
        operation_summary="Get Expense Types List",
        operation_description="Retrieve list of all available expense types for treatment cost breakdowns (e.g., Hospital Fees, Medical Staff, etc.).",
        tags=['Lookups'],
        responses={
            200: ExpenseTypeLookupSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ============ ADMIN EXPENSE TYPE MANAGEMENT ============

class AdminExpenseTypeListCreateView(generics.ListCreateAPIView):
    """
    🔴 NEW - Admin API to list and create expense types for cost breakdowns.
    """
    serializer_class = ExpenseTypeLookupSerializer
    permission_classes = [IsAdminUser]
    queryset = ExpenseTypeLookup.objects.all().order_by('display_order', 'name')
    
    @swagger_auto_schema(
        operation_summary="List All Expense Types (Admin)",
        operation_description="""
        Admin endpoint to retrieve all expense types including inactive ones.
        Returns expense types ordered by display_order and name.
        """,
        tags=['Admin - Expense Type Management'],
        responses={
            200: ExpenseTypeLookupSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Create New Expense Type (Admin)",
        operation_description="""
        Admin endpoint to create a new expense type for treatment cost breakdowns.
        
        **Required fields:**
        - name: Display name (e.g., "Hospital Fees")
        - slug: URL-friendly identifier (e.g., "hospital-fees")
        
        **Optional fields:**
        - description: Detailed description of the expense type
        - is_active: Whether this expense type is active (default: true)
        - display_order: Order to display in breakdown lists (default: 0)
        """,
        tags=['Admin - Expense Type Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'slug'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, example='Transportation'),
                'slug': openapi.Schema(type=openapi.TYPE_STRING, example='transportation'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, example='Patient transportation and travel costs'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                'display_order': openapi.Schema(type=openapi.TYPE_INTEGER, default=0),
            }
        ),
        responses={
            201: ExpenseTypeLookupSerializer,
            400: 'Bad Request - Validation errors'
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminExpenseTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    🔴 NEW - Admin API to retrieve, update, or delete a specific expense type.
    """
    serializer_class = ExpenseTypeLookupSerializer
    permission_classes = [IsAdminUser]
    queryset = ExpenseTypeLookup.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="Get Expense Type Details (Admin)",
        operation_description="Admin endpoint to retrieve details of a specific expense type by ID.",
        tags=['Admin - Expense Type Management'],
        responses={
            200: ExpenseTypeLookupSerializer,
            404: 'Not Found - Expense type does not exist'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update Expense Type (Admin)",
        operation_description="""
        Admin endpoint to update an expense type. 
        Use PUT for full update or PATCH for partial update.
        
        **Note:** Changing slug may affect existing cost breakdowns.
        """,
        tags=['Admin - Expense Type Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, example='Medical Transportation'),
                'slug': openapi.Schema(type=openapi.TYPE_STRING, example='medical-transportation'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, example='Updated description'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'display_order': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
        responses={
            200: ExpenseTypeLookupSerializer,
            400: 'Bad Request - Validation errors',
            404: 'Not Found - Expense type does not exist'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Partially Update Expense Type (Admin)",
        operation_description="Admin endpoint to partially update an expense type (only provided fields will be updated).",
        tags=['Admin - Expense Type Management'],
        responses={
            200: ExpenseTypeLookupSerializer,
            400: 'Bad Request - Validation errors',
            404: 'Not Found - Expense type does not exist'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete Expense Type (Admin)",
        operation_description="""
        Admin endpoint to delete an expense type.
        
        **Warning:** This will fail if the expense type is used in existing cost breakdowns.
        Consider setting is_active=false instead of deleting.
        """,
        tags=['Admin - Expense Type Management'],
        responses={
            204: 'Successfully deleted',
            400: 'Bad Request - Cannot delete expense type in use',
            404: 'Not Found - Expense type does not exist'
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
