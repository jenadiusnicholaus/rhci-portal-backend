#!/bin/bash

# Donation API Testing Script
# Usage: ./TEST_DONATION_APIS.sh

BASE_URL="http://localhost:8000/api/v1.0/donors"

echo "======================================"
echo "🧪 RHCI Donation API Testing"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}TEST 1: Anonymous Donation - Mobile Money${NC}"
echo -e "${BLUE}================================================${NC}"
curl -X POST "${BASE_URL}/donate/azampay/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "amount": 50.00,
    "anonymous_name": "John Doe",
    "anonymous_email": "john@example.com",
    "message": "Get well soon!",
    "donation_type": "ONE_TIME",
    "payment_method": "MOBILE_MONEY",
    "provider": "mpesa",
    "phone_number": "0789123456"
  }'
echo -e "\n\n"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}TEST 2: Anonymous Donation - Airtel Money${NC}"
echo -e "${BLUE}================================================${NC}"
curl -X POST "${BASE_URL}/donate/azampay/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 25.00,
    "anonymous_name": "Jane Smith",
    "anonymous_email": "jane@example.com",
    "message": "Hope this helps",
    "donation_type": "ONE_TIME",
    "payment_method": "MOBILE_MONEY",
    "provider": "airtel",
    "phone_number": "0712345678"
  }'
echo -e "\n\n"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}TEST 3: Anonymous Donation - Monthly Recurring${NC}"
echo -e "${BLUE}================================================${NC}"
curl -X POST "${BASE_URL}/donate/azampay/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "amount": 100.00,
    "anonymous_name": "Anonymous Supporter",
    "anonymous_email": "supporter@example.com",
    "donation_type": "MONTHLY",
    "payment_method": "MOBILE_MONEY",
    "provider": "tigo",
    "phone_number": "0755123456"
  }'
echo -e "\n\n"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}TEST 4: Anonymous Donation - Bank Transfer${NC}"
echo -e "${BLUE}================================================${NC}"
curl -X POST "${BASE_URL}/donate/azampay/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 200.00,
    "anonymous_name": "Generous Donor",
    "anonymous_email": "donor@example.com",
    "payment_method": "BANK",
    "provider": "crdb",
    "merchant_account_number": "1234567890",
    "merchant_mobile_number": "0789123456",
    "otp": "123456"
  }'
echo -e "\n\n"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}TEST 5: Anonymous Donation - General Organization${NC}"
echo -e "${BLUE}================================================${NC}"
curl -X POST "${BASE_URL}/donate/azampay/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 75.00,
    "anonymous_name": "Community Helper",
    "anonymous_email": "helper@example.com",
    "message": "For the organization",
    "payment_method": "MOBILE_MONEY",
    "provider": "halopesa",
    "phone_number": "0765432109"
  }'
echo -e "\n\n"

echo -e "${RED}================================================${NC}"
echo -e "${RED}TEST 6: Anonymous Donation - Missing Fields (Should Fail)${NC}"
echo -e "${RED}================================================${NC}"
curl -X POST "${BASE_URL}/donate/azampay/anonymous/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.00,
    "payment_method": "MOBILE_MONEY",
    "provider": "mpesa",
    "phone_number": "0789123456"
  }'
echo -e "\n\n"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}TEST 7: Authenticated Donation - Mobile Money${NC}"
echo -e "${GREEN}(Replace YOUR_JWT_TOKEN with actual token)${NC}"
echo -e "${GREEN}================================================${NC}"
echo "curl -X POST \"${BASE_URL}/donate/azampay/\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
echo "  -d '{"
echo "    \"patient_id\": 1,"
echo "    \"amount\": 150.00,"
echo "    \"message\": \"Monthly support\","
echo "    \"donation_type\": \"MONTHLY\","
echo "    \"payment_method\": \"MOBILE_MONEY\","
echo "    \"provider\": \"mpesa\","
echo "    \"phone_number\": \"0789123456\""
echo "  }'"
echo -e "\n"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}TEST 8: Authenticated Donation - Bank Transfer${NC}"
echo -e "${GREEN}(Replace YOUR_JWT_TOKEN with actual token)${NC}"
echo -e "${GREEN}================================================${NC}"
echo "curl -X POST \"${BASE_URL}/donate/azampay/\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
echo "  -d '{"
echo "    \"amount\": 500.00,"
echo "    \"payment_method\": \"BANK\","
echo "    \"provider\": \"nmb\","
echo "    \"merchant_account_number\": \"9876543210\","
echo "    \"merchant_mobile_number\": \"0712345678\","
echo "    \"otp\": \"654321\""
echo "  }'"
echo -e "\n"

echo -e "${RED}================================================${NC}"
echo -e "${RED}TEST 9: Authenticated Donation - No Token (Should Fail)${NC}"
echo -e "${RED}================================================${NC}"
curl -X POST "${BASE_URL}/donate/azampay/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.00,
    "payment_method": "MOBILE_MONEY",
    "provider": "mpesa",
    "phone_number": "0789123456"
  }'
echo -e "\n\n"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}TEST 10: Check Payment Status${NC}"
echo -e "${BLUE}(Replace 1 with actual donation_id from above)${NC}"
echo -e "${BLUE}================================================${NC}"
curl -X GET "${BASE_URL}/payment/status/?donation_id=1"
echo -e "\n\n"

echo "======================================"
echo "✅ Testing Complete!"
echo "======================================"
