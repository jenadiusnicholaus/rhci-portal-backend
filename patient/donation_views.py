from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from auth_app.permissions import IsAdminUser
from .models import PatientProfile, DonationAmountOption
from .serializers import DonationAmountOptionSerializer, DonationAmountOptionCreateSerializer


# ============ PUBLIC/DONOR ENDPOINTS ============

class PatientDonationAmountsView(generics.ListAPIView):
    """
    Public endpoint to get suggested donation amounts for a patient.
    Used by donors when selecting donation amount.
    """
    serializer_class = DonationAmountOptionSerializer
    permission_classes = []  # Public access
    
    @swagger_auto_schema(
        operation_summary="Get Patient Donation Amount Options",
        operation_description="""
        Retrieve suggested donation amounts (quick-select buttons) for a specific patient.
        These are the pre-configured amounts that donors can quickly select when making a donation.
        
        Returns active donation options sorted by display order.
        """,
        tags=['Public - Patient Profiles'],
        responses={
            200: openapi.Response(
                description="List of donation amount options",
                schema=DonationAmountOptionSerializer(many=True)
            ),
            404: 'Patient not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return DonationAmountOption.objects.filter(
            patient_profile_id=patient_id,
            is_active=True
        ).order_by('display_order', 'amount')


# ============ ADMIN ENDPOINTS ============

class AdminDonationAmountListCreateView(generics.ListCreateAPIView):
    """
    Admin endpoint to list and create donation amount options for a patient.
    """
    serializer_class = DonationAmountOptionSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="List Patient Donation Amounts (Admin)",
        operation_description="Get all donation amount options configured for a specific patient, including inactive ones.",
        tags=['Admin - Patient Review & Management'],
        responses={
            200: DonationAmountOptionSerializer(many=True)
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Create Donation Amount Option (Admin)",
        operation_description="Add a new suggested donation amount for a patient.",
        tags=['Admin - Patient Review & Management'],
        request_body=DonationAmountOptionCreateSerializer,
        responses={
            201: DonationAmountOptionSerializer,
            400: 'Bad Request - Invalid data',
            404: 'Patient not found'
        }
    )
    def post(self, request, *args, **kwargs):
        patient_id = self.kwargs.get('patient_id')
        
        # Verify patient exists
        get_object_or_404(PatientProfile, id=patient_id)
        
        # Create serializer with patient_id
        serializer = DonationAmountOptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(patient_profile_id=patient_id)
        
        # Return with full serializer
        output_serializer = DonationAmountOptionSerializer(serializer.instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return DonationAmountOption.objects.filter(
            patient_profile_id=patient_id
        ).order_by('display_order', 'amount')


class AdminDonationAmountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to retrieve, update, or delete a specific donation amount option.
    """
    serializer_class = DonationAmountOptionSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_summary="Get Donation Amount Details (Admin)",
        operation_description="Retrieve details of a specific donation amount option.",
        tags=['Admin - Patient Review & Management'],
        responses={
            200: DonationAmountOptionSerializer,
            404: 'Not Found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update Donation Amount (Admin)",
        operation_description="Update a donation amount option (amount, order, active status, etc.).",
        tags=['Admin - Patient Review & Management'],
        request_body=DonationAmountOptionCreateSerializer,
        responses={
            200: DonationAmountOptionSerializer,
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Partially Update Donation Amount (Admin)",
        operation_description="Partially update a donation amount option.",
        tags=['Admin - Patient Review & Management'],
        request_body=DonationAmountOptionCreateSerializer,
        responses={
            200: DonationAmountOptionSerializer,
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete Donation Amount (Admin)",
        operation_description="Delete a donation amount option.",
        tags=['Admin - Patient Review & Management'],
        responses={
            204: 'Deleted successfully',
            404: 'Not Found'
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return DonationAmountOption.objects.filter(patient_profile_id=patient_id)


class AdminBulkCreateDonationAmountsView(APIView):
    """
    Admin endpoint to bulk create default donation amounts for a patient.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Bulk Create Default Donation Amounts (Admin)",
        operation_description="""
        Automatically generate 4 smart donation amount options for a patient based on their remaining funding.
        
        Calculations:
        - Option 1: ~1% of remaining (smallest amount)
        - Option 2: ~3% of remaining
        - Option 3: ~5% of remaining
        - Option 4: ~15% of remaining (marked as recommended)
        
        Amounts are rounded to nearest $5 or $10 for clean values.
        """,
        tags=['Admin - Patient Review & Management'],
        responses={
            201: openapi.Response(
                description="Donation amounts created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'created_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'amounts': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            ),
            404: 'Patient not found',
            400: 'Patient has no remaining funding'
        }
    )
    def post(self, request, patient_id):
        from decimal import Decimal
        
        # Get patient
        patient = get_object_or_404(PatientProfile, id=patient_id)
        
        # Calculate remaining funding
        remaining = patient.funding_required - patient.funding_received
        
        if remaining <= 0:
            return Response(
                {'error': 'Patient has no remaining funding to configure donation amounts'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clear existing amounts (optional - can be made configurable)
        DonationAmountOption.objects.filter(patient_profile=patient).delete()
        
        # Create 4 suggested amounts
        amounts = [
            (remaining * Decimal('0.01'), 1, False),  # ~1% of remaining
            (remaining * Decimal('0.03'), 2, False),  # ~3% of remaining
            (remaining * Decimal('0.05'), 3, False),  # ~5% of remaining
            (remaining * Decimal('0.15'), 4, True),   # ~15% of remaining (recommended)
        ]
        
        created_options = []
        for amount, order, is_recommended in amounts:
            # Round to nearest $5 or $10
            if amount < 50:
                rounded_amount = round(amount / 5) * 5
            else:
                rounded_amount = round(amount / 10) * 10
            
            if rounded_amount > 0:
                option = DonationAmountOption.objects.create(
                    patient_profile=patient,
                    amount=Decimal(str(rounded_amount)),
                    display_order=order,
                    is_active=True,
                    is_recommended=is_recommended
                )
                created_options.append(option)
        
        # Serialize results
        serializer = DonationAmountOptionSerializer(created_options, many=True)
        
        return Response({
            'message': f'Created {len(created_options)} donation amount options',
            'created_count': len(created_options),
            'amounts': serializer.data
        }, status=status.HTTP_201_CREATED)
