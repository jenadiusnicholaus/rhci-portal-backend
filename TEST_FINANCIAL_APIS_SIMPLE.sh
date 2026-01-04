#!/bin/bash

# Simple test showing the two main APIs

BASE_URL="http://localhost:8090/api/v1.0/auth"

echo "=========================================="
echo "TWO MAIN FINANCIAL REPORT APIs"
echo "=========================================="

# API 1: PUBLIC - Get current public financial report (Frontend/Community)
echo -e "\n[API 1] PUBLIC - Get Current Public Report"
echo "Endpoint: GET $BASE_URL/financial-report/public/"
echo "Access: Anyone (No authentication required)"
echo "Purpose: Show current public financial report to frontend/community"
echo -e "\nResponse:"
curl -s -X GET "$BASE_URL/financial-report/public/" | jq '.'

# API 2: ADMIN - List all financial reports
echo -e "\n=========================================="
echo -e "\n[API 2] ADMIN - List All Reports"
echo "Endpoint: GET $BASE_URL/admin/financial-reports/"
echo "Access: Admin only (Bearer token required)"
echo "Purpose: Show all reports to admin (public and private)"

# Login as admin first
echo -e "\nLogging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@rhci.co.tz", "password": "admin123"}')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.tokens.access')

if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ Admin authenticated"
    echo -e "\nResponse:"
    curl -s -X GET "$BASE_URL/admin/financial-reports/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
else
    echo "❌ Admin login failed"
fi

echo -e "\n=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "✅ API 1 (Public): GET $BASE_URL/financial-report/public/"
echo "   → Returns: Current public report for community/frontend"
echo "   → Response: {id, title, description, document_url, uploaded_at}"
echo ""
echo "✅ API 2 (Admin): GET $BASE_URL/admin/financial-reports/"
echo "   → Returns: All reports (public + private) for admin"
echo "   → Response: [{id, title, description, document, document_url, is_public, uploaded_by, ...}, ...]"
echo ""
