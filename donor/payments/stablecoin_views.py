"""
Stablecoin (USDC / Solana) donation views.

Flow:
1. Frontend calls POST /donors/donate/usdc/patient/anonymous/ or /donate/usdc/patient/
2. Backend creates a PENDING Donation and returns the USDC collection address + donation ID.
3. Donor sends USDC to that address; the Pepea aggregator detects the on-chain payment
   and POSTs to /donors/webhooks/stablecoin/payment/ (handled in stablecoin_webhook.py).
4. Donation status is updated to COMPLETED.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import logging

from donor.models import Donation
from patient.models import PatientProfile

logger = logging.getLogger(__name__)


def _create_stablecoin_donation(request_data, donor_user=None):
    """
    Shared donation creation logic for both anonymous and authenticated flows.
    Returns (donation, error_response) — one will be None.
    """
    patient_id = request_data.get('patient_id')
    amount_raw = request_data.get('amount')
    message = request_data.get('message', '')
    dedication = request_data.get('dedication', '')
    anonymous_name = request_data.get('anonymous_name', '')
    anonymous_email = request_data.get('anonymous_email', '')

    # Validate amount
    if not amount_raw:
        return None, {'error': 'amount is required'}
    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            return None, {'error': 'amount must be greater than zero'}
    except InvalidOperation:
        return None, {'error': 'Invalid amount value'}

    # Resolve patient (optional — omit for general fund donation)
    patient = None
    if patient_id:
        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return None, {'error': f'Patient with id {patient_id} not found'}

    donation = Donation.objects.create(
        donor=donor_user,
        is_anonymous=(donor_user is None),
        anonymous_name=anonymous_name,
        anonymous_email=anonymous_email,
        patient=patient,
        amount=amount,
        patient_amount=amount,
        rhci_support_amount=Decimal('0.00'),
        currency='USD',
        donation_type='ONE_TIME',
        status='PENDING',
        payment_gateway='STABLECOIN_SOLANA',
        payment_method='USDC on Solana',
        message=message,
        dedication=dedication,
        ip_address=request_data.get('_ip_address'),
        user_agent=request_data.get('_user_agent', ''),
    )
    return donation, None


# ─────────────────────────────────────────────
# Shared Swagger schema
# ─────────────────────────────────────────────

_REQUEST_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['amount'],
    properties={
        'patient_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Patient ID (omit for general fund)'),
        'amount': openapi.Schema(type=openapi.TYPE_STRING, description='Amount in USDC (= USD)', example='25.00'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message to the patient'),
        'dedication': openapi.Schema(type=openapi.TYPE_STRING, description='Dedication note'),
        'anonymous_name': openapi.Schema(type=openapi.TYPE_STRING, description='Display name (anonymous only)'),
        'anonymous_email': openapi.Schema(type=openapi.TYPE_STRING, description='Email for receipt (anonymous only)'),
    },
)

_RESPONSE_200 = openapi.Response(
    description='Donation created — send USDC to the returned address',
    examples={
        'application/json': {
            'success': True,
            'donation_id': 42,
            'collection_address': '7xKX...abc',
            'amount_usdc': '25.00',
            'currency': 'USDC',
            'network': 'Solana',
            'memo': 'donation-42',
            'message': 'Send exactly 25.00 USDC on the Solana network to the address above.',
        }
    },
)


# ─────────────────────────────────────────────
# Anonymous donation
# ─────────────────────────────────────────────

class StablecoinAnonymousDonationView(APIView):
    """Create a USDC/Solana donation without authentication."""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=['Donations - Stablecoin'],
        operation_summary='Anonymous USDC / Solana Donation',
        request_body=_REQUEST_BODY,
        responses={200: _RESPONSE_200, 400: 'Validation error', 404: 'Patient not found'},
    )
    def post(self, request):
        try:
            data = dict(request.data)
            data['_ip_address'] = request.META.get('REMOTE_ADDR')
            data['_user_agent'] = request.META.get('HTTP_USER_AGENT', '')

            donation, error = _create_stablecoin_donation(data, donor_user=None)
            if error:
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            collection_address = getattr(settings, 'STABLECOIN_COLLECTION_ADDRESS', 'ASiECMRmktWqAmbqmXDYxT6mnW4ZMu65gQEJ45GeZeii')
            logger.info(f'✅ Stablecoin donation {donation.id} created (anonymous) — {donation.amount} USDC')

            return Response({
                'success': True,
                'donation_id': donation.id,
                'collection_address': collection_address,
                'amount_usdc': str(donation.amount),
                'currency': 'USDC',
                'network': 'Solana',
                'memo': f'donation-{donation.id}',
                'message': f'Send exactly {donation.amount} USDC on the Solana network to the address above.',
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Error creating anonymous stablecoin donation: {e}')
            return Response({'error': 'Failed to create donation', 'details': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# Authenticated donation
# ─────────────────────────────────────────────

class StablecoinAuthenticatedDonationView(APIView):
    """Create a USDC/Solana donation for a logged-in donor."""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Donations - Stablecoin'],
        operation_summary='Authenticated USDC / Solana Donation',
        request_body=_REQUEST_BODY,
        responses={200: _RESPONSE_200, 400: 'Validation error', 404: 'Patient not found'},
    )
    def post(self, request):
        try:
            data = dict(request.data)
            data['_ip_address'] = request.META.get('REMOTE_ADDR')
            data['_user_agent'] = request.META.get('HTTP_USER_AGENT', '')

            donation, error = _create_stablecoin_donation(data, donor_user=request.user)
            if error:
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            collection_address = getattr(settings, 'STABLECOIN_COLLECTION_ADDRESS', 'ASiECMRmktWqAmbqmXDYxT6mnW4ZMu65gQEJ45GeZeii')
            logger.info(f'✅ Stablecoin donation {donation.id} created (user {request.user.id}) — {donation.amount} USDC')

            return Response({
                'success': True,
                'donation_id': donation.id,
                'collection_address': collection_address,
                'amount_usdc': str(donation.amount),
                'currency': 'USDC',
                'network': 'Solana',
                'memo': f'donation-{donation.id}',
                'message': f'Send exactly {donation.amount} USDC on the Solana network to the address above.',
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Error creating authenticated stablecoin donation: {e}')
            return Response({'error': 'Failed to create donation', 'details': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
