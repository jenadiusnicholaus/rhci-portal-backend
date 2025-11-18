from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    DonorRegisterSerializer, DonorProfileSerializer, PatientRegisterSerializer, 
    LoginSerializer, UserSerializer, PatientProfileSerializer
)
from .models import CustomUser, DonorProfile, PatientProfile
from .exceptions import (
    DonorProfileNotFoundException,
    PatientProfileNotFoundException,
    InsufficientPermissionsException
)


class DonorRegisterView(generics.CreateAPIView):
    """
    Register a new donor account.
    
    Creates a donor user account and automatically creates an associated donor profile.
    Email verification is required before the account can be used.
    """
    serializer_class = DonorRegisterSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Register as Donor",
        operation_description="Create a new donor account with email and password. A donor profile is automatically created.",
        tags=['1. Authentication & Registration'],
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
            'message': 'Donor registration successful. Check your email to verify.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class PatientRegisterView(generics.CreateAPIView):
    """
    Register a new patient account.
    
    Creates a patient user account with medical story. Profile must be approved by admin before becoming public.
    """
    serializer_class = PatientRegisterSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Register as Patient",
        operation_description="Create a new patient account with personal details and medical story. Requires admin approval before publication.",
        tags=['1. Authentication & Registration'],
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
            'user': UserSerializer(user).data
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
        tags=['1. Authentication & Registration'],
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
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current authenticated user's basic profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get Current User Profile",
        operation_description="Retrieve or update basic user information for the authenticated user.",
        tags=['2. User Profile Management'],
        responses={
            200: UserSerializer,
            401: 'Unauthorized'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update Current User Profile",
        tags=['2. User Profile Management'],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def get_object(self):
        return self.request.user


class DonorProfileView(generics.RetrieveUpdateAPIView):
    """
    Donor's own profile management (authenticated access only)
    GET: View own profile
    PATCH/PUT: Update own profile
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get My Donor Profile",
        operation_description="Retrieve the authenticated donor's profile with all details.",
        tags=['3. Donor Management (Private)'],
        responses={
            200: DonorProfileSerializer,
            401: 'Unauthorized',
            403: 'Forbidden - Not a donor account'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update My Donor Profile",
        operation_description="Update donor profile details (photo, bio, privacy settings, etc.).",
        tags=['3. Donor Management (Private)'],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def get_object(self):
        # Only donors can manage their own profile
        if self.request.user.user_type != 'DONOR':
            raise InsufficientPermissionsException(
                detail="Only donors can access this endpoint. Please ensure you registered as a donor."
            )
        
        if not hasattr(self.request.user, 'donor_profile'):
            raise DonorProfileNotFoundException()
        
        return self.request.user.donor_profile


class PublicDonorProfileView(generics.RetrieveAPIView):
    """
    Public donor profile view (read-only)
    Anyone can view public profiles (is_profile_private=False)
    Only the owner can view private profiles
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="View Public Donor Profile",
        operation_description="View a specific donor's public profile. Private profiles require owner authentication.",
        tags=['4. Donor Management (Public)'],
        responses={
            200: DonorProfileSerializer,
            403: 'Forbidden - Profile is private',
            404: 'Not Found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_object(self):
        profile_id = self.kwargs.get('id')
        profile = get_object_or_404(DonorProfile, id=profile_id)
        
        # Check if profile is private
        if profile.is_profile_private:
            # Only the owner can view private profile
            if not self.request.user.is_authenticated or self.request.user != profile.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("This profile is private and can only be viewed by the owner.")
        
        return profile


class DonorProfileListView(generics.ListAPIView):
    """
    List all public donor profiles
    Only shows profiles where is_profile_private=False
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="List Public Donors",
        operation_description="Browse all public donor profiles. Private profiles are excluded.",
        tags=['4. Donor Management (Public)'],
        responses={
            200: DonorProfileSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        # Only return public profiles
        return DonorProfile.objects.filter(is_profile_private=False).select_related('user')


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
        tags=['5. Patient Management (Private)'],
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
        tags=['5. Patient Management (Private)'],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
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
        tags=['6. Patient Management (Public)'],
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
        tags=['6. Patient Management (Public)'],
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
