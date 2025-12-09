"""
Separate Donation APIs by Type and Authentication
- One-time donations
- Monthly recurring donations
- Organization donations
- Patient-specific donations
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db import transaction as db_transaction
from django.conf import settings
from decimal import Decimal
import logging
from dateutil.relativedelta import relativedelta

from donor.models import Donation
from .azampay_service import azampay_service, AzamPayError
from patient.models import PatientProfile

logger = logging.getLogger(__name__)


# ============================================
# ONE-TIME PATIENT DONATIONS
# ============================================

class AnonymousOneTimePatientDonationView(APIView):
    """🔓 Anonymous One-Time Patient Donation"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['🔴 Donations - One-Time Patient'],
        operation_summary="🔓 Anonymous One-Time Patient Donation",
        operation_description="Make a one-time donation to a specific patient without login.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['patient_id', 'amount', 'anonymous_name', 'anonymous_email', 'payment_method', 'provider'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Patient ID (required)'),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=50.00),
                'anonymous_name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe'),
                'anonymous_email': openapi.Schema(type=openapi.TYPE_STRING, example='john@example.com'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='Get well soon!'),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING, description='mpesa, airtel, tigo, halopesa, azampesa, crdb, nmb'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, example='0789123456'),
                'merchant_account_number': openapi.Schema(type=openapi.TYPE_STRING),
                'merchant_mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Payment initiated', 400: 'Validation error', 404: 'Patient not found'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=False, is_recurring=False, require_patient=True)
    
    def _process_donation(self, request, is_authenticated, is_recurring, require_patient):
        try:
            # Validate required fields
            amount = request.data.get('amount')
            payment_method = request.data.get('payment_method')
            provider = request.data.get('provider')
            patient_id = request.data.get('patient_id')
            
            if not all([amount, payment_method, provider]):
                return Response({'error': 'Required: amount, payment_method, provider'}, status=status.HTTP_400_BAD_REQUEST)
            
            if require_patient and not patient_id:
                return Response({'error': 'patient_id is required for patient-specific donations'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Anonymous validation
            if not is_authenticated:
                anonymous_name = request.data.get('anonymous_name')
                anonymous_email = request.data.get('anonymous_email')
                if not all([anonymous_name, anonymous_email]):
                    return Response({'error': 'Required: anonymous_name, anonymous_email'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Payment method validation
            if payment_method == 'MOBILE_MONEY' and not request.data.get('phone_number'):
                return Response({'error': 'phone_number required for mobile money'}, status=status.HTTP_400_BAD_REQUEST)
            
            if payment_method == 'BANK':
                if not all([request.data.get('merchant_account_number'), request.data.get('merchant_mobile_number'), request.data.get('otp')]):
                    return Response({'error': 'Bank payment requires: merchant_account_number, merchant_mobile_number, otp'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get patient if ID provided
            patient = None
            if patient_id:
                try:
                    patient = PatientProfile.objects.get(id=patient_id)
                except PatientProfile.DoesNotExist:
                    return Response({'error': f'Patient {patient_id} not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Create donation
            donation_type = 'MONTHLY' if is_recurring else 'ONE_TIME'
            
            with db_transaction.atomic():
                donation_data = {
                    'amount': Decimal(str(amount)),
                    'donation_type': donation_type,
                    'status': 'PENDING',
                    'message': request.data.get('message', ''),
                    'patient': patient,
                    'is_recurring_active': is_recurring,
                    'recurring_frequency': 1,  # Default to 1 (monthly) even for one-time
                    'next_charge_date': (timezone.now() + relativedelta(months=1)).date() if is_recurring else None,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
                
                if is_authenticated:
                    donation_data['donor'] = request.user
                    donation_data['is_anonymous'] = False
                else:
                    donation_data['donor'] = None
                    donation_data['is_anonymous'] = True
                    donation_data['anonymous_name'] = request.data.get('anonymous_name')
                    donation_data['anonymous_email'] = request.data.get('anonymous_email')
                
                donation = Donation.objects.create(**donation_data)
                logger.info(f"Created {'recurring' if is_recurring else 'one-time'} donation {donation.id}")
            
            # Initiate payment
            payment_amount = donation.amount * Decimal('2300')
            external_id = f"RHCI-DN-{donation.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            donor_info = {
                'donation_id': donation.id,
                'patient_id': patient.id if patient else None,
                'patient_name': patient.full_name if patient else "General Organization",
                'is_anonymous': not is_authenticated,
                'donation_type': donation_type,
            }
            
            if is_authenticated:
                donor_info.update({
                    'donor_id': request.user.id,
                    'donor_email': request.user.email,
                    'donor_name': request.user.get_full_name() or request.user.email,
                })
            else:
                donor_info.update({
                    'donor_email': request.data.get('anonymous_email'),
                    'donor_name': request.data.get('anonymous_name'),
                })
            
            if payment_method == 'MOBILE_MONEY':
                success, response_data = azampay_service.initiate_checkout(
                    amount=payment_amount,
                    currency='TZS',
                    external_id=external_id,
                    provider=provider,
                    account_number=request.data.get('phone_number'),
                    additional_properties=donor_info
                )
            else:
                success, response_data = azampay_service.initiate_bank_checkout(
                    amount=payment_amount,
                    currency='TZS',
                    external_id=external_id,
                    provider=provider,
                    merchant_account_number=request.data.get('merchant_account_number'),
                    merchant_mobile_number=request.data.get('merchant_mobile_number'),
                    otp=request.data.get('otp'),
                    additional_properties=donor_info
                )
            
            if success:
                donation.payment_method = f"{'Mobile Money' if payment_method == 'MOBILE_MONEY' else 'Bank Transfer'} - {provider.title()}"
                donation.payment_gateway = 'Azam Pay'
                donation.transaction_id = response_data.get('data', {}).get('transactionId', external_id)
                
                # Auto-complete payment in sandbox environment
                # In sandbox, AzamPay doesn't send webhooks, so we complete immediately
                if settings.AZAM_PAY_ENVIRONMENT == 'sandbox':
                    donation.status = 'COMPLETED'
                    donation.completed_at = timezone.now()
                    
                    # Update patient funding
                    if patient:
                        patient.funding_received += donation.amount
                        if patient.funding_received >= patient.funding_required:
                            patient.status = 'FULLY_FUNDED'
                        patient.save()
                        logger.info(f"🎉 Sandbox auto-complete: Donation {donation.id} completed, patient {patient.id} funding: {patient.funding_received}/{patient.funding_required}")
                    else:
                        logger.info(f"🎉 Sandbox auto-complete: Organization donation {donation.id} completed")
                
                donation.save()
                
                message = 'Payment initiated. Check your phone to confirm.' if payment_method == 'MOBILE_MONEY' else 'Bank payment processing.'
                if settings.AZAM_PAY_ENVIRONMENT == 'sandbox':
                    message = '✅ Payment completed successfully (sandbox mode - auto-completed)'
                
                response_data = {
                    'success': True,
                    'message': message,
                    'donation': {
                        'id': donation.id,
                        'status': donation.status,
                        'amount': str(donation.amount),
                        'patient_id': patient.id if patient else None,
                        'patient_name': patient.full_name if patient else "General Organization",
                        'donation_type': donation_type,
                        'is_anonymous': not is_authenticated,
                        'completed_at': donation.completed_at.isoformat() if donation.completed_at else None,
                    },
                    'payment': {
                        'transaction_id': donation.transaction_id,
                        'amount': str(payment_amount),
                        'currency': 'TZS',
                        'provider': provider,
                    }
                }
                
                if is_authenticated:
                    response_data['donation'].update({
                        'donor_name': request.user.get_full_name() or request.user.email,
                        'is_recurring': is_recurring,
                        'next_charge_date': str(donation.next_charge_date) if donation.next_charge_date else None,
                    })
                
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                donation.status = 'FAILED'
                donation.save()
                return Response({'error': 'Payment failed', 'details': response_data.get('error')}, status=status.HTTP_400_BAD_REQUEST)
        
        except AzamPayError as e:
            if 'donation' in locals():
                donation.status = 'FAILED'
                donation.save()
            return Response({'error': e.message, 'error_code': e.error_code}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Donation error: {str(e)}", exc_info=True)
            if 'donation' in locals():
                donation.status = 'FAILED'
                donation.save()
            return Response({'error': 'Payment processing error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuthenticatedOneTimePatientDonationView(AnonymousOneTimePatientDonationView):
    """🔐 Authenticated One-Time Patient Donation"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['🔴 Donations - One-Time Patient'],
        operation_summary="🔐 Authenticated One-Time Patient Donation",
        operation_description="Make a one-time donation to a specific patient with your account.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['patient_id', 'amount', 'payment_method', 'provider'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Patient ID (required)'),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=100.00),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='Best wishes!'),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, example='0789123456'),
                'merchant_account_number': openapi.Schema(type=openapi.TYPE_STRING),
                'merchant_mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Payment initiated', 401: 'Not authenticated'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=True, is_recurring=False, require_patient=True)


# ============================================
# MONTHLY RECURRING PATIENT DONATIONS
# ============================================

class AnonymousMonthlyPatientDonationView(AnonymousOneTimePatientDonationView):
    """🔓 Anonymous Monthly Patient Donation"""
    
    @swagger_auto_schema(
        tags=['🔴 Donations - Monthly Recurring'],
        operation_summary="🔓 Anonymous Monthly Patient Donation",
        operation_description="Set up monthly recurring donation to a patient without login.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['patient_id', 'amount', 'anonymous_name', 'anonymous_email', 'payment_method', 'provider'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=50.00),
                'anonymous_name': openapi.Schema(type=openapi.TYPE_STRING),
                'anonymous_email': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Monthly donation set up'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=False, is_recurring=True, require_patient=True)


class AuthenticatedMonthlyPatientDonationView(AnonymousOneTimePatientDonationView):
    """🔐 Authenticated Monthly Patient Donation"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['🔴 Donations - Monthly Recurring'],
        operation_summary="🔐 Authenticated Monthly Patient Donation",
        operation_description="Set up monthly recurring donation to a patient with your account.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['patient_id', 'amount', 'payment_method', 'provider'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=100.00),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Monthly donation set up', 401: 'Not authenticated'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=True, is_recurring=True, require_patient=True)


# ============================================
# ORGANIZATION DONATIONS (NO PATIENT)
# ============================================

class AnonymousOrganizationDonationView(AnonymousOneTimePatientDonationView):
    """🔓 Anonymous Organization Donation"""
    
    @swagger_auto_schema(
        tags=['🔴 Donations - Organization'],
        operation_summary="🔓 Anonymous Organization Donation",
        operation_description="Make a one-time donation to the organization without login.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'anonymous_name', 'anonymous_email', 'payment_method', 'provider'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=100.00),
                'anonymous_name': openapi.Schema(type=openapi.TYPE_STRING),
                'anonymous_email': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='For the organization'),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Organization donation processed'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=False, is_recurring=False, require_patient=False)


class AuthenticatedOrganizationDonationView(AnonymousOneTimePatientDonationView):
    """🔐 Authenticated Organization Donation"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['🔴 Donations - Organization'],
        operation_summary="🔐 Authenticated Organization Donation",
        operation_description="Make a one-time donation to the organization with your account.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'payment_method', 'provider'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=200.00),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Organization donation processed', 401: 'Not authenticated'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=True, is_recurring=False, require_patient=False)


class AnonymousMonthlyOrganizationDonationView(AnonymousOneTimePatientDonationView):
    """🔓 Anonymous Monthly Organization Donation"""
    
    @swagger_auto_schema(
        tags=['🔴 Donations - Organization'],
        operation_summary="🔓 Anonymous Monthly Organization Donation",
        operation_description="Set up monthly recurring donation to the organization without login.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'anonymous_name', 'anonymous_email', 'payment_method', 'provider'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=50.00),
                'anonymous_name': openapi.Schema(type=openapi.TYPE_STRING),
                'anonymous_email': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Monthly organization donation set up'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=False, is_recurring=True, require_patient=False)


class AuthenticatedMonthlyOrganizationDonationView(AnonymousOneTimePatientDonationView):
    """🔐 Authenticated Monthly Organization Donation"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['🔴 Donations - Organization'],
        operation_summary="🔐 Authenticated Monthly Organization Donation",
        operation_description="Set up monthly recurring donation to the organization with your account.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'payment_method', 'provider'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, example=100.00),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, enum=['MOBILE_MONEY', 'BANK']),
                'provider': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: 'Monthly organization donation set up', 401: 'Not authenticated'}
    )
    def post(self, request):
        return self._process_donation(request, is_authenticated=True, is_recurring=True, require_patient=False)
