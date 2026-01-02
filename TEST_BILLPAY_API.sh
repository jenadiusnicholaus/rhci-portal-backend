#!/bin/bash

# Bill Pay API Test Script
# Tests all 3 Bill Pay API endpoints

BASE_URL="http://localhost:8000/api/donor"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Bill Pay API Test Suite"
echo "=========================================="
echo ""

# Generate JWT token (replace with actual implementation)
# For testing, you'll need to generate a valid JWT token
JWT_SECRET="your-jwt-secret-change-in-production"
HMAC_SECRET="your-hmac-secret-change-in-production"

# For now, use a placeholder token
# In production, generate this using your JWT library
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhemFtcGF5IiwiZXhwIjoxNzM1OTI1NDAwfQ.placeholder"

echo -e "${YELLOW}NOTE: You need to generate a valid JWT token for actual testing${NC}"
echo "JWT Token: $JWT_TOKEN"
echo ""

# Test 1: Name Lookup
echo -e "${YELLOW}Test 1: Name Lookup${NC}"
echo "Endpoint: POST $BASE_URL/merchant/name-lookup"
echo ""

BILL_IDENTIFIER="JIMMY-2024-472"  # Replace with actual bill_identifier from your database

PAYLOAD='{"bill_identifier": "'$BILL_IDENTIFIER'"}'
echo "Payload: $PAYLOAD"
echo ""

# Generate HMAC signature for the payload
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')
echo "HMAC Signature: $SIGNATURE"
echo ""

curl -X POST "$BASE_URL/merchant/name-lookup" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-Signature: $SIGNATURE" \
  -d "$PAYLOAD" \
  -w "\nStatus Code: %{http_code}\n" \
  -s | jq .

echo ""
echo "=========================================="
echo ""

# Test 2: Payment Notification
echo -e "${YELLOW}Test 2: Payment Notification${NC}"
echo "Endpoint: POST $BASE_URL/merchant/payment"
echo ""

PAYMENT_PAYLOAD='{
  "bill_identifier": "'$BILL_IDENTIFIER'",
  "amount": 10000.00,
  "currency": "TZS",
  "phone_number": "255712345678",
  "transaction_id": "AZMPAY-TEST-'$(date +%s)'",
  "payment_method": "Mpesa",
  "payment_date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "customer_name": "John Doe Test"
}'

echo "Payload: $PAYMENT_PAYLOAD"
echo ""

PAYMENT_SIGNATURE=$(echo -n "$PAYMENT_PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')
echo "HMAC Signature: $PAYMENT_SIGNATURE"
echo ""

curl -X POST "$BASE_URL/merchant/payment" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-Signature: $PAYMENT_SIGNATURE" \
  -d "$PAYMENT_PAYLOAD" \
  -w "\nStatus Code: %{http_code}\n" \
  -s | jq .

echo ""
echo "=========================================="
echo ""

# Test 3: Status Check
echo -e "${YELLOW}Test 3: Status Check${NC}"
echo "Endpoint: POST $BASE_URL/merchant/status-check"
echo ""

# Use the transaction_id from Test 2
STATUS_PAYLOAD='{"bill_identifier": "'$BILL_IDENTIFIER'"}'
echo "Payload: $STATUS_PAYLOAD"
echo ""

STATUS_SIGNATURE=$(echo -n "$STATUS_PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')
echo "HMAC Signature: $STATUS_SIGNATURE"
echo ""

curl -X POST "$BASE_URL/merchant/status-check" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-Signature: $STATUS_SIGNATURE" \
  -d "$STATUS_PAYLOAD" \
  -w "\nStatus Code: %{http_code}\n" \
  -s | jq .

echo ""
echo "=========================================="
echo ""

# Test 4: Public Patient Lookup (no auth required)
echo -e "${YELLOW}Test 4: Public Patient Lookup by Bill Identifier${NC}"
echo "Endpoint: GET $BASE_URL/patients/by-bill/$BILL_IDENTIFIER"
echo ""

curl -X GET "$BASE_URL/patients/by-bill/$BILL_IDENTIFIER" \
  -H "Content-Type: application/json" \
  -w "\nStatus Code: %{http_code}\n" \
  -s | jq .

echo ""
echo "=========================================="
echo -e "${GREEN}All tests completed!${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT NOTES:${NC}"
echo "1. Replace JWT_TOKEN with a valid token generated using your JWT secret"
echo "2. Replace BILL_IDENTIFIER with an actual patient bill_identifier from your database"
echo "3. Update JWT_SECRET and HMAC_SECRET in your .env file for production"
echo "4. Make sure you've run migrations: python manage.py migrate patient"
echo "5. Generate bill identifiers for existing patients: python manage.py generate_bill_identifiers"
