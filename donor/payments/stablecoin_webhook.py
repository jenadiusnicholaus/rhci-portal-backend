"""
Webhook handler for stablecoin (USDC / Solana) payment notifications.

The Pepea aggregator calls this endpoint when an on-chain payment is detected
at the registered collection address.  We verify the HMAC-SHA256 signature,
extract the donation ID from the memo, and update the Donation status.

Endpoint: POST /api/v1.0/donors/webhooks/stablecoin/payment/
"""

import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from donor.models import Donation

logger = logging.getLogger(__name__)


def _verify_signature(body_bytes: bytes, signature: str, secret: str) -> bool:
    """
    Verify HMAC-SHA256 signature from Pepea aggregator.
    The aggregator sends:  X-Signature: <hex digest of HMAC-SHA256(body, signing_secret)>
    """
    if not secret:
        # If no secret is configured, skip verification (dev/sandbox only)
        logger.warning('[stablecoin_webhook] STABLECOIN_WEBHOOK_SECRET not set — skipping signature check')
        return True
    expected = hmac.new(
        key=secret.encode('utf-8'),
        msg=body_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _extract_donation_id(payload: dict) -> int | None:
    """
    Try to extract the donation ID from the webhook payload.

    Pepea includes a `memo` field in the Solana Pay URI (e.g. 'donation-42').
    The outbound webhook payload mirrors this as part of the payment record.
    We also accept a top-level `donation_id` field as a fallback.
    """
    # Method 1: memo field (set by the frontend Solana Pay URI)
    memo = payload.get('memo', '')
    if memo and memo.startswith('donation-'):
        try:
            return int(memo.split('-', 1)[1])
        except (IndexError, ValueError):
            pass

    # Method 2: explicit donation_id field
    try:
        return int(payload['donation_id'])
    except (KeyError, TypeError, ValueError):
        pass

    return None


class StablecoinPaymentWebhookView(APIView):
    """
    Receives payment-received notifications from the Pepea stablecoin aggregator.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Donations - Stablecoin'],
        operation_summary='Stablecoin Payment Webhook (Pepea → RHCI)',
        operation_description="""
        Called by the Pepea aggregator when a USDC / Solana payment is detected
        on-chain at the registered collection address.

        **Security:** Every request carries an `X-Signature` header (HMAC-SHA256
        of the JSON body using `STABLECOIN_WEBHOOK_SECRET`).

        **Payload example:**
        ```json
        {
            "event": "payment.received",
            "payment_id": "abc123",
            "endpoint_id": "...",
            "stablecoin_address": "7xKX...",
            "amount": "25.00",
            "currency": "usdc",
            "chain": "solana",
            "from_address": "sender...",
            "transaction_hash": "...",
            "bridge_status": "payment_processed",
            "bridge_transfer_id": "...",
            "memo": "donation-42",
            "received_at": "2026-03-12T..."
        }
        ```
        """,
        responses={
            200: 'Webhook processed successfully',
            400: 'Invalid payload or signature',
            404: 'Donation not found',
        },
    )
    def post(self, request):
        # ── 1. Read raw body for signature verification ────────────────────
        body_bytes = request.body
        signature = request.headers.get('X-Signature', '')

        secret = getattr(settings, 'STABLECOIN_WEBHOOK_SECRET', '')
        if signature and not _verify_signature(body_bytes, signature, secret):
            logger.warning('[stablecoin_webhook] Invalid signature — request rejected')
            return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)

        # ── 2. Parse payload ────────────────────────────────────────────────
        try:
            payload = request.data
        except Exception:
            return Response({'error': 'Invalid JSON payload'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info('=' * 50)
        logger.info(f'[stablecoin_webhook] Received: {payload}')
        logger.info('=' * 50)

        event = payload.get('event', '')
        if event != 'payment.received':
            # Acknowledge but do nothing for other event types
            return Response({'success': True, 'message': 'Event acknowledged'}, status=status.HTTP_200_OK)

        # ── 3. Extract fields ───────────────────────────────────────────────
        pepea_payment_id = payload.get('payment_id', '')
        amount = payload.get('amount', '0')
        transaction_hash = payload.get('transaction_hash', '')
        bridge_status = payload.get('bridge_status', '')
        chain = payload.get('chain', 'solana')
        currency = payload.get('currency', 'usdc').upper()

        donation_id = _extract_donation_id(payload)
        if not donation_id:
            logger.error(f'[stablecoin_webhook] Could not extract donation_id — payload: {payload}')
            return Response(
                {'error': 'Cannot identify donation — include memo: "donation-<id>" in Solana Pay URI'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 4. Update donation atomically ───────────────────────────────────
        with db_transaction.atomic():
            try:
                donation = Donation.objects.select_for_update().get(id=donation_id)
            except Donation.DoesNotExist:
                logger.error(f'[stablecoin_webhook] Donation {donation_id} not found')
                return Response({'error': f'Donation {donation_id} not found'}, status=status.HTTP_404_NOT_FOUND)

            # Idempotency — ignore if already completed
            if donation.status == 'COMPLETED':
                logger.warning(f'[stablecoin_webhook] Donation {donation_id} already completed — duplicate ignored')
                return Response({'success': True, 'message': 'Already processed'}, status=status.HTTP_200_OK)

            donation.status = 'COMPLETED'
            donation.completed_at = timezone.now()
            donation.transaction_id = transaction_hash or pepea_payment_id
            donation.gateway_reference = pepea_payment_id
            donation.payment_gateway = 'STABLECOIN_SOLANA'
            donation.payment_method = f'USDC on {chain.capitalize()}'
            donation.save()

            # Update patient funding status if applicable
            if donation.patient:
                patient = donation.patient
                if patient.funding_required == 0 or patient.funding_received >= patient.funding_required:
                    patient.status = 'FULLY_FUNDED'
                patient.save()
                logger.info(
                    f'[stablecoin_webhook] Patient {patient.id} funding: '
                    f'{patient.funding_received}/{patient.funding_required} ({patient.funding_percentage}%)'
                )

            logger.info(
                f'✅ [stablecoin_webhook] Donation {donation_id} completed — '
                f'{amount} {currency} | tx: {transaction_hash}'
            )

        response_data = {
            'success': True,
            'message': 'Payment recorded',
            'donation': {
                'id': donation.id,
                'status': donation.status,
                'amount': str(donation.amount),
                'currency': donation.currency,
                'transaction_id': donation.transaction_id,
            },
        }

        if donation.patient and donation.status == 'COMPLETED':
            patient = donation.patient
            response_data['patient'] = {
                'id': patient.id,
                'name': patient.full_name,
                'funding_received': str(patient.funding_received),
                'funding_required': str(patient.funding_required),
                'funding_percentage': round(patient.funding_percentage, 1),
                'status': patient.status,
            }

        return Response(response_data, status=status.HTTP_200_OK)
