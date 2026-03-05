# Yellow Card Collection Webhook Events

This document describes all the Yellow Card Collection webhook events handled by the RHCI Portal.

## Webhook Endpoint

- **URL**: `/api/v1.0/donors/webhooks/yellowcard/collection/`
- **Method**: POST
- **Authentication**: HMAC-SHA256 signature in `X-YC-Signature` header

## Supported Events (13 Total)

### 1. COLLECTION.CREATED

- **Trigger**: Collection request submitted, undergoing initial validation
- **Status**: `CREATED`
- **Action**: Ensures donation status is PENDING
- **Response**: `{"status": "created", "donation_id": 123}`

### 2. COLLECTION.PENDING_APPROVAL

- **Trigger**: Collection pending client action (accept/deny)
- **Status**: `PENDING_APPROVAL`
- **Action**: Keeps donation as PENDING (waiting for user action)
- **Response**: `{"status": "pending_approval", "donation_id": 123}`

### 3. COLLECTION.PROCESS

- **Trigger**: Collection accepted, undergoing final checks
- **Status**: `PROCESS`
- **Action**: Keeps donation as PENDING (still processing)
- **Response**: `{"status": "process", "donation_id": 123}`

### 4. COLLECTION.PROCESSING

- **Trigger**: Collection being broadcasted on channel
- **Status**: `PROCESSING`
- **Action**: Keeps donation as PENDING (broadcasting in progress)
- **Response**: `{"status": "processing", "donation_id": 123}`

### 5. COLLECTION.PENDING

- **Trigger**: Collection awaiting results from channel
- **Status**: `PENDING`
- **Action**: Ensures donation status is PENDING
- **Response**: `{"status": "pending", "donation_id": 123}`

### 6. COLLECTION.COMPLETE

- **Trigger**: Collection completed successfully
- **Status**: `COMPLETE`
- **Action**:
  - Updates donation to COMPLETED
  - Sets completed_at timestamp
  - Updates patient funding if applicable
  - Marks patient as FULLY_FUNDED if funding goal reached
- **Response**: `{"status": "completed", "donation_id": 123}`

### 7. COLLECTION.FAILED

- **Trigger**: Collection failed
- **Status**: `FAILED`
- **Action**:
  - Updates donation to FAILED
  - Sets failure_reason from errorCode
- **Response**: `{"status": "failed", "donation_id": 123}`

### 8. COLLECTION.EXPIRED

- **Trigger**: Collection not accepted/denied within expiry timeframe
- **Status**: `EXPIRED`
- **Action**:
  - Updates donation to FAILED
  - Sets failure_reason to "Collection expired - not accepted/denied within timeframe"
- **Response**: `{"status": "expired", "donation_id": 123}`

### 9. COLLECTION.CANCELLED

- **Trigger**: Collection cancelled by user or system
- **Status**: `CANCELLED`
- **Action**:
  - Updates donation to FAILED
  - Sets failure_reason to "Collection cancelled - refund will be processed if payment was received"
- **Response**: `{"status": "cancelled", "donation_id": 123}`

### 10. COLLECTION.PENDING_REFUND

- **Trigger**: Collection refund request received and queued
- **Status**: `PENDING_REFUND`
- **Action**:
  - Updates donation to FAILED
  - Sets failure_reason to "Collection refund pending - refund request queued"
- **Response**: `{"status": "pending_refund", "donation_id": 123}`

### 11. COLLECTION.REFUND_PROCESSING

- **Trigger**: Collection refund being processed
- **Status**: `REFUND_PROCESSING`
- **Action**:
  - Updates donation to FAILED
  - Sets failure_reason to "Collection refund processing - waiting for provider feedback"
- **Response**: `{"status": "refund_processing", "donation_id": 123}`

### 12. COLLECTION.REFUND_FAILED

- **Trigger**: Collection refund failed after 5 attempts
- **Status**: `REFUND_FAILED`
- **Action**:
  - Updates donation to FAILED
  - Sets failure_reason to "Collection refund failed - retry after few hours recommended"
- **Response**: `{"status": "refund_failed", "donation_id": 123}`

### 13. COLLECTION.REFUNDED

- **Trigger**: Collection refund is complete
- **Status**: `REFUNDED`
- **Action**:
  - Updates donation to FAILED
  - Sets failure_reason to "Collection refunded - payment returned to customer"
- **Response**: `{"status": "refunded", "donation_id": 123}`

## Webhook Payload Format

```json
{
  "id": "unique-webhook-id",
  "event": "COLLECTION.COMPLETE",
  "status": "COMPLETE",
  "apiKey": "your-api-key",
  "sessionId": "transaction-id",
  "errorCode": "REFUSED", // Optional, for failed events
  "executedAt": "2026-03-05T09:45:00Z"
}
```

## Response Format

### Success Responses

- `200 OK` with JSON body indicating the action taken

### Error Responses

- `400 Bad Request`: Missing required fields
- `401 Unauthorized`: Invalid signature
- `403 Forbidden`: IP not whitelisted (production only)
- `500 Internal Server Error`: Processing error

## Edge Cases Handled

1. **Donation not found**: Returns `{"status": "ignored", "reason": "donation_not_found"}`
2. **Already completed**: Returns `{"status": "already_completed"}`
3. **Already failed**: Returns `{"status": "already_failed"}`
4. **Unhandled event**: Returns `{"status": "ignored", "reason": "unhandled_event"}`

## Security Features

1. **Signature Verification**: HMAC-SHA256 of request body
2. **IP Whitelisting**: Production only (configurable via `YELLOWCARD_WEBHOOK_IPS`)
3. **API Key Validation**: Validates apiKey matches configured key

## Production Setup

1. Create webhook in Yellow Card dashboard:
   - URL: `https://api.rhci.co.tz/webhooks/yellowcard/collection/`
   - Events: `COLLECTION.*` (all collection events)
   - Active: Yes

2. Configure settings:
   - `YELLOWCARD_SECRET_KEY`: For signature verification
   - `YELLOWCARD_WEBHOOK_IPS`: Whitelist Yellow Card IPs (optional)

## Testing

Use the management command to test webhooks:

```bash
# List webhooks
python manage.py setup_yellowcard_webhooks --action=list

# Create webhook (sandbox)
python manage.py setup_yellowcard_webhooks --action=create --url=https://webhook.site/your-id

# Delete webhook
python manage.py setup_yellowcard_webhooks --action=delete --webhook-id=webhook-id
```
