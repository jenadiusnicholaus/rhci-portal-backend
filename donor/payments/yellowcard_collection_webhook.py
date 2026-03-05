import json
import logging
import hmac
import hashlib
import base64
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from decimal import Decimal

logger = logging.getLogger(__name__)

# Whitelist Yellow Card webhook IPs (production only)
YELLOWCARD_WEBHOOK_IPS = getattr(settings, 'YELLOWCARD_WEBHOOK_IPS', [])

def verify_yellowcard_signature(request_body, signature, secret_key):
    """
    Verify Yellow Card webhook signature.
    
    According to Yellow Card docs:
    "The signature is a base64 encoded sha256 hash of the request body using the secretkey"
    
    Args:
        request_body: Raw request body as bytes
        signature: X-YC-Signature header value
        secret_key: Yellow Card API secret key
    
    Returns:
        bool: True if signature is valid
    """
    if not signature:
        logger.error("Missing X-YC-Signature header")
        return False
    
    try:
        # Calculate expected signature - simple HMAC of body only
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            request_body,
            hashlib.sha256
        ).digest()
        
        # Convert to base64
        expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature_b64)
        
        if not is_valid:
            logger.error(f"Invalid signature. Expected: {expected_signature_b64}, Got: {signature}")
            logger.error(f"Secret key length: {len(secret_key)}")
            logger.error(f"Request body: {request_body}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Signature verification error: {str(e)}")
        return False

