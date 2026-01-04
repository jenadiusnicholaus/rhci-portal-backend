#!/bin/bash

# Financial Reports API - All Upload Methods
BASE_URL="http://localhost:8090/api/v1.0/auth"

echo "=========================================="
echo "FINANCIAL REPORTS - 3 UPLOAD METHODS"
echo "=========================================="

# Method 1: Base64 Upload (Programmatic)
echo -e "\n[METHOD 1] BASE64 UPLOAD - For API/Programmatic Upload"
echo "=========================================="
cat << 'EOF'
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Financial Report",
    "description": "Financial transparency report",
    "document": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,UEsDBBQABgAI...",
    "is_public": true
  }'
EOF

# Method 2: Normal File Upload (Form Data)
echo -e "\n\n[METHOD 2] NORMAL FILE UPLOAD - Using multipart/form-data"
echo "=========================================="
cat << 'EOF'
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=Q1 2026 Financial Report" \
  -F "description=Financial transparency report" \
  -F "document=@/path/to/financial_report.xlsx" \
  -F "is_public=true"
EOF

# Method 3: Google Doc URL
echo -e "\n\n[METHOD 3] GOOGLE DOC/DRIVE LINK - No file upload needed"
echo "=========================================="
cat << 'EOF'
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Financial Report",
    "description": "Financial transparency report",
    "google_doc_url": "https://docs.google.com/spreadsheets/d/abc123/edit",
    "is_public": true
  }'
EOF

# Valid Google Doc URLs
echo -e "\n\n[VALID GOOGLE DOC URLS]"
echo "=========================================="
echo "✅ https://docs.google.com/document/d/..."
echo "✅ https://docs.google.com/spreadsheets/d/..."
echo "✅ https://drive.google.com/file/d/..."
echo "✅ https://sheets.google.com/..."

# Testing with Real Data
echo -e "\n\n=========================================="
echo "TESTING LIVE APIs"
echo "=========================================="

# Login
echo -e "\n[1] Admin Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@rhci.co.tz", "password": "admin123"}')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.tokens.access')

if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ Logged in successfully"
    
    # Test Method 3: Google Doc URL
    echo -e "\n[2] Testing Google Doc URL Upload..."
    RESPONSE=$(curl -s -X POST "$BASE_URL/admin/financial-reports/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Q1 2026 Financial Report (Google Doc)",
        "description": "Shared via Google Docs for transparency",
        "google_doc_url": "https://docs.google.com/spreadsheets/d/1abc123def456/edit",
        "is_public": true
      }')
    
    echo "$RESPONSE" | jq '.'
    
    REPORT_ID=$(echo "$RESPONSE" | jq -r '.id')
    
    if [ "$REPORT_ID" != "null" ] && [ -n "$REPORT_ID" ]; then
        echo -e "\n✅ Report created successfully! ID: $REPORT_ID"
        
        # Test Public API
        echo -e "\n[3] Getting Public Report..."
        curl -s -X GET "$BASE_URL/financial-report/public/" | jq '.'
        
        # List all reports
        echo -e "\n[4] Listing All Reports (Admin)..."
        curl -s -X GET "$BASE_URL/admin/financial-reports/" \
          -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
    fi
else
    echo "❌ Login failed"
fi

echo -e "\n=========================================="
echo "COMPLETE EXAMPLES"
echo "=========================================="

# Complete examples for all methods
cat << 'EOF'

Example 1: Upload with Base64
------------------------------
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Report",
    "description": "Financial data",
    "document": "data:application/pdf;base64,JVBERi0xLjQKJ...",
    "is_public": true
  }'

Example 2: Upload Actual File
------------------------------
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Q1 2026 Report" \
  -F "description=Financial data" \
  -F "document=@./financial_report.xlsx" \
  -F "is_public=true"

Example 3: Google Doc Link
---------------------------
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Report",
    "description": "View on Google Docs",
    "google_doc_url": "https://docs.google.com/spreadsheets/d/1abc123/edit",
    "is_public": true
  }'

Example 4: Both File AND Google Doc (Optional)
-----------------------------------------------
curl -X POST http://localhost:8090/api/v1.0/auth/admin/financial-reports/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Report",
    "description": "Available as file and Google Doc",
    "document": "data:application/pdf;base64,JVBERi0xLjQKJ...",
    "google_doc_url": "https://docs.google.com/spreadsheets/d/1abc123/edit",
    "is_public": true
  }'

EOF

echo -e "\n=========================================="
echo "KEY FEATURES"
echo "=========================================="
echo ""
echo "✅ Method 1: Base64 upload (JSON) - For programmatic uploads"
echo "✅ Method 2: Normal file upload (multipart/form-data) - Like traditional forms"
echo "✅ Method 3: Google Doc URL - No file upload, just share link"
echo "✅ Validation: At least one (document OR google_doc_url) must be provided"
echo "✅ Flexibility: Can provide both if needed"
echo "✅ Google URLs: Validates only docs.google.com, drive.google.com, sheets.google.com"
echo ""
