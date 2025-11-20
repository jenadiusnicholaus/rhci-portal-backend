from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Campaign, CampaignPhoto, CampaignUpdate, PaymentMethod
from .serializers import (
    CampaignCreateSerializer,
    CampaignSerializer,
    CampaignDetailSerializer,
    CampaignPhotoSerializer,
    CampaignUpdateSerializer,
    PaymentMethodSerializer,
    AdminPaymentMethodSerializer
)


# ============ PUBLIC CAMPAIGN VIEWS ============

class PublicCampaignListView(generics.ListAPIView):
    """
    List all active campaigns (public)
    """
    serializer_class = CampaignSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Campaigns (Public)'],
        operation_summary="List Active Campaigns",
        operation_description="""
        Browse all active campaigns.
        
        **Public Access**
        
        **Filtering:**
        - Only shows ACTIVE campaigns
        - Ordered by creation date (newest first)
        """,
        responses={
            200: openapi.Response(
                description="List of active campaigns",
                schema=CampaignSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Campaign.objects.filter(status='ACTIVE').prefetch_related('photos', 'payment_methods')


class PublicCampaignDetailView(generics.RetrieveAPIView):
    """
    View campaign details (public)
    """
    serializer_class = CampaignSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        tags=['Campaigns (Public)'],
        operation_summary="View Campaign Details",
        operation_description="""
        View detailed information about a campaign.
        
        **Public Access**
        
        **Includes:**
        - Campaign details
        - Payment methods (set by RHCI admin)
        - Photos
        - Updates
        """,
        responses={
            200: openapi.Response(
                description="Campaign details",
                schema=CampaignSerializer
            ),
            404: "Campaign not found"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Campaign.objects.filter(status='ACTIVE').prefetch_related('photos', 'payment_methods', 'updates')


# ============ CAMPAIGN LAUNCHER VIEWS ============

class MyCampaignsView(generics.ListAPIView):
    """
    List authenticated user's campaigns
    """
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Campaigns (Launcher)'],
        operation_summary="My Campaigns",
        operation_description="""
        List all campaigns created by authenticated user.
        
        **Authenticated Only**
        """,
        responses={
            200: openapi.Response(
                description="List of user's campaigns",
                schema=CampaignSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Campaign.objects.filter(launcher=self.request.user).prefetch_related('photos', 'payment_methods')


class CreateCampaignView(generics.CreateAPIView):
    """
    Create a new campaign
    """
    serializer_class = CampaignCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Campaigns (Launcher)'],
        operation_summary="Create Campaign",
        operation_description="""
        Create a new campaign.
        
        **Authenticated Only**
        
        **Note:**
        - Campaign starts in DRAFT status
        - Submit for review to change to PENDING_REVIEW
        - Payment methods are assigned by RHCI admin after approval
        - Campaign launcher CANNOT set payment methods
        """,
        responses={
            201: openapi.Response(
                description="Campaign created successfully",
                schema=CampaignSerializer
            ),
            400: "Validation error"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create campaign with launcher as current user
        campaign = serializer.save(launcher=request.user, status='DRAFT')
        
        response_serializer = CampaignSerializer(campaign)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UpdateCampaignView(generics.UpdateAPIView):
    """
    Update own campaign
    """
    serializer_class = CampaignCreateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        tags=['Campaigns (Launcher)'],
        operation_summary="Update Campaign",
        operation_description="""
        Update own campaign.
        
        **Authenticated Only**
        
        **Note:**
        - Can only update own campaigns
        - Can only update campaigns in DRAFT or REJECTED status
        - Cannot modify payment methods (admin only)
        """,
        responses={
            200: openapi.Response(
                description="Campaign updated successfully",
                schema=CampaignSerializer
            ),
            403: "Cannot update this campaign",
            404: "Campaign not found"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Can only update own campaigns in DRAFT or REJECTED status
        return Campaign.objects.filter(
            launcher=self.request.user,
            status__in=['DRAFT', 'REJECTED']
        )


class SubmitCampaignForReviewView(APIView):
    """
    Submit campaign for admin review
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Campaigns (Launcher)'],
        operation_summary="Submit Campaign for Review",
        operation_description="""
        Submit campaign for admin review.
        
        **Authenticated Only**
        
        **Changes status from DRAFT to PENDING_REVIEW**
        """,
        responses={
            200: "Campaign submitted for review",
            400: "Campaign cannot be submitted"
        }
    )
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id, launcher=request.user)
        
        if campaign.status != 'DRAFT':
            return Response(
                {"error": "Only DRAFT campaigns can be submitted for review"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'PENDING_REVIEW'
        campaign.save()
        
        serializer = CampaignSerializer(campaign)
        return Response(serializer.data)


class UploadCampaignPhotoView(generics.CreateAPIView):
    """
    Upload photo to campaign
    """
    serializer_class = CampaignPhotoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        tags=['Campaigns (Launcher)'],
        operation_summary="Upload Campaign Photo",
        operation_description="""
        Upload a photo to campaign.
        
        **Authenticated Only**
        
        **Can only upload to own campaigns**
        """,
        responses={
            201: openapi.Response(
                description="Photo uploaded successfully",
                schema=CampaignPhotoSerializer
            )
        }
    )
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id, launcher=request.user)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(campaign=campaign)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostCampaignUpdateView(generics.CreateAPIView):
    """
    Post update to campaign
    """
    serializer_class = CampaignUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Campaigns (Launcher)'],
        operation_summary="Post Campaign Update",
        operation_description="""
        Post an update to campaign.
        
        **Authenticated Only**
        
        **Can only post to own campaigns**
        """,
        responses={
            201: openapi.Response(
                description="Update posted successfully",
                schema=CampaignUpdateSerializer
            )
        }
    )
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id, launcher=request.user)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(campaign=campaign, author=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============ ADMIN CAMPAIGN VIEWS ============

class AdminCampaignListView(generics.ListAPIView):
    """
    Admin: List all campaigns
    """
    serializer_class = CampaignDetailSerializer
    permission_classes = [IsAdminUser]
    queryset = Campaign.objects.all().prefetch_related('photos', 'payment_methods').order_by('-created_at')
    
    @swagger_auto_schema(
        tags=['Admin - Campaigns'],
        operation_summary="List All Campaigns (Admin)",
        operation_description="""
        List all campaigns in the system.
        
        **Admin Only**
        
        **Filtering Options:**
        - Filter by status
        """,
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by status"),
        ],
        responses={
            200: openapi.Response(
                description="List of all campaigns",
                schema=CampaignDetailSerializer(many=True)
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
        
        return queryset


class AdminCampaignDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin: Get or update campaign
    """
    serializer_class = CampaignDetailSerializer
    permission_classes = [IsAdminUser]
    queryset = Campaign.objects.all().prefetch_related('photos', 'payment_methods')
    lookup_field = 'id'
    
    @swagger_auto_schema(
        tags=['Admin - Campaigns'],
        operation_summary="Get/Update Campaign (Admin)",
        operation_description="""
        Get or update campaign details.
        
        **Admin Only**
        
        **Can update:**
        - Status
        - Payment methods
        - Admin notes
        - Rejection reason
        """,
        responses={
            200: openapi.Response(
                description="Campaign details",
                schema=CampaignDetailSerializer
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Admin - Campaigns'],
        operation_summary="Update Campaign (Admin)"
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class AdminApproveCampaignView(APIView):
    """
    Admin: Approve campaign and assign payment methods
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        tags=['Admin - Campaigns'],
        operation_summary="Approve Campaign (Admin)",
        operation_description="""
        Approve campaign and assign payment methods.
        
        **Admin Only**
        
        **Required:**
        - payment_method_ids: Array of payment method IDs
        
        **Changes status to APPROVED**
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['payment_method_ids'],
            properties={
                'payment_method_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='Array of payment method IDs'
                )
            }
        ),
        responses={
            200: "Campaign approved",
            400: "Invalid request"
        }
    )
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        
        if campaign.status != 'PENDING_REVIEW':
            return Response(
                {"error": "Only PENDING_REVIEW campaigns can be approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_method_ids = request.data.get('payment_method_ids', [])
        if not payment_method_ids:
            return Response(
                {"error": "At least one payment method must be assigned"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate payment methods exist
        payment_methods = PaymentMethod.objects.filter(id__in=payment_method_ids, is_active=True)
        if payment_methods.count() != len(payment_method_ids):
            return Response(
                {"error": "Invalid payment method IDs"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Approve campaign and assign payment methods
        campaign.status = 'APPROVED'
        campaign.approved_by = request.user
        campaign.approved_at = timezone.now()
        campaign.save()
        
        campaign.payment_methods.set(payment_methods)
        
        serializer = CampaignDetailSerializer(campaign)
        return Response(serializer.data)


class AdminRejectCampaignView(APIView):
    """
    Admin: Reject campaign
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        tags=['Admin - Campaigns'],
        operation_summary="Reject Campaign (Admin)",
        operation_description="""
        Reject campaign with reason.
        
        **Admin Only**
        
        **Required:**
        - rejection_reason: Reason for rejection
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['rejection_reason'],
            properties={
                'rejection_reason': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            200: "Campaign rejected"
        }
    )
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        
        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response(
                {"error": "Rejection reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'REJECTED'
        campaign.rejection_reason = rejection_reason
        campaign.save()
        
        serializer = CampaignDetailSerializer(campaign)
        return Response(serializer.data)


class AdminActivateCampaignView(APIView):
    """
    Admin: Activate approved campaign
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        tags=['Admin - Campaigns'],
        operation_summary="Activate Campaign (Admin)",
        operation_description="""
        Activate approved campaign to make it publicly visible.
        
        **Admin Only**
        """,
        responses={
            200: "Campaign activated"
        }
    )
    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        
        if campaign.status != 'APPROVED':
            return Response(
                {"error": "Only APPROVED campaigns can be activated"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'ACTIVE'
        campaign.save()
        
        serializer = CampaignDetailSerializer(campaign)
        return Response(serializer.data)


# ============ ADMIN PAYMENT METHOD VIEWS ============

class AdminPaymentMethodListCreateView(generics.ListCreateAPIView):
    """
    Admin: List or create payment methods
    """
    serializer_class = AdminPaymentMethodSerializer
    permission_classes = [IsAdminUser]
    queryset = PaymentMethod.objects.all().order_by('display_order', 'name')
    
    @swagger_auto_schema(
        tags=['Admin - Payment Methods'],
        operation_summary="List Payment Methods (Admin)",
        operation_description="""
        List all payment methods.
        
        **Admin Only**
        """,
        responses={
            200: openapi.Response(
                description="List of payment methods",
                schema=AdminPaymentMethodSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Admin - Payment Methods'],
        operation_summary="Create Payment Method (Admin)",
        operation_description="""
        Create a new payment method.
        
        **Admin Only**
        """,
        responses={
            201: openapi.Response(
                description="Payment method created",
                schema=AdminPaymentMethodSerializer
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminPaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin: Get, update, or delete payment method
    """
    serializer_class = AdminPaymentMethodSerializer
    permission_classes = [IsAdminUser]
    queryset = PaymentMethod.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        tags=['Admin - Payment Methods'],
        operation_summary="Get Payment Method (Admin)"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Admin - Payment Methods'],
        operation_summary="Update Payment Method (Admin)"
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Admin - Payment Methods'],
        operation_summary="Delete Payment Method (Admin)"
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