def get_client_ip(request):
    """Get client IP address, accounting for proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
@require_http_methods(["POST"])
def yellowcard_collection_webhook(request):
    """
    Handle Yellow Card Collection webhooks.
    
    Events:
    - COLLECTION.PENDING: Collection initiated
    - COLLECTION.COMPLETE: Collection successful
    - COLLECTION.FAILED: Collection failed
    - COLLECTION.EXPIRED: Collection expired
    """
    
    # 1. IP Whitelist Check (production only)
    if not settings.DEBUG and YELLOWCARD_WEBHOOK_IPS:
        client_ip = get_client_ip(request)
        if client_ip not in YELLOWCARD_WEBHOOK_IPS:
            logger.warning(f"Webhook request from non-whitelisted IP: {client_ip}")
            return HttpResponse('Forbidden', status=403)
    
    # 2. Get request body and signature
    try:
        request_body = request.body
        webhook_data = json.loads(request_body)
        signature = request.headers.get('X-YC-Signature')
        
        logger.info(f"Yellow Card Collection webhook: {webhook_data}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error parsing webhook: {str(e)}")
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # 3. Signature Verification
    secret_key = getattr(settings, 'YELLOWCARD_SECRET_KEY', None)
    if not secret_key:
        logger.error("YELLOWCARD_SECRET_KEY not configured")
        return JsonResponse({'error': 'Server configuration error'}, status=500)
    
    if not verify_yellowcard_signature(request_body, signature, secret_key):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    # 4. Validate required fields
    required_fields = ['event', 'status', 'apiKey', 'sessionId']
    for field in required_fields:
        if field not in webhook_data:
            logger.error(f"Missing required field: {field}")
            return JsonResponse({'error': f'Missing field: {field}'}, status=400)
    
    # 5. Process the webhook event
    event = webhook_data.get('event')
    webhook_status = webhook_data.get('status')
    session_id = webhook_data.get('sessionId')
    api_key = webhook_data.get('apiKey')
    
    logger.info(f"Processing Collection webhook: {event} - {webhook_status} - Session: {session_id}")
    
    try:
        with transaction.atomic():
            # Find donation by Yellow Card session ID
            from donor.models import Donation
            
            donation = Donation.objects.filter(
                transaction_id=session_id,
                payment_gateway='YELLOWCARD'
            ).first()
            
            if not donation:
                logger.warning(f"No donation found for session: {session_id}")
                return JsonResponse({'status': 'ignored', 'reason': 'donation_not_found'}, status=200)
            
            logger.info(f"Found donation {donation.id} for session {session_id}")
            
            # Handle different collection events
            if event == 'COLLECTION.COMPLETE' and webhook_status == 'COMPLETE':
                if donation.status == 'COMPLETED':
                    logger.info(f"Donation {donation.id} already completed")
                    return JsonResponse({'status': 'already_completed'}, status=200)
                
                # Update donation to completed
                donation.status = 'COMPLETED'
                donation.completed_at = timezone.now()
                donation.save()
                
                # Update patient status if applicable
                if donation.patient and donation.status == 'COMPLETED':
                    patient = donation.patient
                    if patient.funding_required == 0 or patient.funding_received_actual >= patient.funding_required:
                        patient.status = 'FULLY_FUNDED'
                        patient.save()
                        logger.info(f"Patient {patient.id} marked as FULLY_FUNDED")
                
                logger.info(f"✅ Collection completed: Donation {donation.id}")
                return JsonResponse({'status': 'completed', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.FAILED' and webhook_status == 'FAILED':
                if donation.status == 'FAILED':
                    logger.info(f"Donation {donation.id} already failed")
                    return JsonResponse({'status': 'already_failed'}, status=200)
                
                donation.status = 'FAILED'
                donation.failure_reason = webhook_data.get('errorCode', 'Collection failed')
                donation.save()
                
                logger.info(f"❌ Collection failed: Donation {donation.id} - {donation.failure_reason}")
                return JsonResponse({'status': 'failed', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.EXPIRED' and webhook_status == 'EXPIRED':
                if donation.status == 'FAILED':
                    logger.info(f"Donation {donation.id} already marked as failed")
                    return JsonResponse({'status': 'already_failed'}, status=200)
                
                donation.status = 'FAILED'
                donation.failure_reason = 'Collection expired - not accepted/denied within timeframe'
                donation.save()
                
                logger.info(f"⏰ Collection expired: Donation {donation.id}")
                return JsonResponse({'status': 'expired', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.PENDING' and webhook_status == 'PENDING':
                # Collection is awaiting results from channel
                if donation.status != 'PENDING':
                    donation.status = 'PENDING'
                    donation.save()
                
                logger.info(f"⏳ Collection pending: Donation {donation.id}")
                return JsonResponse({'status': 'pending', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.CREATED' and webhook_status == 'CREATED':
                # Collection request submitted, undergoing initial validation
                # Donation should already be PENDING from creation
                if donation.status != 'PENDING':
                    donation.status = 'PENDING'
                    donation.save()
                
                logger.info(f"📝 Collection created: Donation {donation.id}")
                return JsonResponse({'status': 'created', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.PENDING_APPROVAL' and webhook_status == 'PENDING_APPROVAL':
                # Collection pending client action (accept/deny)
                # Keep as PENDING - waiting for user action
                if donation.status != 'PENDING':
                    donation.status = 'PENDING'
                    donation.save()
                
                logger.info(f"⏳ Collection pending approval: Donation {donation.id}")
                return JsonResponse({'status': 'pending_approval', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.PROCESS' and webhook_status == 'PROCESS':
                # Collection accepted, undergoing final checks
                # Keep as PENDING - still processing
                if donation.status != 'PENDING':
                    donation.status = 'PENDING'
                    donation.save()
                
                logger.info(f"⚙️ Collection in process: Donation {donation.id}")
                return JsonResponse({'status': 'process', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.PROCESSING' and webhook_status == 'PROCESSING':
                # Collection being broadcasted on channel
                # Keep as PENDING - still broadcasting
                if donation.status != 'PENDING':
                    donation.status = 'PENDING'
                    donation.save()
                
                logger.info(f"📡 Collection processing: Donation {donation.id}")
                return JsonResponse({'status': 'processing', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.CANCELLED' and webhook_status == 'CANCELLED':
                # Collection was cancelled and will be refunded
                if donation.status == 'FAILED':
                    logger.info(f"Donation {donation.id} already marked as failed")
                    return JsonResponse({'status': 'already_failed'}, status=200)
                
                donation.status = 'FAILED'
                donation.failure_reason = 'Collection cancelled - refund will be processed if payment was received'
                donation.save()
                
                logger.info(f"🚫 Collection cancelled: Donation {donation.id}")
                return JsonResponse({'status': 'cancelled', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.REFUNDED' and webhook_status == 'REFUNDED':
                # Collection refund is complete
                if donation.status == 'FAILED':
                    logger.info(f"Donation {donation.id} already marked as failed")
                    return JsonResponse({'status': 'already_failed'}, status=200)
                
                # Mark as failed since refund means the donation didn't succeed
                donation.status = 'FAILED'
                donation.failure_reason = 'Collection refunded - payment returned to customer'
                donation.save()
                
                logger.info(f"💰 Collection refunded: Donation {donation.id}")
                return JsonResponse({'status': 'refunded', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.PENDING_REFUND' and webhook_status == 'PENDING_REFUND':
                # Collection refund request received and queued
                # Mark as failed since refund is being processed
                donation.status = 'FAILED'
                donation.failure_reason = 'Collection refund pending - refund request queued'
                donation.save()
                
                logger.info(f"⏳ Collection refund pending: Donation {donation.id}")
                return JsonResponse({'status': 'pending_refund', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.REFUND_PROCESSING' and webhook_status == 'REFUND_PROCESSING':
                # Collection refund being processed
                donation.status = 'FAILED'
                donation.failure_reason = 'Collection refund processing - waiting for provider feedback'
                donation.save()
                
                logger.info(f"⚙️ Collection refund processing: Donation {donation.id}")
                return JsonResponse({'status': 'refund_processing', 'donation_id': donation.id}, status=200)
            
            elif event == 'COLLECTION.REFUND_FAILED' and webhook_status == 'REFUND_FAILED':
                # Collection refund failed after 5 attempts
                donation.status = 'FAILED'
                donation.failure_reason = 'Collection refund failed - retry after few hours recommended'
                donation.save()
                
                logger.info(f"❌ Collection refund failed: Donation {donation.id}")
                return JsonResponse({'status': 'refund_failed', 'donation_id': donation.id}, status=200)
            
            else:
                logger.warning(f"Unhandled webhook event: {event} - {webhook_status}")
                return JsonResponse({'status': 'ignored', 'reason': 'unhandled_event'}, status=200)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Processing error'}, status=500)
