"""
Payment callback and status check views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db import transaction as db_transaction
import logging

from donor.models import Donation
from .azampay_service import azampay_service

logger = logging.getLogger(__name__)


class AzamPayCallbackView(APIView):
    """
    Webhook endpoint to receive payment notifications from Azam Pay
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Donations - AzamPay'],
        operation_summary="Azam Pay Webhook Callback",
        operation_description="""
        Webhook endpoint for Azam Pay payment notifications.
        This endpoint is called automatically by Azam Pay when payment status changes.
        
        **IMPORTANT - Production Setup:**
        1. Configure this URL in your AzamPay merchant dashboard
        2. URL: https://your-domain.com/api/v1.0/donors/payment/azampay/callback/
        3. Must be publicly accessible (not localhost)
        4. Must use HTTPS in production
        5. Return 200 OK to acknowledge receipt
        
        **Callback Payload Format:**
        ```json
        {
            "transactionId": "AZM123456789",
            "externalId": "RHCI-DN-29-20251208065834",
            "amount": "115000",
            "status": "success",
            "message": "Payment successful",
            "provider": "Mpesa"
        }
        ```
        
        **Status Values:**
        - `success` / `successful` - Payment completed
        - `failed` / `failure` - Payment failed
        - `cancelled` / `canceled` - Payment cancelled by user
        
        **Note:** In sandbox mode, callbacks may not be sent automatically.
        Use the manual update endpoint for testing.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Azam Pay callback payload (Official format)',
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction amount in TZS', example='115000'),
                'clientId': openapi.Schema(type=openapi.TYPE_STRING, description='Client identifier'),
                'externalreference': openapi.Schema(type=openapi.TYPE_STRING, description='Your reference ID', example='RHCI-DN-29-20251208065834'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction description'),
                'mnoreference': openapi.Schema(type=openapi.TYPE_STRING, description='Mobile network operator reference'),
                'msisdn': openapi.Schema(type=openapi.TYPE_STRING, description='Customer phone number', example='255789123456'),
                'operator': openapi.Schema(type=openapi.TYPE_STRING, description='Mobile network operator', example='Mpesa'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Webhook authentication password'),
                'reference': openapi.Schema(type=openapi.TYPE_STRING, description='AzamPay transaction reference'),
                'transactionstatus': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction status', enum=['success', 'failure']),
                'transid': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction ID'),
                'user': openapi.Schema(type=openapi.TYPE_STRING, description='User identifier'),
                'utilityref': openapi.Schema(type=openapi.TYPE_STRING, description='Utility reference ID'),
            }
        ),
        responses={
            200: 'Callback processed successfully',
            400: 'Invalid callback data',
            404: 'Donation not found'
        }
    )
    def post(self, request):
        try:
            callback_data = request.data
            logger.info(f"="*50)
            logger.info(f"Received Azam Pay callback: {callback_data}")
            logger.info(f"="*50)
            
            # Optional: Verify webhook password (if configured)
            from django.conf import settings
            if settings.AZAM_PAY_WEBHOOK_PASSWORD:
                webhook_password = callback_data.get('password')
                if webhook_password != settings.AZAM_PAY_WEBHOOK_PASSWORD:
                    logger.warning(f"Invalid webhook password received: {webhook_password}")
                    return Response({
                        'error': 'Unauthorized webhook'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Process callback
            result = azampay_service.process_callback(callback_data)
            
            external_id = result.get('external_id')
            transaction_status = result.get('status', '').upper()
            transaction_id = result.get('transaction_id')
            
            logger.info(f"Processed callback - External ID: {external_id}, Status: {transaction_status}, TxnID: {transaction_id}")
            
            if not external_id:
                logger.error("No external_id in callback")
                return Response({
                    'error': 'Invalid callback data'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract donation ID from external_id (format: RHCI-DN-{id}-timestamp)
            try:
                donation_id = int(external_id.split('-')[2])
                donation = Donation.objects.get(id=donation_id)
                logger.info(f"Found donation {donation.id} with current status: {donation.status}")
            except (IndexError, ValueError, Donation.DoesNotExist):
                logger.error(f"Could not find donation from external_id: {external_id}")
                return Response({
                    'error': 'Donation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update donation based on status
            with db_transaction.atomic():
                if transaction_status in ['SUCCESS', 'SUCCESSFUL', 'COMPLETED']:
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
                        
                        logger.info(f"Updated patient {patient.id} funding: {patient.funding_received}/{patient.funding_required}")
                    
                    logger.info(f"✅ Donation {donation.id} completed successfully")
                    
                elif transaction_status in ['FAILED', 'FAILURE']:
                    donation.status = 'FAILED'
                    logger.warning(f"❌ Donation {donation.id} payment failed")
                    
                elif transaction_status in ['CANCELLED', 'CANCELED']:
                    donation.status = 'CANCELLED'
                    logger.info(f"⚠️  Donation {donation.id} cancelled")
                else:
                    logger.warning(f"Unknown status '{transaction_status}' for donation {donation.id}")
                
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
        tags=['Donations - AzamPay'],
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
                logger.info(f"Checking status for pending donation {donation.id} with txn ID: {donation.transaction_id}")
                success, response_data = azampay_service.check_transaction_status(
                    donation.transaction_id
                )
                
                logger.info(f"AzamPay status check response: {response_data}")
                
                if success:
                    # Handle different response formats
                    # Format 1: {"data": {"status": "success"}}
                    # Format 2: {"status": "success"}
                    azam_status = response_data.get('data', {}).get('status') or response_data.get('status')
                    
                    if azam_status:
                        azam_status = azam_status.upper()
                        logger.info(f"AzamPay status for donation {donation.id}: {azam_status}")
                        
                        if azam_status in ['SUCCESS', 'SUCCESSFUL', 'COMPLETED']:
                            with db_transaction.atomic():
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
                                    logger.info(f"✅ Updated donation {donation.id} to COMPLETED, patient funding: {patient.funding_received}")
                        elif azam_status in ['FAILED', 'FAILURE']:
                            donation.status = 'FAILED'
                            donation.save()
                            logger.warning(f"❌ Updated donation {donation.id} to FAILED")
                        elif azam_status in ['PENDING', 'PROCESSING']:
                            logger.info(f"⏳ Donation {donation.id} still pending on AzamPay side")
                    else:
                        logger.warning(f"No status found in AzamPay response: {response_data}")
                else:
                    logger.error(f"Failed to check status with AzamPay: {response_data}")
            
            response_payload = {
                'donation_id': donation.id,
                'status': donation.status,
                'transaction_id': donation.transaction_id,
                'amount': str(donation.amount),
                'payment_method': donation.payment_method,
                'payment_gateway': donation.payment_gateway,
                'created_at': donation.created_at,
                'completed_at': donation.completed_at
            }
            
            # Add debug info for sandbox
            if donation.status == 'PENDING':
                response_payload['note'] = 'Payment still pending. In sandbox, you may need to manually confirm the payment in AzamPay dashboard or use test credentials to complete the transaction.'
            
            return Response(response_payload, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return Response({
                'error': 'Status check error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManualPaymentUpdateView(APIView):
    """
    Manually update payment status - useful for sandbox testing
    WARNING: Should be disabled in production or require admin authentication
    """
    permission_classes = [AllowAny]  # TODO: Change to IsAdminUser in production
    
    @swagger_auto_schema(
        tags=['Donations - AzamPay'],
        operation_summary="Manual Payment Status Update (Sandbox Only)",
        operation_description="""
        Manually update donation payment status - useful for sandbox testing.
        
        **⚠️ WARNING:** This endpoint should be disabled in production or require admin authentication.
        Use this to simulate payment completion in sandbox environment.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['donation_id', 'status'],
            properties={
                'donation_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Donation ID'),
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['COMPLETED', 'FAILED', 'CANCELLED'],
                    description='New payment status'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description='Status updated successfully',
                examples={
                    'application/json': {
                        'success': True,
                        'message': 'Donation status updated to COMPLETED',
                        'donation': {
                            'id': 29,
                            'status': 'COMPLETED',
                            'amount': '50.00',
                            'completed_at': '2025-12-08T07:30:00Z'
                        }
                    }
                }
            ),
            400: 'Invalid request',
            404: 'Donation not found'
        }
    )
    def post(self, request):
        try:
            donation_id = request.data.get('donation_id')
            new_status = request.data.get('status', '').upper()
            
            if not donation_id or not new_status:
                return Response({
                    'error': 'donation_id and status are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if new_status not in ['COMPLETED', 'FAILED', 'CANCELLED']:
                return Response({
                    'error': 'Invalid status. Must be COMPLETED, FAILED, or CANCELLED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                donation = Donation.objects.get(id=donation_id)
            except Donation.DoesNotExist:
                return Response({
                    'error': 'Donation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update donation status
            with db_transaction.atomic():
                old_status = donation.status
                donation.status = new_status
                
                if new_status == 'COMPLETED':
                    donation.completed_at = timezone.now()
                    
                    # Update patient funding if applicable
                    if donation.patient and old_status != 'COMPLETED':
                        patient = donation.patient
                        patient.funding_received += donation.amount
                        patient.save()
                        
                        # Check if fully funded
                        if patient.funding_received >= patient.funding_required:
                            patient.status = 'FULLY_FUNDED'
                            patient.save()
                
                donation.save()
                logger.info(f"🔧 Manual update: Donation {donation.id} status changed from {old_status} to {new_status}")
            
            return Response({
                'success': True,
                'message': f'Donation status updated to {new_status}',
                'donation': {
                    'id': donation.id,
                    'status': donation.status,
                    'amount': str(donation.amount),
                    'transaction_id': donation.transaction_id,
                    'completed_at': donation.completed_at,
                    'old_status': old_status
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in manual status update: {str(e)}")
            return Response({
                'error': 'Status update error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
