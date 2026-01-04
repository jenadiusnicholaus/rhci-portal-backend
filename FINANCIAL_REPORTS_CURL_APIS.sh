#!/bin/bash

# Complete Financial Reports API - All Endpoints in cURL
# Base URL
BASE_URL="http://localhost:8090/api/v1.0/auth"

echo "=========================================="
echo "FINANCIAL REPORTS - ALL API ENDPOINTS"
echo "=========================================="

# Step 1: Admin Login (Required for admin operations)
echo -e "\n[STEP 1] Admin Login"
echo "curl -X POST $BASE_URL/login/ \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"email\": \"admin@rhci.co.tz\", \"password\": \"admin123\"}'"
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@rhci.co.tz", "password": "admin123"}')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.tokens.access')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Login failed! Using placeholder token for examples"
    ACCESS_TOKEN="YOUR_ACCESS_TOKEN_HERE"
fi

echo "Response: Access Token: ${ACCESS_TOKEN:0:30}..."

# Step 2: Create/Upload Financial Report
echo -e "\n=========================================="
echo -e "\n[STEP 2] CREATE - Upload Financial Report (Admin)"
echo "POST $BASE_URL/admin/financial-reports/"
echo ""
cat << 'EOF'
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Financial Report",
    "description": "Complete financial transparency report for Q1 2026",
    "document": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,UEsDBBQABgAIAAAAIQDd...",
    "is_public": true
  }'
EOF

# Step 3: List All Reports (Admin)
echo -e "\n=========================================="
echo -e "\n[STEP 3] LIST ALL - Get All Financial Reports (Admin)"
echo "GET $BASE_URL/admin/financial-reports/"
echo ""
cat << EOF
curl -X GET http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
EOF

# Step 4: Get Single Report Details (Admin)
echo -e "\n=========================================="
echo -e "\n[STEP 4] GET ONE - Get Specific Report Details (Admin)"
echo "GET $BASE_URL/admin/financial-reports/{id}/"
echo ""
cat << EOF
curl -X GET http://localhost:8090/api/v1.0/auth/admin/financial-reports/1/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
EOF

# Step 5: Update Report (Full Update)
echo -e "\n=========================================="
echo -e "\n[STEP 5] UPDATE (PUT) - Replace Entire Report (Admin)"
echo "PUT $BASE_URL/admin/financial-reports/{id}/"
echo ""
cat << 'EOF'
curl -X PUT http://localhost:8090/api/v1.0/auth/admin/financial-reports/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Financial Report (Updated)",
    "description": "Updated complete financial transparency report",
    "document": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,UEsDBBQABgAI...",
    "is_public": true
  }'
EOF

# Step 6: Partial Update (PATCH)
echo -e "\n=========================================="
echo -e "\n[STEP 6] UPDATE (PATCH) - Partial Update (Admin)"
echo "PATCH $BASE_URL/admin/financial-reports/{id}/"
echo ""
echo "Example 1: Update only description"
cat << EOF
curl -X PATCH http://localhost:8090/api/v1.0/auth/admin/financial-reports/1/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"description": "Updated description only"}'
EOF

echo -e "\n\nExample 2: Make report public"
cat << EOF
curl -X PATCH http://localhost:8090/api/v1.0/auth/admin/financial-reports/1/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"is_public": true}'
EOF

echo -e "\n\nExample 3: Make report private"
cat << EOF
curl -X PATCH http://localhost:8090/api/v1.0/auth/admin/financial-reports/1/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"is_public": false}'
EOF

# Step 7: Delete Report
echo -e "\n=========================================="
echo -e "\n[STEP 7] DELETE - Remove Financial Report (Admin)"
echo "DELETE $BASE_URL/admin/financial-reports/{id}/"
echo ""
cat << EOF
curl -X DELETE http://localhost:8090/api/v1.0/auth/admin/financial-reports/1/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
EOF

# Step 8: Public API (No Auth)
echo -e "\n=========================================="
echo -e "\n[STEP 8] PUBLIC - Get Current Public Report (Anyone)"
echo "GET $BASE_URL/financial-report/public/"
echo ""
cat << EOF
curl -X GET http://localhost:8090/api/v1.0/auth/financial-report/public/
EOF

echo -e "\n\n=========================================="
echo "TESTING WITH REAL DATA"
echo "=========================================="

if [ "$ACCESS_TOKEN" != "YOUR_ACCESS_TOKEN_HERE" ]; then
    # Create a simple mock document
    MOCK_DOC="UEsDBBQABgAIAAAAIQDd"
    
    echo -e "\n[TEST 1] Creating a financial report..."
    CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/admin/financial-reports/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"title\": \"Test Q1 2026 Report\",
        \"description\": \"Test financial report for demonstration\",
        \"document\": \"data:application/pdf;base64,$MOCK_DOC\",
        \"is_public\": true
      }")
    
    echo "$CREATE_RESPONSE" | jq '.'
    REPORT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
    
    echo -e "\n[TEST 2] Listing all reports..."
    curl -s -X GET "$BASE_URL/admin/financial-reports/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
    
    echo -e "\n[TEST 3] Getting public report (no auth)..."
    curl -s -X GET "$BASE_URL/financial-report/public/" | jq '.'
fi

echo -e "\n=========================================="
echo "COMPLETE API SUMMARY"
echo "=========================================="
echo ""
echo "ADMIN ENDPOINTS (Requires Auth):"
echo "  1. POST   /admin/financial-reports/      - Create new report"
echo "  2. GET    /admin/financial-reports/      - List all reports"
echo "  3. GET    /admin/financial-reports/{id}/ - Get specific report"
echo "  4. PUT    /admin/financial-reports/{id}/ - Full update report"
echo "  5. PATCH  /admin/financial-reports/{id}/ - Partial update report"
echo "  6. DELETE /admin/financial-reports/{id}/ - Delete report"
echo ""
echo "PUBLIC ENDPOINT (No Auth):"
echo "  7. GET    /financial-report/public/      - Get current public report"
echo ""
echo "FILE FORMATS: PDF, XLSX, XLS, DOC, DOCX (Max 20MB)"
echo "ENCODING: Base64 with data URL format"
echo ""
