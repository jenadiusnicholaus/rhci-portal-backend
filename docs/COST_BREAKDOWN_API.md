# Treatment Cost Breakdown Management API

## Overview
Complete admin API for managing treatment cost breakdown items for patients. Allows creating, listing, updating, and deleting expense items with support for bulk operations.

## Endpoints

### 1. List & Create Cost Breakdowns
**GET** `/api/v1.0/patients/admin/<patient_id>/cost-breakdowns/`
**POST** `/api/v1.0/patients/admin/<patient_id>/cost-breakdowns/`

**Authentication:** Admin only (Bearer token)

**GET Response:**
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "expense_type": 1,
            "expense_type_name": "Hospital Fees",
            "expense_type_slug": "hospital-fees",
            "amount": "7500.00",
            "notes": "",
            "created_at": "2025-11-18T10:06:26.515809Z"
        }
    ]
}
```

**POST Request:**
```json
{
    "expense_type": 4,
    "amount": "2500.00",
    "notes": "X-ray and imaging services"
}
```

**POST Response:**
```json
{
    "id": 161,
    "expense_type": 4,
    "expense_type_name": "Medical Equipment",
    "expense_type_slug": "medical-equipment",
    "amount": "2500.00",
    "notes": "X-ray and imaging services",
    "created_at": "2025-11-29T15:49:00.851785Z"
}
```

### 2. Retrieve, Update & Delete Cost Breakdown
**GET** `/api/v1.0/patients/admin/<patient_id>/cost-breakdowns/<id>/`
**PUT** `/api/v1.0/patients/admin/<patient_id>/cost-breakdowns/<id>/`
**PATCH** `/api/v1.0/patients/admin/<patient_id>/cost-breakdowns/<id>/`
**DELETE** `/api/v1.0/patients/admin/<patient_id>/cost-breakdowns/<id>/`

**Authentication:** Admin only (Bearer token)

**PATCH Request:**
```json
{
    "amount": "3000.00",
    "notes": "Updated: Advanced imaging and X-ray procedures"
}
```

**Response:**
```json
{
    "id": 161,
    "expense_type": 4,
    "expense_type_name": "Medical Equipment",
    "expense_type_slug": "medical-equipment",
    "amount": "3000.00",
    "notes": "Updated: Advanced imaging and X-ray procedures",
    "created_at": "2025-11-29T15:49:00.851785Z"
}
```

### 3. Bulk Create Cost Breakdowns
**POST** `/api/v1.0/patients/admin/<patient_id>/cost-breakdowns/bulk/`

**Authentication:** Admin only (Bearer token)

**Request:**
```json
{
    "items": [
        {
            "expense_type": 5,
            "amount": "1500.00",
            "notes": "Complete blood count and chemistry panel"
        },
        {
            "expense_type": 10,
            "amount": "12000.00",
            "notes": "Surgical procedure costs"
        }
    ]
}
```

**Response:**
```json
{
    "message": "Successfully created 2 cost breakdown items",
    "created_count": 2,
    "total_cost": 13500.0,
    "items": [
        {
            "id": 163,
            "expense_type": 5,
            "expense_type_name": "Lab Tests",
            "expense_type_slug": "lab-tests",
            "amount": "1500.00",
            "notes": "Complete blood count and chemistry panel",
            "created_at": "2025-11-29T15:59:40.226208Z"
        },
        {
            "id": 164,
            "expense_type": 10,
            "expense_type_name": "Surgery Costs",
            "expense_type_slug": "surgery-costs",
            "amount": "12000.00",
            "notes": "Surgical procedure costs",
            "created_at": "2025-11-29T15:59:40.231697Z"
        }
    ]
}
```

## Available Expense Types

| ID | Name | Slug |
|----|------|------|
| 1 | Hospital Fees | hospital-fees |
| 2 | Medical Staff | medical-staff |
| 3 | Medication | medication |
| 4 | Medical Equipment | medical-equipment |
| 5 | Lab Tests | lab-tests |
| 10 | Surgery Costs | surgery-costs |
| 11 | Medical Supplies | medical-supplies |

## Testing Examples

### Get Admin Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1.0/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@rhci.com","password":"admin123"}' | \
  python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])")
```

### List Cost Breakdowns for Patient 1
```bash
curl -s http://localhost:8000/api/v1.0/patients/admin/1/cost-breakdowns/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Create New Cost Breakdown
```bash
curl -s -X POST http://localhost:8000/api/v1.0/patients/admin/1/cost-breakdowns/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expense_type": 4, "amount": "2500.00", "notes": "X-ray and imaging"}' | \
  python -m json.tool
```

### Update Cost Breakdown
```bash
curl -s -X PATCH http://localhost:8000/api/v1.0/patients/admin/1/cost-breakdowns/161/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": "3000.00", "notes": "Updated notes"}' | \
  python -m json.tool
```

### Bulk Create Multiple Items
```bash
curl -s -X POST http://localhost:8000/api/v1.0/patients/admin/1/cost-breakdowns/bulk/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"expense_type": 5, "amount": "1500.00", "notes": "Lab tests"}, {"expense_type": 10, "amount": "12000.00", "notes": "Surgery"}]}' | \
  python -m json.tool
```

### Delete Cost Breakdown
```bash
curl -s -X DELETE http://localhost:8000/api/v1.0/patients/admin/1/cost-breakdowns/161/ \
  -H "Authorization: Bearer $TOKEN"
```

## Features

✅ **List all cost breakdowns** for a patient with pagination
✅ **Create individual** cost breakdown items
✅ **Bulk create** multiple items in one request
✅ **Update** existing items (full or partial)
✅ **Delete** items
✅ **Automatic slug resolution** - expense type names included in response
✅ **Total cost calculation** - automatic sum in bulk create response
✅ **Validation** - expense types must exist
✅ **Admin-only access** - protected endpoints

## Swagger Documentation

All endpoints are documented in Swagger UI with 🔴 NEW labels:
- http://localhost:8000/swagger/

Look for the "Admin - Patient Review & Management" section.

## Implementation Details

**Files Modified:**
- `patient/admin_views.py` - Added 3 view classes (~250 lines)
- `patient/urls.py` - Added 3 URL routes
- Uses existing `TreatmentCostBreakdownSerializer`
- Uses existing `TreatmentCostBreakdown` model

**Related Models:**
- `TreatmentCostBreakdown` (patient/models.py)
- `ExpenseTypeLookup` (patient/models.py)
