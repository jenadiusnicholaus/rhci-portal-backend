"""
AzamPay Bill Pay API Integration
---------------------------------
Implements the 3 required endpoints for Bill Pay API:
1. Name Lookup - Returns patient info by bill_identifier
2. Payment Processing - Creates donation and updates patient
3. Status Check - Returns payment/donation status

Security: JWT token + HMAC-SHA256 hash verification
"""

import jwt
import hmac
import hashlib
import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from functools import wraps

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from patient.models import PatientProfile
from donor.models import Donation

logger = logging.getLogger(__name__)


# ============================================================================
# SECURITY UTILITIES
# ============================================================================

def get_billpay_secret():
    """Get Bill Pay API secret from settings"""
    return getattr(settings, 'AZAMPAY_BILLPAY_SECRET', 'your-billpay-secret-key')


def get_billpay_jwt_secret():
    """Get JWT secret for Bill Pay API"""
    return getattr(settings, 'AZAMPAY_BILLPAY_JWT_SECRET', 'your-jwt-secret')


def verify_jwt_token(token):
    """
    Verify JWT token from AzamPay
    Returns decoded payload if valid, None if invalid
    """
    try:
        jwt_secret = get_billpay_jwt_secret()
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        # Check expiration
        exp = payload.get('exp')
        if exp and datetime.fromtimestamp(exp) < datetime.now():
            logger.warning("JWT token expired")
            return None
        
        return payload
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        return None


