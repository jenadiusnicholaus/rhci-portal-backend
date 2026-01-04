#!/bin/bash

# Test script for donation split feature
# Tests: patient_amount + rhci_support_amount = total amount sent to AzamPay

echo "========================================"
echo "DONATION SPLIT FEATURE TEST"
echo "========================================"
echo ""

# Test 1: Patient only (no RHCI support)
echo "Test 1: Patient Only Donation"
echo "Patient: 100, RHCI: 0, Total: 100"
curl -X POST http://localhost:8080/api/v1.0/donors/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 100.00,
    "rhci_support_amount": 0.00,
    "currency": "TZS",
    "message": "Get well soon!",
    "is_anonymous": false
  }'
echo -e "\n"

# Test 2: Patient + RHCI Support
echo "Test 2: Patient + RHCI Support"
echo "Patient: 80, RHCI: 20, Total: 100"
curl -X POST http://localhost:8080/api/v1.0/donors/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 80.00,
    "rhci_support_amount": 20.00,
    "currency": "TZS",
    "message": "Supporting both patient and RHCI!",
    "is_anonymous": false
  }'
echo -e "\n"

# Test 3: Patient + RHCI Support (null RHCI)
echo "Test 3: Patient Only (RHCI null)"
echo "Patient: 50, RHCI: null, Total: 50"
curl -X POST http://localhost:8080/api/v1.0/donors/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 50.00,
    "currency": "TZS",
    "message": "Patient only support",
    "is_anonymous": false
  }'
echo -e "\n"

# Test 4: Validation - Total must be > 0
echo "Test 4: Validation - Should FAIL (total = 0)"
echo "Patient: 0, RHCI: 0, Total: 0"
curl -X POST http://localhost:8080/api/v1.0/donors/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 0.00,
    "rhci_support_amount": 0.00,
    "currency": "TZS",
    "is_anonymous": false
  }'
echo -e "\n"

# Test 5: Validation - Patient amount required if patient selected
echo "Test 5: Validation - Should FAIL (patient selected but amount = 0)"
echo "Patient: 0, RHCI: 50, Total: 50"
curl -X POST http://localhost:8080/api/v1.0/donors/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "patient_amount": 0.00,
    "rhci_support_amount": 50.00,
    "currency": "TZS",
    "is_anonymous": false
  }'
echo -e "\n"

echo "========================================"
echo "PAYMENT FLOW:"
echo "1. Frontend sends patient_amount + rhci_support_amount"
echo "2. Backend calculates total = patient_amount + rhci_support_amount"
echo "3. Send TOTAL to AzamPay (single transaction)"
echo "4. On payment success:"
echo "   - Patient gets credited: patient_amount only"
echo "   - RHCI tracked: rhci_support_amount (filter donations)"
echo "========================================"
