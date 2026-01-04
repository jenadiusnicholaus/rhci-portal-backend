from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import CustomUser
from patient.models import PatientProfile, PatientTimeline
from .serializers import (
    AdminPatientReviewSerializer,
    AdminPatientApprovalSerializer,
    AdminPatientPublishSerializer,
    AdminTimelineEventSerializer,
    PatientProfileSerializer
)
from .permissions import IsAdminUser
from .exceptions import PatientProfileNotFoundException


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


# ============ FINANCIAL REPORTS VIEWS ============

class AdminFinancialReportListCreateView(generics.ListCreateAPIView):
    """
    Admin endpoint to list all financial reports and upload new ones.
    """
    from .models import FinancialReport
    from .serializers import FinancialReportSerializer
    
    queryset = FinancialReport.objects.all()
    serializer_class = FinancialReportSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] List & Upload Financial Reports",
        operation_description="""
        List all financial reports or upload a new one.
        
        **Upload Process:**
        1. Upload Excel/PDF document using base64 encoding
        2. Provide title and optional description
        3. Mark as public for community transparency (only one can be public at a time)
        
        **Allowed File Types:** PDF, XLSX, XLS, DOC, DOCX
        **Max File Size:** 20MB
        """,
        tags=['Admin - Financial Reports'],
        responses={
            200: FinancialReportSerializer(many=True),
            201: FinancialReportSerializer,
            400: 'Bad Request - Invalid file or data',
            401: 'Unauthorized',
            403: 'Forbidden - Admin access required'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Upload Financial Report",
        tags=['Admin - Financial Reports'],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminFinancialReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to view, update, or delete a financial report.
    """
    from .models import FinancialReport
    from .serializers import FinancialReportSerializer
    
    queryset = FinancialReport.objects.all()
    serializer_class = FinancialReportSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Get Financial Report Details",
        operation_description="Retrieve detailed information about a specific financial report.",
        tags=['Admin - Financial Reports'],
        responses={
            200: FinancialReportSerializer,
            404: 'Not Found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Update Financial Report",
        operation_description="Update report title, description, or mark as public/private. Document can also be replaced.",
        tags=['Admin - Financial Reports'],
        responses={
            200: FinancialReportSerializer,
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Partial Update Financial Report",
        tags=['Admin - Financial Reports'],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="[ADMIN] Delete Financial Report",
        operation_description="Permanently delete a financial report and its document.",
        tags=['Admin - Financial Reports'],
        responses={
            204: 'No Content - Successfully deleted',
            404: 'Not Found'
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class PublicFinancialReportView(generics.RetrieveAPIView):
    """
    Public endpoint to view the currently published financial report.
    Only shows the report marked as public.
    """
    from .models import FinancialReport
    from .serializers import PublicFinancialReportSerializer
    
    serializer_class = PublicFinancialReportSerializer
    permission_classes = []  # Public access
    
    @swagger_auto_schema(
        operation_summary="Public Financial Report (Transparency)",
        operation_description="""
        View the current public financial report for community transparency.
        
        Returns the financial report that has been marked as public by admin.
        This allows donors and community members to see how funds are being used.
        """,
        tags=['Public - Transparency'],
        responses={
            200: PublicFinancialReportSerializer,
            404: 'Not Found - No public report available'
        }
    )
    def get(self, request, *args, **kwargs):
        from .models import FinancialReport
        
        # Get the public report
        public_report = FinancialReport.objects.filter(is_public=True).first()
        
        if not public_report:
            return Response(
                {'detail': 'No public financial report available at this time.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(public_report)
        return Response(serializer.data)
