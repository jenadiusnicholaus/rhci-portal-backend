#!/bin/bash

# Financial Reports API Testing Script
# Tests admin upload and public viewing of financial reports

BASE_URL="http://localhost:8090/api/v1.0/auth"
ADMIN_EMAIL="admin@rhci.co.tz"
ADMIN_PASSWORD="admin123"

echo "=================================================="
echo "FINANCIAL REPORTS API TESTING"
echo "=================================================="

# Step 1: Admin Login
echo -e "\n[1] Admin Login"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASSWORD\"
  }")

echo "$LOGIN_RESPONSE" | jq '.'

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.tokens.access')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Login failed! Cannot proceed."
    exit 1
fi

echo "✅ Admin logged in successfully!"
echo "Access Token: ${ACCESS_TOKEN:0:20}..."

# Step 2: Create sample Excel file in base64 (mock financial report)
echo -e "\n[2] Creating Mock Excel Financial Report"

# Create a simple CSV content to simulate Excel
MOCK_EXCEL_CONTENT="Month,Income,Expenses,Balance
January,50000,35000,15000
February,60000,40000,20000
March,75000,45000,30000"

# Convert to base64
EXCEL_BASE64=$(echo "$MOCK_EXCEL_CONTENT" | base64)

# Create data URL (using csv for simplicity, in real case use xlsx)
DOCUMENT_BASE64="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,$EXCEL_BASE64"

# Step 3: Upload Financial Report (Admin)
echo -e "\n[3] Uploading Financial Report"
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/admin/financial-reports/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Q1 2026 Financial Report\",
    \"description\": \"Complete financial transparency report for Q1 2026 including all donations and expenses.\",
    \"document\": \"$DOCUMENT_BASE64\",
    \"is_public\": true
  }")

echo "$UPLOAD_RESPONSE" | jq '.'

REPORT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.id')

if [ "$REPORT_ID" = "null" ] || [ -z "$REPORT_ID" ]; then
    echo "❌ Upload failed!"
else
    echo "✅ Financial report uploaded successfully! ID: $REPORT_ID"
fi

# Step 4: List All Financial Reports (Admin)
echo -e "\n[4] Listing All Financial Reports (Admin View)"
curl -s -X GET "$BASE_URL/admin/financial-reports/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

# Step 5: Get Public Financial Report (No Auth Required)
echo -e "\n[5] Getting Public Financial Report (Community View)"
curl -s -X GET "$BASE_URL/financial-report/public/" | jq '.'

# Step 6: Upload Another Report (Not Public)
echo -e "\n[6] Uploading Second Report (Private)"
curl -s -X POST "$BASE_URL/admin/financial-reports/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Q4 2025 Financial Report\",
    \"description\": \"Previous quarter financial data for internal review.\",
    \"document\": \"$DOCUMENT_BASE64\",
    \"is_public\": false
  }" | jq '.'

# Step 7: List All Reports Again
echo -e "\n[7] Listing All Reports (Should Show Both)"
curl -s -X GET "$BASE_URL/admin/financial-reports/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

# Step 8: Update Report to Make it Public
if [ "$REPORT_ID" != "null" ] && [ -n "$REPORT_ID" ]; then
    echo -e "\n[8] Updating Report $REPORT_ID"
    curl -s -X PATCH "$BASE_URL/admin/financial-reports/$REPORT_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"description\": \"Updated: Complete financial transparency report for Q1 2026\"
      }" | jq '.'
fi

# Step 9: Delete a Report
if [ "$REPORT_ID" != "null" ] && [ -n "$REPORT_ID" ]; then
    echo -e "\n[9] Deleting Report $REPORT_ID"
    DELETE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X DELETE "$BASE_URL/admin/financial-reports/$REPORT_ID/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    HTTP_STATUS=$(echo "$DELETE_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    
    if [ "$HTTP_STATUS" = "204" ]; then
        echo "✅ Report deleted successfully!"
    else
        echo "❌ Delete failed with status: $HTTP_STATUS"
    fi
fi

echo -e "\n=================================================="
echo "TESTING COMPLETE"
echo "=================================================="
echo ""
echo "API ENDPOINTS:"
echo "  Admin List/Create:  POST/GET $BASE_URL/admin/financial-reports/"
echo "  Admin Detail:       GET/PUT/PATCH/DELETE $BASE_URL/admin/financial-reports/{id}/"
echo "  Public View:        GET $BASE_URL/financial-report/public/"
echo ""
echo "FEATURES:"
echo "  ✅ Base64 Excel/PDF document upload (max 20MB)"
echo "  ✅ Multiple reports with admin-only access"
echo "  ✅ Mark one report as public for community transparency"
echo "  ✅ Auto-unmarking previous public report when new one is published"
echo "  ✅ Full CRUD operations for admin"
echo "  ✅ Public endpoint for community viewing"
