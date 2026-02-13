#!/bin/bash
# ============================================================
# Yellow Card API - CURL Test Commands
# ============================================================
# 
# Yellow Card uses HMAC-SHA256 authentication with timestamp
# This script generates proper headers for each request
#
# Usage: ./test_yellowcard_curl.sh
# ============================================================

# Configuration
API_KEY="0392fa1c63d962a064b483013db4a52b"
API_SECRET="41da10bae44592dd28da5577acf7507557a6834e656f372d6c2a9945234bc72b"
BASE_URL="https://sandbox.api.yellowcard.io"

# Function to generate signature
generate_signature() {
    local TIMESTAMP="$1"
    local PATH="$2"
    local METHOD="$3"
    local BODY="$4"
    
    # Build message: timestamp + path + method
    MESSAGE="${TIMESTAMP}${PATH}${METHOD}"
    
    # For POST/PUT, add base64(sha256(body))
    if [[ "$METHOD" == "POST" || "$METHOD" == "PUT" ]] && [[ -n "$BODY" ]]; then
        BODY_HASH=$(echo -n "$BODY" | openssl dgst -sha256 -binary | base64)
        MESSAGE="${MESSAGE}${BODY_HASH}"
    fi
    
    # Generate HMAC-SHA256 signature
    SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_SECRET" -binary | base64)
    echo "$SIGNATURE"
}

# Function to make authenticated request
yc_request() {
    local METHOD="$1"
    local PATH="$2"
    local BODY="$3"
    
    # Generate timestamp (ISO8601 format)
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
    
    # Generate signature
    SIGNATURE=$(generate_signature "$TIMESTAMP" "$PATH" "$METHOD" "$BODY")
    
    echo ""
    echo "============================================================"
    echo "📡 $METHOD $PATH"
    echo "============================================================"
    echo "Timestamp: $TIMESTAMP"
    echo "Authorization: YcHmacV1 $API_KEY:$SIGNATURE"
    echo ""
    
    if [[ "$METHOD" == "GET" ]]; then
        curl -s -X GET "${BASE_URL}${PATH}" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            -H "X-YC-Timestamp: $TIMESTAMP" \
            -H "Authorization: YcHmacV1 ${API_KEY}:${SIGNATURE}" | python3 -m json.tool 2>/dev/null || cat
    else
        curl -s -X "$METHOD" "${BASE_URL}${PATH}" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            -H "X-YC-Timestamp: $TIMESTAMP" \
            -H "Authorization: YcHmacV1 ${API_KEY}:${SIGNATURE}" \
            -d "$BODY" | python3 -m json.tool 2>/dev/null || cat
    fi
    echo ""
}

# ============================================================
# TEST 1: Get Channels
# ============================================================
echo ""
echo "🔷 TEST 1: GET CHANNELS"
yc_request "GET" "/business/channels"

# ============================================================
# TEST 2: Get Rates
# ============================================================
echo ""
echo "🔷 TEST 2: GET RATES"
yc_request "GET" "/business/rates"

# ============================================================
# TEST 3: Get Networks
# ============================================================
echo ""
echo "🔷 TEST 3: GET NETWORKS"
yc_request "GET" "/business/networks"

# ============================================================
# TEST 4: Get Payment Reasons (may not work)
# ============================================================
echo ""
echo "🔷 TEST 4: GET PAYMENT REASONS"
yc_request "GET" "/business/reasons"

echo ""
echo "============================================================"
echo "✅ Basic API tests completed!"
echo "============================================================"
echo ""
echo "To test Submit Collection Request, uncomment the section below"
echo ""

# ============================================================
# TEST 5: Submit Collection Request (UNCOMMENT TO TEST)
# ============================================================
# echo ""
# echo "🔷 TEST 5: SUBMIT COLLECTION REQUEST"
# COLLECTION_BODY='{
#     "channelId": "656d4e72-7849-4fd6-b???-???",
#     "amount": "50000",
#     "currency": "TZS",
#     "country": "TZ",
#     "reason": "donation",
#     "network": "VODACOM",
#     "sequenceId": "test-donation-001",
#     "sender": {
#         "name": "John Doe",
#         "phone": "+255712345678",
#         "country": "TZ"
#     }
# }'
# yc_request "POST" "/business/collections" "$COLLECTION_BODY"
