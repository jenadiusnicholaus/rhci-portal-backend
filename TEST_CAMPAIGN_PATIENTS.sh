#!/bin/bash

# Campaign Patient Selection - Test Script
# Test both General Fund and Patient-Specific campaigns

BASE_URL="http://localhost:8080/api/v1"
TOKEN="YOUR_AUTH_TOKEN_HERE"

echo "=========================================="
echo "Campaign Patient Selection Tests"
echo "=========================================="
echo ""

# Test 1: Create General Fund Campaign
echo "Test 1: Create General Fund Campaign"
echo "--------------------------------------"
curl -X POST ${BASE_URL}/campaigns/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "RHCI General Operations Fund 2026",
    "description": "Support our mission to provide healthcare to children in need across Tanzania. Your donation helps us maintain operations, purchase medical equipment, and support our medical partners.",
    "goal_amount": 100000.00,
    "end_date": "2026-12-31",
    "is_general_fund": true
  }' | python3 -m json.tool
echo ""
echo ""

# Test 2: Create Single Patient Campaign
echo "Test 2: Create Single Patient Campaign"
echo "--------------------------------------"
curl -X POST ${BASE_URL}/campaigns/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "Help Sarah Get Heart Surgery",
    "description": "Sarah is a 10-year-old girl from Dar es Salaam who needs urgent heart surgery. Your support can save her life.",
    "goal_amount": 25000.00,
    "end_date": "2026-03-31",
    "is_general_fund": false,
    "patients": [1]
  }' | python3 -m json.tool
echo ""
echo ""

# Test 3: Create Multi-Patient Campaign
echo "Test 3: Create Multi-Patient Campaign"
echo "--------------------------------------"
curl -X POST ${BASE_URL}/campaigns/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "Help 5 Children Get Treatment",
    "description": "These five children all need urgent medical treatment. Together, we can make a difference in all their lives.",
    "goal_amount": 150000.00,
    "end_date": "2026-06-30",
    "is_general_fund": false,
    "patients": [1, 2, 3, 4, 5]
  }' | python3 -m json.tool
echo ""
echo ""

# Test 4: Validation Error - Patient campaign without patients
echo "Test 4: Validation Error - Patient campaign without patients"
echo "--------------------------------------"
curl -X POST ${BASE_URL}/campaigns/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "Invalid Campaign",
    "description": "This should fail validation",
    "goal_amount": 10000.00,
    "end_date": "2026-06-30",
    "is_general_fund": false,
    "patients": []
  }' | python3 -m json.tool
echo ""
echo ""

# Test 5: Validation Error - General fund with patients
echo "Test 5: Validation Error - General fund with patients"
echo "--------------------------------------"
curl -X POST ${BASE_URL}/campaigns/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "Invalid General Fund",
    "description": "This should fail validation",
    "goal_amount": 50000.00,
    "end_date": "2026-06-30",
    "is_general_fund": true,
    "patients": [1, 2]
  }' | python3 -m json.tool
echo ""
echo ""

# Test 6: Get Campaign Details (Check Patient Info)
echo "Test 6: Get Campaign Details"
echo "--------------------------------------"
echo "Replace CAMPAIGN_ID with an actual campaign ID"
# curl -X GET ${BASE_URL}/campaigns/CAMPAIGN_ID/ \
#   -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool
echo ""
echo ""

# Test 7: List All Campaigns
echo "Test 7: List All Campaigns"
echo "--------------------------------------"
curl -X GET ${BASE_URL}/campaigns/ \
  -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool
echo ""
echo ""

echo "=========================================="
echo "Tests Complete!"
echo "=========================================="
