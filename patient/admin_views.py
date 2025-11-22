from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from auth_app.models import CustomUser
from auth_app.permissions import IsAdminUser
from auth_app.exceptions import PatientProfileNotFoundException
from .models import PatientProfile, PatientTimeline
from .serializers import (
    AdminPatientReviewSerializer,
    AdminPatientApprovalSerializer,
    AdminPatientPublishSerializer,
    AdminTimelineEventSerializer,
    PatientProfileSerializer,
    AdminPatientManagementSerializer,
    AdminPatientCreateSerializer,
    AdminPatientBulkActionSerializer,
    AdminPatientStatsSerializer
)


# ============ ADMIN PATIENT REVIEW VIEWS ============

class AdminPatientListView(generics.ListAPIView):
    """
    Admin endpoint to list all patient submissions.
    Filter by status, country, etc.
    """
    serializer_class = AdminPatientReviewSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'country', 'diagnosis', 'medical_partner']
    ordering_fields = ['created_at', 'status', 'funding_percentage']
    ordering = ['-created_at']
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] List All Patient Submissions",
        operation_description="Retrieve all patient profiles with advanced filtering. Includes pending, approved, and published patients.",
        tags=['Admin - Patient Review & Management'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (SUBMITTED, PUBLISHED, etc.)", type=openapi.TYPE_STRING),
            openapi.Parameter('country', openapi.IN_QUERY, description="Filter by country", type=openapi.TYPE_STRING),
            openapi.Parameter('verified', openapi.IN_QUERY, description="Filter by verification status (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in name, country, diagnosis, medical partner", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field (prefix with - for descending)", type=openapi.TYPE_STRING),
        ],
        responses={
            200: AdminPatientReviewSerializer(many=True),
            401: 'Unauthorized',
            403: 'Forbidden - Admin access required'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = PatientProfile.objects.all().select_related('user').prefetch_related(
            'cost_breakdowns', 'timeline_events'
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by country
        country_filter = self.request.query_params.get('country', None)
        if country_filter:
            queryset = queryset.filter(country__icontains=country_filter)
        
        # Filter by verified status
        verified = self.request.query_params.get('verified', None)
        if verified is not None:
            verified_bool = verified.lower() == 'true'
            queryset = queryset.filter(user__is_patient_verified=verified_bool)
        
        return queryset


class AdminPatientDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin endpoint to view and edit full patient profile.
    Admin can edit story, medical details, funding, etc.
    """
    serializer_class = AdminPatientReviewSerializer
    permission_classes = [IsAdminUser]
    queryset = PatientProfile.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] View Patient Details",
        operation_description="Retrieve complete patient profile with all details including timeline and cost breakdown.",
        tags=['Admin - Patient Review & Management'],
        responses={
            200: AdminPatientReviewSerializer,
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Edit Patient Profile",
        operation_description="Update patient profile details including medical information, funding, and story.",
        tags=['Admin - Patient Review & Management'],
        responses={
            200: AdminPatientReviewSerializer,
            400: 'Bad Request - Validation errors',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Edit Patient Profile (Full)",
        operation_description="Full update of patient profile details including medical information, funding, and story.",
        tags=['Admin - Patient Review & Management'],
        responses={
            200: AdminPatientReviewSerializer,
            400: 'Bad Request - Validation errors',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    def get_queryset(self):
        return PatientProfile.objects.all().select_related('user').prefetch_related(
            'cost_breakdowns', 'timeline_events'
        )


class AdminPatientApprovalView(APIView):
    """
    Admin endpoint to approve or reject patient profiles.
    POST with action: 'approve' or 'reject'
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Approve/Reject Patient",
        operation_description="Approve or reject a patient profile submission. Approval verifies the user and creates timeline event.",
        tags=['Admin - Patient Review & Management'],
        request_body=AdminPatientApprovalSerializer,
        responses={
            200: openapi.Response('Action completed successfully', AdminPatientReviewSerializer),
            400: 'Bad Request - Invalid action or missing rejection reason',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def post(self, request, id):
        patient_profile = get_object_or_404(PatientProfile, id=id)
        serializer = AdminPatientApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        
        if action == 'approve':
            # Mark user as verified and patient as verified
            patient_profile.user.is_verified = True
            patient_profile.user.is_patient_verified = True
            patient_profile.user.is_active = True
            patient_profile.user.save()
            
            # Clear any rejection reason
            patient_profile.rejection_reason = ''
            patient_profile.save()
            
            # Create timeline event
            PatientTimeline.objects.create(
                patient_profile=patient_profile,
                event_type='PROFILE_SUBMITTED',
                title='Profile Approved',
                description=f'Profile approved by admin {request.user.email}',
                created_by=request.user,
                is_milestone=True
            )
            
            return Response({
                'message': 'Patient profile approved successfully.',
                'patient': AdminPatientReviewSerializer(patient_profile).data
            }, status=status.HTTP_200_OK)
        
        else:  # reject
            rejection_reason = serializer.validated_data.get('rejection_reason', '')
            
            # Mark as not verified
            patient_profile.user.is_patient_verified = False
            patient_profile.user.save()
            
            # Save rejection reason
            patient_profile.rejection_reason = rejection_reason
            patient_profile.status = 'SUBMITTED'
            patient_profile.save()
            
            # Create timeline event
            PatientTimeline.objects.create(
                patient_profile=patient_profile,
                event_type='STATUS_CHANGED',
                title='Profile Rejected',
                description=f'Profile rejected: {rejection_reason}',
                created_by=request.user,
                is_visible=False  # Don't show rejection to public
            )
            
            # TODO: Send email notification to patient
            
            return Response({
                'message': 'Patient profile rejected.',
                'rejection_reason': rejection_reason
            }, status=status.HTTP_200_OK)


class AdminPatientPublishView(APIView):
    """
    Admin endpoint to publish patient profiles to make them publicly visible.
    POST with publish: true/false, featured: true/false
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Publish/Unpublish Patient",
        operation_description="Publish patient profile to make it visible on public API. Can mark as featured for homepage.",
        tags=['Admin - Patient Review & Management'],
        request_body=AdminPatientPublishSerializer,
        responses={
            200: openapi.Response('Patient published successfully', AdminPatientReviewSerializer),
            400: 'Bad Request - Patient must be verified before publishing',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def post(self, request, id):
        patient_profile = get_object_or_404(PatientProfile, id=id)
        serializer = AdminPatientPublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        should_publish = serializer.validated_data.get('publish', True)
        is_featured = serializer.validated_data.get('featured', False)
        
        if should_publish:
            # Patient must be verified before publishing
            if not patient_profile.user.is_patient_verified:
                return Response({
                    'error': True,
                    'message': 'Patient must be verified before publishing.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update status to published
            patient_profile.status = 'PUBLISHED'
            patient_profile.is_featured = is_featured
            patient_profile.save()
            
            # Create timeline event
            PatientTimeline.objects.create(
                patient_profile=patient_profile,
                event_type='PROFILE_PUBLISHED',
                title='Profile Published',
                description=f'Profile published by admin {request.user.email}',
                created_by=request.user,
                is_milestone=True
            )
            
            # If funding is needed, create awaiting funding event
            if patient_profile.funding_required > 0 and patient_profile.funding_received < patient_profile.funding_required:
                PatientTimeline.objects.create(
                    patient_profile=patient_profile,
                    event_type='AWAITING_FUNDING',
                    title='Awaiting Funding',
                    description=f'Seeking ${patient_profile.funding_required:,.2f} for treatment',
                    created_by=request.user,
                    is_milestone=True,
                    is_current_state=True
                )
                patient_profile.status = 'AWAITING_FUNDING'
                patient_profile.save()
            
            return Response({
                'message': 'Patient profile published successfully.',
                'patient': AdminPatientReviewSerializer(patient_profile).data
            }, status=status.HTTP_200_OK)
        
        else:
            # Unpublish profile
            patient_profile.status = 'SUBMITTED'
            patient_profile.is_featured = False
            patient_profile.save()
            
            return Response({
                'message': 'Patient profile unpublished.'
            }, status=status.HTTP_200_OK)


# ============ ADMIN TIMELINE MANAGEMENT VIEWS ============

class AdminTimelineEventCreateView(generics.CreateAPIView):
    """
    Admin endpoint to manually add timeline events.
    """
    serializer_class = AdminTimelineEventSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Create Timeline Event",
        operation_description="Manually add a timeline event to a patient's journey. Supports TBD (future) events with event_date.",
        tags=['Admin - Timeline Management'],
        responses={
            201: AdminTimelineEventSerializer,
            400: 'Bad Request - Validation errors',
            403: 'Forbidden - Admin access required'
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # Set created_by to current admin user
        serializer.save(created_by=self.request.user)


class AdminTimelineEventUpdateView(generics.UpdateAPIView):
    """
    Admin endpoint to edit existing timeline events.
    """
    serializer_class = AdminTimelineEventSerializer
    permission_classes = [IsAdminUser]
    queryset = PatientTimeline.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Update Timeline Event",
        operation_description="Edit existing timeline event. Setting is_current_state=true will automatically unmark all other events.",
        tags=['Admin - Timeline Management'],
        responses={
            200: AdminTimelineEventSerializer,
            400: 'Bad Request - Validation errors',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Update Timeline Event (Full)",
        operation_description="Full update of timeline event. Setting is_current_state=true will automatically unmark all other events.",
        tags=['Admin - Timeline Management'],
        responses={
            200: AdminTimelineEventSerializer,
            400: 'Bad Request - Validation errors',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        # If marking as current state, unmark all other events
        if serializer.validated_data.get('is_current_state', False):
            patient_profile = serializer.instance.patient_profile
            PatientTimeline.objects.filter(
                patient_profile=patient_profile
            ).exclude(id=serializer.instance.id).update(is_current_state=False)
        
        serializer.save()


class AdminTimelineEventDeleteView(generics.DestroyAPIView):
    """
    Admin endpoint to remove timeline events.
    """
    permission_classes = [IsAdminUser]
    queryset = PatientTimeline.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Delete Timeline Event",
        operation_description="Remove a timeline event. Cannot delete auto-generated milestone events (PROFILE_SUBMITTED, PROFILE_PUBLISHED, FULLY_FUNDED).",
        tags=['Admin - Timeline Management'],
        responses={
            204: 'Timeline event deleted successfully',
            400: 'Bad Request - Cannot delete protected milestone events',
            403: 'Forbidden - Admin access required',
            404: 'Not Found'
        }
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Don't allow deleting auto-generated milestone events
        if instance.is_milestone and instance.event_type in [
            'PROFILE_SUBMITTED', 'PROFILE_PUBLISHED', 'FULLY_FUNDED'
        ]:
            return Response({
                'error': True,
                'message': 'Cannot delete auto-generated milestone events.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response({
            'message': 'Timeline event deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)


class AdminTimelineEventListView(generics.ListAPIView):
    """
    Admin endpoint to view all timeline events for a patient.
    """
    serializer_class = AdminTimelineEventSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] List Patient Timeline",
        operation_description="View all timeline events for a specific patient in chronological order.",
        tags=['Admin - Timeline Management'],
        responses={
            200: AdminTimelineEventSerializer(many=True),
            403: 'Forbidden - Admin access required'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        if patient_id:
            return PatientTimeline.objects.filter(
                patient_profile_id=patient_id
            ).select_related('patient_profile', 'created_by').order_by('created_at')
        return PatientTimeline.objects.none()


# ============ PUBLIC PATIENT PROFILE VIEWS ============

class PublicPatientDetailView(generics.RetrieveAPIView):
    """
    Public endpoint to view individual patient profile.
    Only verified and published patients are visible.
    """
    serializer_class = PatientProfileSerializer
    permission_classes = []  # Public access
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="View Patient Profile",
        operation_description="View complete patient profile including story, timeline, funding details, and cost breakdown. Only published patients are accessible.",
        tags=['Public - Patient Profiles'],
        responses={
            200: PatientProfileSerializer,
            404: 'Not Found - Patient not published or does not exist'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return PatientProfile.objects.filter(
            user__is_patient_verified=True,
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED', 'TREATMENT_COMPLETE']
        ).select_related('user').prefetch_related('cost_breakdowns', 'timeline_events')


class PublicPatientListView(generics.ListAPIView):
    """
    Public endpoint to list all published patient profiles.
    Supports filtering by country, medical partner, funding status.
    """
    serializer_class = PatientProfileSerializer
    permission_classes = []  # Public access
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'country', 'diagnosis', 'medical_partner']
    ordering_fields = ['created_at', 'funding_percentage']
    ordering = ['-created_at']
    
    @swagger_auto_schema(
        operation_summary="List All Patients",
        operation_description="Browse all published patient profiles with advanced filtering and search. Perfect for donor browsing.",
        tags=['Public - Patient Profiles'],
        manual_parameters=[
            openapi.Parameter('country', openapi.IN_QUERY, description="Filter by country", type=openapi.TYPE_STRING),
            openapi.Parameter('medical_partner', openapi.IN_QUERY, description="Filter by hospital/medical partner", type=openapi.TYPE_STRING),
            openapi.Parameter('funding_status', openapi.IN_QUERY, description="Filter by funding status (fully_funded, awaiting_funding, partially_funded)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in name, country, diagnosis, medical partner", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field (created_at, funding_percentage). Prefix with - for descending", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number for pagination", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: PatientProfileSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = PatientProfile.objects.filter(
            user__is_patient_verified=True,
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED']
        ).select_related('user').prefetch_related('cost_breakdowns', 'timeline_events')
        
        # Filter by country
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        # Filter by medical partner
        medical_partner = self.request.query_params.get('medical_partner', None)
        if medical_partner:
            queryset = queryset.filter(medical_partner__icontains=medical_partner)
        
        # Filter by funding status
        funding_status = self.request.query_params.get('funding_status', None)
        if funding_status == 'fully_funded':
            queryset = queryset.filter(status='FULLY_FUNDED')
        elif funding_status == 'awaiting_funding':
            queryset = queryset.filter(status='AWAITING_FUNDING')
        elif funding_status == 'partially_funded':
            queryset = queryset.filter(
                status='AWAITING_FUNDING',
                funding_received__gt=0
            )
        
        return queryset


class PublicFeaturedPatientsView(generics.ListAPIView):
    """
    Public endpoint for featured patients (for homepage).
    Returns only featured patients.
    """
    serializer_class = PatientProfileSerializer
    permission_classes = []  # Public access
    
    @swagger_auto_schema(
        operation_summary="Featured Patients (Homepage)",
        operation_description="Get up to 6 featured patients for homepage display. Only returns published and verified patients marked as featured.",
        tags=['Public - Patient Profiles'],
        responses={
            200: PatientProfileSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return PatientProfile.objects.filter(
            user__is_patient_verified=True,
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED'],
            is_featured=True
        ).select_related('user').prefetch_related(
            'cost_breakdowns', 'timeline_events'
        ).order_by('-created_at')[:6]  # Limit to 6 featured patients


# ============ NEW COMPREHENSIVE ADMIN PATIENT MANAGEMENT VIEWS ============

class AdminPatientManagementListView(generics.ListCreateAPIView):
    """
    Comprehensive admin endpoint for patient management.
    GET: List all patients with advanced filtering and search
    POST: Create new patient profile
    """
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'user__email', 'diagnosis', 'medical_partner', 'country_fk__name']
    ordering_fields = ['created_at', 'updated_at', 'status', 'funding_percentage', 'funding_required', 'full_name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminPatientCreateSerializer
        return AdminPatientManagementSerializer
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] List All Patients",
        operation_description="Retrieve all patient profiles with comprehensive filtering, search, and pagination for admin management.",
        tags=['Admin - Patient Review & Management'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('country', openapi.IN_QUERY, description="Filter by country ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('gender', openapi.IN_QUERY, description="Filter by gender (M/F/O)", type=openapi.TYPE_STRING),
            openapi.Parameter('is_featured', openapi.IN_QUERY, description="Filter by featured status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_verified', openapi.IN_QUERY, description="Filter by user verification", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('funding_min', openapi.IN_QUERY, description="Minimum funding required", type=openapi.TYPE_NUMBER),
            openapi.Parameter('funding_max', openapi.IN_QUERY, description="Maximum funding required", type=openapi.TYPE_NUMBER),
            openapi.Parameter('created_after', openapi.IN_QUERY, description="Created after date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_before', openapi.IN_QUERY, description="Created before date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in name, email, diagnosis, medical partner, country", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING),
        ],
        responses={200: AdminPatientManagementSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Create New Patient",
        operation_description="Create a new patient profile with associated user account.",
        tags=['Admin - Patient Review & Management'],
        request_body=AdminPatientCreateSerializer,
        responses={
            201: AdminPatientManagementSerializer,
            400: 'Validation Error'
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = PatientProfile.objects.select_related(
            'user', 'country_fk'
        ).prefetch_related(
            'cost_breakdowns', 'timeline_events'
        )
        
        # Apply filters
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country_fk_id=country)
        
        gender = self.request.query_params.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(user__is_verified=is_verified.lower() == 'true')
        
        funding_min = self.request.query_params.get('funding_min')
        if funding_min:
            queryset = queryset.filter(funding_required__gte=funding_min)
        
        funding_max = self.request.query_params.get('funding_max')
        if funding_max:
            queryset = queryset.filter(funding_required__lte=funding_max)
        
        created_after = self.request.query_params.get('created_after')
        if created_after:
            queryset = queryset.filter(created_at__date__gte=created_after)
        
        created_before = self.request.query_params.get('created_before')
        if created_before:
            queryset = queryset.filter(created_at__date__lte=created_before)
        
        return queryset


class AdminPatientManagementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint for individual patient management.
    GET: Retrieve patient details
    PUT/PATCH: Update patient information
    DELETE: Delete patient profile
    """
    serializer_class = AdminPatientManagementSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Get Patient Details",
        operation_description="Retrieve detailed information for a specific patient.",
        tags=['Admin - Patient Review & Management'],
        responses={
            200: AdminPatientManagementSerializer,
            404: 'Patient not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Update Patient",
        operation_description="Update patient profile information.",
        tags=['Admin - Patient Review & Management'],
        request_body=AdminPatientManagementSerializer,
        responses={
            200: AdminPatientManagementSerializer,
            400: 'Validation Error',
            404: 'Patient not found'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Partial Update Patient",
        operation_description="Partially update patient profile information.",
        tags=['Admin - Patient Review & Management'],
        request_body=AdminPatientManagementSerializer,
        responses={
            200: AdminPatientManagementSerializer,
            400: 'Validation Error',
            404: 'Patient not found'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Delete Patient",
        operation_description="Delete a patient profile and associated user account.",
        tags=['Admin - Patient Review & Management'],
        responses={
            204: 'Patient deleted successfully',
            404: 'Patient not found'
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def perform_destroy(self, instance):
        # Delete associated user account as well
        user = instance.user
        instance.delete()
        user.delete()
    
    def get_queryset(self):
        return PatientProfile.objects.select_related(
            'user', 'country_fk'
        ).prefetch_related(
            'cost_breakdowns', 'timeline_events'
        )


class AdminPatientBulkActionView(APIView):
    """
    Admin endpoint for bulk actions on multiple patients.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Bulk Patient Actions",
        operation_description="Perform bulk actions on multiple patient profiles (approve, reject, publish, etc.).",
        tags=['Admin - Patient Review & Management'],
        request_body=AdminPatientBulkActionSerializer,
        responses={
            200: openapi.Response(
                description="Bulk action completed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'affected_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                    }
                )
            ),
            400: 'Validation Error'
        }
    )
    def post(self, request):
        serializer = AdminPatientBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        patient_ids = serializer.validated_data['patient_ids']
        action = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        
        # Get patients
        patients = PatientProfile.objects.filter(id__in=patient_ids)
        if not patients.exists():
            return Response({
                'success': False,
                'message': 'No patients found with provided IDs'
            }, status=status.HTTP_404_NOT_FOUND)
        
        results = []
        affected_count = 0
        
        for patient in patients:
            try:
                if action == 'approve':
                    patient.status = 'SCHEDULED'
                    patient.save()
                    results.append({'patient_id': patient.id, 'status': 'approved'})
                    affected_count += 1
                    
                elif action == 'reject':
                    patient.status = 'SUBMITTED'
                    patient.rejection_reason = reason
                    patient.save()
                    results.append({'patient_id': patient.id, 'status': 'rejected'})
                    affected_count += 1
                    
                elif action == 'publish':
                    patient.status = 'PUBLISHED'
                    patient.save()
                    results.append({'patient_id': patient.id, 'status': 'published'})
                    affected_count += 1
                    
                elif action == 'unpublish':
                    patient.status = 'SCHEDULED'
                    patient.save()
                    results.append({'patient_id': patient.id, 'status': 'unpublished'})
                    affected_count += 1
                    
                elif action == 'feature':
                    patient.is_featured = True
                    patient.save()
                    results.append({'patient_id': patient.id, 'status': 'featured'})
                    affected_count += 1
                    
                elif action == 'unfeature':
                    patient.is_featured = False
                    patient.save()
                    results.append({'patient_id': patient.id, 'status': 'unfeatured'})
                    affected_count += 1
                    
                elif action == 'delete':
                    user = patient.user
                    patient.delete()
                    user.delete()
                    results.append({'patient_id': patient.id, 'status': 'deleted'})
                    affected_count += 1
                    
            except Exception as e:
                results.append({'patient_id': patient.id, 'status': 'error', 'error': str(e)})
        
        return Response({
            'success': True,
            'message': f'Bulk {action} completed',
            'affected_count': affected_count,
            'results': results
        })


class AdminPatientStatsView(APIView):
    """
    Admin endpoint for patient statistics and dashboard data.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Patient Statistics",
        operation_description="Get comprehensive patient statistics for admin dashboard.",
        tags=['Admin - Patient Review & Management'],
        responses={200: AdminPatientStatsSerializer}
    )
    def get(self, request):
        from django.db.models import Count, Sum, Avg
        from datetime import timedelta
        
        # Basic counts
        total_patients = PatientProfile.objects.count()
        submitted_patients = PatientProfile.objects.filter(status='SUBMITTED').count()
        published_patients = PatientProfile.objects.filter(status='PUBLISHED').count()
        fully_funded_patients = PatientProfile.objects.filter(status='FULLY_FUNDED').count()
        featured_patients = PatientProfile.objects.filter(is_featured=True).count()
        
        # Funding statistics
        funding_stats = PatientProfile.objects.aggregate(
            total_required=Sum('funding_required'),
            total_received=Sum('funding_received'),
            avg_percentage=Avg('funding_received') * 100 / Avg('funding_required') if PatientProfile.objects.exists() else 0
        )
        
        # Patients by country
        patients_by_country = dict(
            PatientProfile.objects.values('country_fk__name')
            .annotate(count=Count('id'))
            .values_list('country_fk__name', 'count')
        )
        
        # Patients by status
        patients_by_status = dict(
            PatientProfile.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # Recent submissions (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_submissions = PatientProfile.objects.filter(created_at__gte=thirty_days_ago).count()
        
        stats_data = {
            'total_patients': total_patients,
            'submitted_patients': submitted_patients,
            'published_patients': published_patients,
            'fully_funded_patients': fully_funded_patients,
            'featured_patients': featured_patients,
            'total_funding_required': funding_stats['total_required'] or 0,
            'total_funding_received': funding_stats['total_received'] or 0,
            'average_funding_percentage': funding_stats['avg_percentage'] or 0,
            'patients_by_country': patients_by_country,
            'patients_by_status': patients_by_status,
            'recent_submissions': recent_submissions
        }
        
        serializer = AdminPatientStatsSerializer(stats_data)
        return Response(serializer.data)
