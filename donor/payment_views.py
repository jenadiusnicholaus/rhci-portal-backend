"""
Payment views for Azam Pay integration
Handles donation payment processing via Azam Pay
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db import transaction as db_transaction
from decimal import Decimal
import logging

from .models import Donation
from .azampay_service import azampay_service
from patient.models import PatientProfile

logger = logging.getLogger(__name__)


class AzamPayMobileMoneyCheckoutView(APIView):
    """
    Initiate mobile money payment via Azam Pay
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Donations - Payment'],
        operation_summary="Azam Pay Mobile Money Checkout",
        operation_description="""
        Initiate mobile money payment for a donation using Azam Pay.
        
        **Supported Providers:**
        - Airtel
        - Tigo
        - Halopesa
        - Azampesa
        
        **Process:**
        1. Create donation first (via /donations/create/)
        2. Use donation ID to initiate payment
        3. Customer receives USSD push notification
        4. Customer confirms payment on phone
        5. Webhook updates donation status
        
        **Phone Number Format:**
        - Use format: 255XXXXXXXXX (Tanzania)
        - Example: 255712345678
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['donation_id', 'provider', 'phone_number'],
            properties={
                'donation_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Donation ID to pay for'
                ),
                'provider': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Mobile money provider',
                    enum=['Airtel', 'Tigo', 'Halopesa', 'Azampesa']
                ),
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Customer phone number (format: 255XXXXXXXXX)',
                    example='255712345678'
                ),
                'currency': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Currency code (default: TZS)',
                    default='TZS'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Payment initiated successfully',
                examples={
                    'application/json': {
                        'success': True,
                        'message': 'Payment initiated. Please check your phone to confirm.',
                        'donation_id': 123,
                        'transaction_id': 'TXN123456',
                        'amount': '50000.00',
                        'currency': 'TZS'
                    }
                }
            ),
            400: 'Bad request - validation error',
            404: 'Donation not found'
        }
    )
    def post(self, request):
        try:
            # Validate input
            donation_id = request.data.get('donation_id')
            provider = request.data.get('provider')
            phone_number = request.data.get('phone_number')
            currency = request.data.get('currency', 'TZS')
            
            if not all([donation_id, provider, phone_number]):
                return Response({
                    'error': 'Missing required fields: donation_id, provider, phone_number'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate provider
            valid_providers = ['Airtel', 'Tigo', 'Halopesa', 'Azampesa']
            if provider not in valid_providers:
                return Response({
                    'error': f'Invalid provider. Must be one of: {", ".join(valid_providers)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get donation
            try:
                donation = Donation.objects.get(id=donation_id)
            except Donation.DoesNotExist:
                return Response({
                    'error': 'Donation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if donation is already completed
            if donation.status == 'COMPLETED':
                return Response({
                    'error': 'Donation already completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if donation is already being processed
            if donation.status == 'PENDING' and donation.transaction_id:
                return Response({
                    'error': 'Payment already in progress for this donation'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert amount to TZS if needed (assuming USD to TZS rate ~2300)
            # You should fetch real exchange rate in production
            amount = donation.amount
            if currency == 'TZS':
                # Convert USD to TZS (you should use a real exchange rate API)
                amount = donation.amount * Decimal('2300')
            
            # Prepare external ID (unique reference)
            external_id = f"RHCI-DN-{donation.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Initiate payment with Azam Pay
            success, response_data = azampay_service.initiate_checkout(
                amount=amount,
                currency=currency,
                external_id=external_id,
                provider=provider,
                account_number=phone_number,
                additional_properties={
                    'donation_id': donation.id,
                    'patient_id': donation.patient.id if donation.patient else None,
                    'donor_email': donation.donor.email if donation.donor else donation.anonymous_email
                }
            )
            
            if success:
                # Update donation with payment info
                with db_transaction.atomic():
                    donation.payment_method = f"Mobile Money - {provider}"
                    donation.payment_gateway = 'Azam Pay'
                    donation.transaction_id = response_data.get('data', {}).get('transactionId', external_id)
                    donation.status = 'PENDING'
                    donation.save()
                
                logger.info(f"Payment initiated for donation {donation.id}: {donation.transaction_id}")
                
                return Response({
                    'success': True,
                    'message': 'Payment initiated. Please check your phone to confirm.',
                    'donation_id': donation.id,
                    'transaction_id': donation.transaction_id,
                    'amount': str(amount),
                    'currency': currency,
                    'provider': provider
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Payment initiation failed for donation {donation.id}: {response_data}")
                return Response({
                    'error': 'Payment initiation failed',
                    'details': response_data.get('error', 'Unknown error')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error in mobile money checkout: {str(e)}")
            return Response({
                'error': 'Payment processing error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AzamPayBankCheckoutView(APIView):
    """
    Initiate bank payment via Azam Pay
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Donations - Payment'],
        operation_summary="Azam Pay Bank Checkout",
        operation_description="""
        Initiate bank payment for a donation using Azam Pay.
        
        **Process:**
        1. Create donation first
        2. Request OTP from your bank
        3. Use this endpoint with OTP to complete payment
        
        **Note:** Requires merchant bank account setup with Azam Pay
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['donation_id', 'provider', 'merchant_account_number', 'merchant_mobile_number', 'otp'],
            properties={
                'donation_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'provider': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Bank provider name'
                ),
                'merchant_account_number': openapi.Schema(type=openapi.TYPE_STRING),
                'merchant_mobile_number': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='One-time password from bank'
                ),
                'currency': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default='TZS'
                )
            }
        ),
        responses={
            200: 'Payment initiated successfully',
            400: 'Bad request',
            404: 'Donation not found'
        }
    )
    def post(self, request):
        try:
            # Validate input
            donation_id = request.data.get('donation_id')
            provider = request.data.get('provider')
            merchant_account = request.data.get('merchant_account_number')
            merchant_mobile = request.data.get('merchant_mobile_number')
            otp = request.data.get('otp')
            currency = request.data.get('currency', 'TZS')
            
            if not all([donation_id, provider, merchant_account, merchant_mobile, otp]):
                return Response({
                    'error': 'Missing required fields'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get donation
            try:
                donation = Donation.objects.get(id=donation_id)
            except Donation.DoesNotExist:
                return Response({
                    'error': 'Donation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if donation.status == 'COMPLETED':
                return Response({
                    'error': 'Donation already completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert amount
            amount = donation.amount
            if currency == 'TZS':
                amount = donation.amount * Decimal('2300')
            
            external_id = f"RHCI-DN-{donation.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Initiate bank payment
            success, response_data = azampay_service.initiate_bank_checkout(
                amount=amount,
                currency=currency,
                external_id=external_id,
                provider=provider,
                merchant_account_number=merchant_account,
                merchant_mobile_number=merchant_mobile,
                otp=otp,
                additional_properties={
                    'donation_id': donation.id,
                    'patient_id': donation.patient.id if donation.patient else None
                }
            )
            
            if success:
                with db_transaction.atomic():
                    donation.payment_method = f"Bank Transfer - {provider}"
                    donation.payment_gateway = 'Azam Pay'
                    donation.transaction_id = response_data.get('data', {}).get('transactionId', external_id)
                    donation.status = 'PENDING'
                    donation.save()
                
                return Response({
                    'success': True,
                    'message': 'Bank payment initiated successfully',
                    'donation_id': donation.id,
                    'transaction_id': donation.transaction_id
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Payment initiation failed',
                    'details': response_data.get('error')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error in bank checkout: {str(e)}")
            return Response({
                'error': 'Payment processing error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AzamPayCallbackView(APIView):
    """
    Webhook endpoint to receive payment notifications from Azam Pay
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Donations - Payment'],
        operation_summary="Azam Pay Webhook Callback",
        operation_description="""
        Webhook endpoint for Azam Pay payment notifications.
        This endpoint is called automatically by Azam Pay when payment status changes.
        
        **Important:** Configure this URL in your Azam Pay merchant dashboard
        **URL:** https://your-domain.com/api/v1.0/donations/payment/azampay/callback/
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Azam Pay callback payload'
        ),
        responses={
            200: 'Callback processed successfully',
            400: 'Invalid callback data'
        }
    )
    def post(self, request):
        try:
            callback_data = request.data
            logger.info(f"Received Azam Pay callback: {callback_data}")
            
            # Process callback
            result = azampay_service.process_callback(callback_data)
            
            external_id = result.get('external_id')
            transaction_status = result.get('status')
            transaction_id = result.get('transaction_id')
            
            if not external_id:
                logger.error("No external_id in callback")
                return Response({
                    'error': 'Invalid callback data'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract donation ID from external_id (format: RHCI-DN-{id}-timestamp)
            try:
                donation_id = int(external_id.split('-')[2])
                donation = Donation.objects.get(id=donation_id)
            except (IndexError, ValueError, Donation.DoesNotExist):
                logger.error(f"Could not find donation from external_id: {external_id}")
                return Response({
                    'error': 'Donation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update donation based on status
            with db_transaction.atomic():
                if transaction_status == 'success' or transaction_status == 'SUCCESSFUL':
                    donation.status = 'COMPLETED'
                    donation.completed_at = timezone.now()
                    
                    # Update patient funding if applicable
                    if donation.patient:
                        patient = donation.patient
                        patient.funding_received += donation.amount
                        patient.save()
                        
                        # Check if fully funded
                        if patient.funding_received >= patient.funding_required:
                            patient.status = 'FULLY_FUNDED'
                            patient.save()
                    
                    logger.info(f"Donation {donation.id} completed successfully")
                    
                elif transaction_status == 'failed' or transaction_status == 'FAILED':
                    donation.status = 'FAILED'
                    logger.warning(f"Donation {donation.id} payment failed")
                    
                elif transaction_status == 'cancelled' or transaction_status == 'CANCELLED':
                    donation.status = 'CANCELLED'
                    logger.info(f"Donation {donation.id} cancelled")
                
                # Update transaction ID if provided
                if transaction_id:
                    donation.transaction_id = transaction_id
                
                donation.save()
            
            return Response({
                'success': True,
                'message': 'Callback processed successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing Azam Pay callback: {str(e)}")
            return Response({
                'error': 'Callback processing error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckPaymentStatusView(APIView):
    """
    Check payment status for a donation
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Donations - Payment'],
        operation_summary="Check Payment Status",
        operation_description="""
        Check the current payment status of a donation.
        Queries Azam Pay for the latest transaction status.
        """,
        manual_parameters=[
            openapi.Parameter(
                'donation_id',
                openapi.IN_QUERY,
                description="Donation ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description='Payment status',
                examples={
                    'application/json': {
                        'donation_id': 123,
                        'status': 'COMPLETED',
                        'transaction_id': 'TXN123456',
                        'amount': '50.00',
                        'payment_method': 'Mobile Money - Tigo'
                    }
                }
            ),
            404: 'Donation not found'
        }
    )
    def get(self, request):
        try:
            donation_id = request.query_params.get('donation_id')
            
            if not donation_id:
                return Response({
                    'error': 'donation_id parameter required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                donation = Donation.objects.get(id=donation_id)
            except Donation.DoesNotExist:
                return Response({
                    'error': 'Donation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # If we have a transaction ID, check with Azam Pay
            if donation.transaction_id and donation.status == 'PENDING':
                success, response_data = azampay_service.check_transaction_status(
                    donation.transaction_id
                )
                
                if success:
                    # Update donation status based on Azam Pay response
                    azam_status = response_data.get('data', {}).get('status')
                    if azam_status == 'success':
                        donation.status = 'COMPLETED'
                        donation.completed_at = timezone.now()
                        donation.save()
                        
                        # Update patient funding
                        if donation.patient:
                            patient = donation.patient
                            patient.funding_received += donation.amount
                            if patient.funding_received >= patient.funding_required:
                                patient.status = 'FULLY_FUNDED'
                            patient.save()
            
            return Response({
                'donation_id': donation.id,
                'status': donation.status,
                'transaction_id': donation.transaction_id,
                'amount': str(donation.amount),
                'payment_method': donation.payment_method,
                'payment_gateway': donation.payment_gateway,
                'created_at': donation.created_at,
                'completed_at': donation.completed_at
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return Response({
                'error': 'Status check error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