def verify_hmac_signature(data_object, provided_hash):
    """
    Verify HMAC-SHA256 signature according to AzamPay Bill Pay API spec
    
    Process:
    1. Convert Data object to minified JSON string
    2. Compute SHA256 hash of the JSON string
    3. Sign the hash with secret key using HMAC-SHA256
    4. Compare with provided Hash field
    
    Args:
        data_object: The Data object from request (dict)
        provided_hash: The Hash field from request
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        secret = get_billpay_secret()
        
        # 1. Convert Data object to minified JSON string (no spaces)
        json_string = json.dumps(data_object, separators=(',', ':'), sort_keys=False)
        
        # 2. Compute SHA256 hash of the JSON string
        sha256_hash = hashlib.sha256(json_string.encode('utf-8')).hexdigest()
        
        # 3. Sign the hash with HMAC-SHA256
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            sha256_hash.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 4. Compare signatures (constant-time comparison)
        is_valid = hmac.compare_digest(expected_signature, provided_hash)
        
        if not is_valid:
            logger.warning(f"HMAC signature mismatch.")
            logger.debug(f"JSON String: {json_string}")
            logger.debug(f"SHA256 Hash: {sha256_hash}")
            logger.debug(f"Expected Signature: {expected_signature}")
            logger.debug(f"Provided Hash: {provided_hash}")
        
        return is_valid
    except Exception as e:
        logger.error(f"HMAC verification error: {str(e)}")
        return False


def billpay_auth_required(view_func):
    """
    Decorator to verify JWT token and HMAC signature per AzamPay Bill Pay API spec
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 1. Verify JWT token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            return JsonResponse({
                'Status': 'Failed',
                'StatusCode': 401,
                'Message': 'Missing or invalid Authorization header'
            }, status=401)
        
        token = auth_header.replace('Bearer ', '')
        payload = verify_jwt_token(token)
        if not payload:
            logger.warning("Invalid JWT token")
            return JsonResponse({
                'Status': 'Failed',
                'StatusCode': 401,
                'Message': 'Invalid or expired token'
            }, status=401)
        
        # 2. Parse request body
        try:
            request_data = json.loads(request.body)
            data_object = request_data.get('Data', {})
            provided_hash = request_data.get('Hash', '')
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'Status': 'Failed',
                'StatusCode': 400,
                'Message': 'Invalid JSON'
            }, status=400)
        
        if not provided_hash:
            logger.warning("Missing Hash field")
            return JsonResponse({
                'Status': 'Failed',
                'StatusCode': 400,
                'Message': 'Missing Hash field'
            }, status=400)
        
        # 3. Verify HMAC signature
        if not verify_hmac_signature(data_object, provided_hash):
            logger.warning("Invalid HMAC signature")
            return JsonResponse({
                'Status': 'Failed',
                'StatusCode': 401,
                'Message': 'Invalid signature - request may be tampered'
            }, status=401)
        
        # Attach payload and data to request for use in view
        request.jwt_payload = payload
        request.bill_data = data_object
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ============================================================================
# BILL PAY API ENDPOINTS
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@billpay_auth_required
def name_lookup(request):
    """
    Bill Pay API: Name Lookup Endpoint
    
    Request:
        POST /api/merchant/name-lookup
        {
            "Data": {
                "BillIdentifier": "JIMMY-2024-472",
                "Currency": "TZS",
                "Language": "en",
                "Country": "Tanzania",
                "TimeStamp": "2024-06-12T10:20:30Z",
                "BillType": "Medical",
                "AdditionalProperties": {}
            },
            "Hash": "..."
        }
    
    Response:
        {
            "Name": "Jimmy Mwangi",
            "BillAmount": 1000000.00,
            "BillIdentifier": "JIMMY-2024-472",
            "Status": "Success",
            "Message": "Name found for the provided BillIdentifier.",
            "StatusCode": 0
        }
    """
    try:
        # Get data from decorator
        data = request.bill_data
        bill_identifier = data.get('BillIdentifier', '').strip()
        
        if not bill_identifier:
            return JsonResponse({
                'Status': 'Failed',
                'StatusCode': 400,
                'Message': 'BillIdentifier is required',
                'Name': '',
                'BillAmount': 0,
                'BillIdentifier': ''
            }, status=400)
        
        logger.info(f"Bill Pay Name Lookup: {bill_identifier}")
        
        # Lookup patient by bill_identifier
        try:
            patient = PatientProfile.objects.select_related('user').get(
                bill_identifier=bill_identifier,
                status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED']
            )
        except PatientProfile.DoesNotExist:
            logger.warning(f"Patient not found for BillIdentifier: {bill_identifier}")
            return JsonResponse({
                'Status': 'Failed',
                'StatusCode': 404,
                'Message': 'BillIdentifier not found or patient not active',
                'Name': '',
                'BillAmount': 0,
                'BillIdentifier': bill_identifier
            }, status=404)
        
        # Calculate remaining amount needed
        remaining_amount = float(patient.funding_remaining)
        
        # Prepare response per AzamPay spec
        response_data = {
            'Name': patient.full_name,
            'BillAmount': remaining_amount,
            'BillIdentifier': bill_identifier,
            'Status': 'Success',
            'Message': 'Name found for the provided BillIdentifier.',
            'StatusCode': 0
        }
        
        logger.info(f"Name lookup successful: {bill_identifier} -> {patient.full_name}, Amount: {remaining_amount}")
        
        return JsonResponse(response_data, status=200)
    
    except Exception as e:
        logger.error(f"Name lookup error: {str(e)}", exc_info=True)
        return JsonResponse({
            'Status': 'Failed',
            'StatusCode': 500,
            'Message': 'Internal server error',
            'Name': '',
            'BillAmount': 0,
            'BillIdentifier': ''
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@billpay_auth_required
def payment_notification(request):
    """
    Bill Pay API: Payment Notification Endpoint
    
    Request:
        POST /api/merchant/payment
        {
            "Data": {
                "FspReferenceId": "fsp123456",
                "PgReferenceId": "pg123456",
                "Amount": 10000,
                "BillIdentifier": "JIMMY-2024-472",
                "PaymentDesc": "Medical donation",
                "FspCode": "MPESA",
                "Country": "Tanzania",
                "TimeStamp": "2024-06-12T10:20:30Z",
                "BillType": "Medical",
                "AdditionalProperties": {"phone": "255712345678"}
            },
            "Hash": "..."
        }
    
    Response:
        {
            "MerchantReferenceId": "RHCI-DN-123",
            "Status": "Success",
            "StatusCode": 0,
            "Message": "Payment successful."
        }
    """
    try:
        # Get data from decorator
        data = request.bill_data
        
        bill_identifier = data.get('BillIdentifier', '').strip()
        amount = data.get('Amount')
        fsp_reference_id = data.get('FspReferenceId', '')
        pg_reference_id = data.get('PgReferenceId', '')
        payment_desc = data.get('PaymentDesc', '')
        fsp_code = data.get('FspCode', 'USSD')
        additional_props = data.get('AdditionalProperties', {})
        phone_number = additional_props.get('phone', '')
        
        # Validate required fields
        if not bill_identifier or not amount or not pg_reference_id:
            return JsonResponse({
                'MerchantReferenceId': '',
                'Status': 'Failed',
                'StatusCode': 400,
                'Message': 'Missing required fields: BillIdentifier, Amount, PgReferenceId'
            }, status=400)
        
        logger.info(f"Bill Pay Payment: {bill_identifier}, Amount: {amount}, PgRef: {pg_reference_id}")
        
        # Convert amount to Decimal
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid amount: {amount}")
            return JsonResponse({
                'MerchantReferenceId': '',
                'Status': 'Failed',
                'StatusCode': 400,
                'Message': 'Invalid amount'
            }, status=400)
        
        # Process payment in atomic transaction
        with transaction.atomic():
            # 1. Lookup patient
            try:
                patient = PatientProfile.objects.select_for_update().get(
                    bill_identifier=bill_identifier
                )
            except PatientProfile.DoesNotExist:
                logger.error(f"Patient not found for BillIdentifier: {bill_identifier}")
                return JsonResponse({
                    'MerchantReferenceId': '',
                    'Status': 'Failed',
                    'StatusCode': 404,
                    'Message': 'BillIdentifier not found'
                }, status=404)
            
            # 2. Check for duplicate transaction
            existing_donation = Donation.objects.filter(
                transaction_id=pg_reference_id
            ).first()
            
            if existing_donation:
                logger.warning(f"Duplicate transaction detected: {pg_reference_id}")
                return JsonResponse({
                    'MerchantReferenceId': existing_donation.receipt_number,
                    'Status': 'Success',
                    'StatusCode': 0,
                    'Message': 'Payment already processed'
                }, status=200)
            
            # 3. Create donation record
            donation = Donation.objects.create(
                patient_profile=patient,
                donor_name=payment_desc or 'Anonymous Donor',
                donor_email='',
                donor_phone=phone_number,
                amount=amount,
                currency=patient.funding_currency,
                payment_method=fsp_code,
                payment_gateway='AZAMPAY_BILLPAY',
                transaction_id=pg_reference_id,
                status='COMPLETED',
                completed_at=timezone.now(),
                is_anonymous=True
            )
            
            logger.info(f"Created donation #{donation.id} (Receipt: {donation.receipt_number})")
            
            # 4. Update patient funding
            patient.funding_received += amount
            
            # Check if fully funded
            if patient.funding_received >= patient.funding_required:
                patient.status = 'FULLY_FUNDED'
                logger.info(f"Patient {patient.full_name} is now FULLY_FUNDED!")
            
            patient.save()
            
            # 5. Prepare response
            response_data = {
                'MerchantReferenceId': donation.receipt_number,
                'Status': 'Success',
                'StatusCode': 0,
                'Message': 'Payment successful.'
            }
            
            logger.info(f"Bill Pay payment processed: Receipt {donation.receipt_number}, Patient funding: {patient.funding_percentage}%")
            
            return JsonResponse(response_data, status=200)
    
    except Exception as e:
        logger.error(f"Payment notification error: {str(e)}", exc_info=True)
        return JsonResponse({
            'MerchantReferenceId': '',
            'Status': 'Failed',
            'StatusCode': 500,
            'Message': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@billpay_auth_required
def status_check(request):
    """
    Bill Pay API: Status Check Endpoint
    
    Request:
        POST /api/merchant/status-check
        {
            "transaction_id": "AZM123456789"
        }
        OR
        {
            "bill_identifier": "JIMMY-2024-472",
            "phone_number": "255712345678"
        }
    
    Response:
        {
            "success": true,
            "status": "COMPLETED",
            "MerchantReferenceId": "RHCI-DN-123"
        }
    
    Response:
        {
            "MerchantReferenceId": "RHCI-DN-123",
            "Status": "Success",
            "StatusCode": 0,
            "Message": "Payment status retrieved successfully",
            "PaymentStatus": "COMPLETED",
            "Amount": 10000,
            "BillIdentifier": "JIMMY-2024-472"
        }
    """
    try:
        # Parse request body (no Data/Hash wrapper for status check per spec)
        body_data = json.loads(request.body)
        merchant_reference_id = body_data.get('MerchantReferenceId', '').strip()
        
        if not merchant_reference_id:
            return JsonResponse({
                'MerchantReferenceId': '',
                'Status': 'Failed',
                'StatusCode': 400,
                'Message': 'MerchantReferenceId is required'
            }, status=400)
        
        logger.info(f"Bill Pay Status Check: {merchant_reference_id}")
        
        # Find donation by receipt_number (our MerchantReferenceId)
        try:
            donation = Donation.objects.select_related('patient_profile').get(
                receipt_number=merchant_reference_id
            )
        except Donation.DoesNotExist:
            logger.warning(f"Donation not found for MerchantReferenceId: {merchant_reference_id}")
            return JsonResponse({
                'MerchantReferenceId': merchant_reference_id,
                'Status': 'Failed',
                'StatusCode': 404,
                'Message': 'Transaction not found'
            }, status=404)
        
        # Prepare response
        response_data = {
            'MerchantReferenceId': merchant_reference_id,
            'Status': 'Success',
            'StatusCode': 0,
            'Message': 'Payment status retrieved successfully',
            'PaymentStatus': donation.status,
            'Amount': float(donation.amount),
            'BillIdentifier': donation.patient_profile.bill_identifier,
            'PatientName': donation.patient_profile.full_name,
            'PaymentDate': donation.completed_at.isoformat() if donation.completed_at else None
        }
        
        logger.info(f"Status check successful: {merchant_reference_id}, Status: {donation.status}")
        
        return JsonResponse(response_data, status=200)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'MerchantReferenceId': '',
            'Status': 'Failed',
            'StatusCode': 400,
            'Message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Status check error: {str(e)}", exc_info=True)
        return JsonResponse({
            'MerchantReferenceId': '',
            'Status': 'Failed',
            'StatusCode': 500,
            'Message': 'Internal server error'
        }, status=500)


# ============================================================================
# PUBLIC HELPER ENDPOINTS (Optional - for frontend/testing)
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_patient_by_bill_identifier(request, bill_identifier):
    """
    Public endpoint to get patient info by bill_identifier
    (For frontend to display patient info before donation)
    
    GET /api/patients/by-bill/{bill_identifier}
    """
    try:
        patient = PatientProfile.objects.get(
            bill_identifier=bill_identifier,
            status__in=['PUBLISHED', 'AWAITING_FUNDING', 'FULLY_FUNDED']
        )
        
        return Response({
            'success': True,
            'patient': {
                'id': patient.id,
                'full_name': patient.full_name,
                'bill_identifier': patient.bill_identifier,
                'short_description': patient.short_description,
                'funding_required': float(patient.funding_required),
                'funding_received': float(patient.funding_received),
                'funding_remaining': float(patient.funding_remaining),
                'funding_percentage': float(patient.funding_percentage),
                'funding_currency': patient.funding_currency,
                'status': patient.status
            }
        })
    except PatientProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Patient not found or not active'
        }, status=status.HTTP_404_NOT_FOUND)
