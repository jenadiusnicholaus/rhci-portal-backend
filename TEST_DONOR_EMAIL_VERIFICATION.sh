#!/bin/bash
# Test Donor Email Verification Flow

BASE_URL="http://localhost:8000/api/v1.0/auth"
TEST_EMAIL="test_donor_$(date +%s)@example.com"
TEST_PASSWORD="TestPass12345"

echo "=========================================="
echo "Donor Email Verification Test Script"
echo "=========================================="
echo ""

# 1. Register new donor
echo "1. Registering new donor..."
RESPONSE=$(curl -s -X POST "$BASE_URL/register/donor/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"first_name\": \"Test\",
    \"last_name\": \"Donor\"
  }")

echo "Response: $RESPONSE"
echo ""

# Extract user ID
USER_ID=$(echo $RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')

if [ -z "$USER_ID" ]; then
  echo "❌ Registration failed!"
  exit 1
fi

echo "✅ Donor registered successfully! ID: $USER_ID"
echo "📧 Verification email should be sent to: $TEST_EMAIL"
echo ""

# 2. Try to login (should fail - not verified)
echo "2. Attempting login before verification..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

echo "Response: $LOGIN_RESPONSE"

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
  echo "⚠️  Login succeeded (should have failed - account not verified)"
else
  echo "✅ Login correctly blocked (account not verified)"
fi
echo ""

# 3. Resend verification email
echo "3. Testing resend verification..."
RESEND_RESPONSE=$(curl -s -X POST "$BASE_URL/donor/resend-verification/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\"
  }")

echo "Response: $RESEND_RESPONSE"

if echo "$RESEND_RESPONSE" | grep -q "successfully"; then
  echo "✅ Resend verification successful"
else
  echo "ℹ️  Note: Resend may be rate-limited"
fi
echo ""

# 4. Check database
echo "4. Checking database status..."
echo "Run this SQL query to check user status:"
echo ""
echo "  SELECT email, is_active, is_verified, email_verification_token IS NOT NULL as has_token"
echo "  FROM auth_app_customuser"
echo "  WHERE email = '$TEST_EMAIL';"
echo ""
echo "Expected: is_active=0, is_verified=0, has_token=1"
echo ""

echo "=========================================="
echo "Manual Steps Required:"
echo "=========================================="
echo ""
echo "5. Check your email at: $TEST_EMAIL"
echo "   - Look for email from: reizahealthcareinitiative@gmail.com"
echo "   - Click the verification link"
echo ""
echo "6. After clicking the link, try logging in again:"
echo ""
echo "   curl -X POST '$BASE_URL/login/' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{"
echo "       \"email\": \"$TEST_EMAIL\","
echo "       \"password\": \"$TEST_PASSWORD\""
echo "     }'"
echo ""
echo "Expected: Login should succeed with JWT tokens"
echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="
