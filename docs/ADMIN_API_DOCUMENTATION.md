# Admin Management API Documentation

## Overview

This document describes the admin-only endpoints for managing patient profiles, approvals, and timeline events.

## Authentication

All admin endpoints require:
- JWT authentication (Bearer token)
- User must have `user_type = 'ADMIN'`
- User must have `is_staff = True`

## Admin Patient Management

### 1. List All Patient Submissions

**Endpoint:** `GET /api/auth/admin/patients/`

**Permission:** Admin only

**Query Parameters:**
- `status` - Filter by status (SUBMITTED, SCHEDULED, PUBLISHED, etc.)
- `country` - Filter by country (case-insensitive)
- `verified` - Filter by verification status (true/false)
- `search` - Search in full_name, country, diagnosis, medical_partner
- `ordering` - Order by created_at, status, funding_percentage (prefix with `-` for descending)

**Example Request:**
```bash
curl -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8091/api/auth/admin/patients/?status=SUBMITTED&ordering=-created_at"
```

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 2,
      "user_email": "patient@example.com",
      "user_verified": false,
      "patient_verified": false,
      "full_name": "John Doe",
      "age": 25,
      "gender": "M",
      "country": "Kenya",
      "short_description": "Brief description...",
      "long_story": "Detailed story...",
      "medical_partner": "",
      "diagnosis": "",
      "treatment_needed": "",
      "treatment_date": null,
      "funding_required": "0.00",
      "funding_received": "0.00",
      "total_treatment_cost": "0.00",
      "funding_percentage": 0,
      "funding_remaining": "0.00",
      "cost_breakdowns": [],
      "cost_breakdown_notes": "",
      "timeline_events": [...],
      "status": "SUBMITTED",
      "created_at": "2025-11-18T10:00:00Z",
      "updated_at": "2025-11-18T10:00:00Z"
    }
  ]
}
```

---

### 2. View/Edit Patient Profile

**Endpoint:** `GET/PATCH/PUT /api/auth/admin/patients/{id}/`

**Permission:** Admin only

**Methods:**
- `GET` - View full patient profile
- `PATCH` - Partial update
- `PUT` - Full update

**Editable Fields:**
- `full_name`, `gender`, `country`
- `short_description`, `long_story`
- `medical_partner`, `diagnosis`, `treatment_needed`, `treatment_date`
- `funding_required`, `funding_received`, `total_treatment_cost`
- `cost_breakdown_notes`, `status`

**Example PATCH Request:**
```bash
curl -X PATCH \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "diagnosis": "Heart condition requiring surgery",
    "treatment_needed": "Cardiac surgery",
    "medical_partner": "Kenyatta National Hospital",
    "treatment_date": "2025-12-15",
    "funding_required": "15000.00",
    "total_treatment_cost": "20000.00"
  }' \
  "http://localhost:8091/api/auth/admin/patients/1/"
```

---

### 3. Approve or Reject Patient Profile

**Endpoint:** `POST /api/auth/admin/patients/{id}/approve/`

**Permission:** Admin only

**Request Body:**
```json
{
  "action": "approve",  // or "reject"
  "rejection_reason": "Required for rejection"
}
```

**Approve Action:**
- Sets `user.is_verified = True`
- Sets `user.is_patient_verified = True`
- Sets `user.is_active = True`
- Creates "Profile Approved" timeline event
- Clears any previous rejection reason

**Reject Action:**
- Sets `user.is_patient_verified = False`
- Saves rejection reason
- Creates "Profile Rejected" timeline event (not visible to public)
- Sends email notification to patient (TODO)

**Example Approve Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}' \
  "http://localhost:8091/api/auth/admin/patients/1/approve/"
```

**Example Reject Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "rejection_reason": "Incomplete medical information. Please provide detailed diagnosis."
  }' \
  "http://localhost:8091/api/auth/admin/patients/1/approve/"
```

---

### 4. Publish Patient Profile

**Endpoint:** `POST /api/auth/admin/patients/{id}/publish/`

**Permission:** Admin only

**Request Body:**
```json
{
  "publish": true,      // true to publish, false to unpublish
  "featured": false     // Optional: feature on homepage
}
```

**Publish Action:**
- Validates patient is verified
- Sets `status = 'PUBLISHED'`
- Creates "Profile Published" timeline event
- If funding needed, creates "Awaiting Funding" event and sets status to 'AWAITING_FUNDING'
- Optionally marks as featured

**Example Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"publish": true, "featured": true}' \
  "http://localhost:8091/api/auth/admin/patients/1/publish/"
```

**Response:**
```json
{
  "message": "Patient profile published successfully.",
  "patient": { ... }
}
```

---

## Admin Timeline Management

### 5. List Timeline Events for Patient

**Endpoint:** `GET /api/auth/admin/patients/{patient_id}/timeline/`

**Permission:** Admin only

**Response:**
```json
[
  {
    "id": 1,
    "patient_profile": 1,
    "event_type": "PROFILE_SUBMITTED",
    "event_type_display": "Profile Submitted",
    "title": "PROFILE SUBMITTED",
    "description": "Patient submitted profile for review",
    "event_date": null,
    "created_by": 1,
    "created_by_name": "Admin User",
    "metadata": {},
    "is_milestone": true,
    "is_visible": true,
    "is_current_state": false,
    "formatted_date": "November 18, 2025",
    "created_at": "2025-11-18T10:00:00Z",
    "updated_at": "2025-11-18T10:00:00Z"
  }
]
```

---

### 6. Create Timeline Event

**Endpoint:** `POST /api/auth/admin/timeline/create/`

**Permission:** Admin only

**Request Body:**
```json
{
  "patient_profile": 1,
  "event_type": "UPDATE_POSTED",
  "title": "Treatment Progress Update",
  "description": "Patient is recovering well after surgery",
  "event_date": "2025-12-20",  // Optional: for TBD events
  "metadata": {"location": "Hospital Ward"},  // Optional
  "is_milestone": false,
  "is_visible": true,
  "is_current_state": true  // Mark as current state
}
```

**Available Event Types:**
- `PROFILE_SUBMITTED` - Profile Submitted
- `TREATMENT_SCHEDULED` - Treatment Scheduled
- `PROFILE_PUBLISHED` - Profile Published
- `AWAITING_FUNDING` - Awaiting Funding
- `FUNDING_MILESTONE` - Funding Milestone Reached
- `FULLY_FUNDED` - Fully Funded
- `TREATMENT_STARTED` - Treatment Started
- `TREATMENT_COMPLETE` - Treatment Complete
- `UPDATE_POSTED` - Update Posted
- `STATUS_CHANGED` - Status Changed

**Example Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_profile": 1,
    "event_type": "TREATMENT_STARTED",
    "title": "Surgery Commenced",
    "description": "Patient has begun cardiac surgery at Kenyatta National Hospital",
    "event_date": "2025-12-15",
    "is_milestone": true,
    "is_visible": true,
    "is_current_state": true
  }' \
  "http://localhost:8091/api/auth/admin/timeline/create/"
```

---

### 7. Update Timeline Event

**Endpoint:** `PATCH/PUT /api/auth/admin/timeline/{id}/update/`

**Permission:** Admin only

**Note:** If setting `is_current_state = true`, all other events for that patient will be unmarked.

**Example Request:**
```bash
curl -X PATCH \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "description": "Updated description",
    "is_current_state": true
  }' \
  "http://localhost:8091/api/auth/admin/timeline/1/update/"
```

---

### 8. Delete Timeline Event

**Endpoint:** `DELETE /api/auth/admin/timeline/{id}/delete/`

**Permission:** Admin only

**Note:** Cannot delete auto-generated milestone events (PROFILE_SUBMITTED, PROFILE_PUBLISHED, FULLY_FUNDED)

**Example Request:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8091/api/auth/admin/timeline/5/delete/"
```

**Success Response:**
```json
{
  "message": "Timeline event deleted successfully."
}
```

**Error Response (protected event):**
```json
{
  "error": true,
  "message": "Cannot delete auto-generated milestone events."
}
```

---

## Public Patient Profile API

### 9. List Public Patients

**Endpoint:** `GET /api/auth/public/patients/`

**Permission:** Public (no authentication required)

**Filters:**
- Only shows `is_patient_verified = True`
- Only shows status: PUBLISHED, AWAITING_FUNDING, FULLY_FUNDED

**Query Parameters:**
- `country` - Filter by country
- `medical_partner` - Filter by medical partner
- `funding_status` - Filter by funding (fully_funded, awaiting_funding, partially_funded)
- `search` - Search full_name, country, diagnosis, medical_partner
- `ordering` - Order by created_at, funding_percentage

**Example Request:**
```bash
curl "http://localhost:8091/api/auth/public/patients/?country=Kenya&ordering=-funding_percentage"
```

---

### 10. View Public Patient Detail

**Endpoint:** `GET /api/auth/public/patients/{id}/`

**Permission:** Public (no authentication required)

**Returns:** Full patient profile with timeline, cost breakdown, funding details

**Example Request:**
```bash
curl "http://localhost:8091/api/auth/public/patients/1/"
```

---

### 11. Featured Patients (Homepage)

**Endpoint:** `GET /api/auth/public/patients/featured/`

**Permission:** Public (no authentication required)

**Returns:** Maximum 6 featured patients marked with `is_featured = True`

**Example Request:**
```bash
curl "http://localhost:8091/api/auth/public/patients/featured/"
```

---

## Business Logic & Automation

### Automatic Timeline Events

The system automatically creates timeline events for:

1. **Profile Submission** - Created when patient registers
   - Event: `PROFILE_SUBMITTED`
   - Trigger: Patient registration

2. **Treatment Scheduled** - Created when treatment_date is set
   - Event: `TREATMENT_SCHEDULED`
   - Trigger: Admin sets `treatment_date`

3. **Profile Published** - Created when admin publishes
   - Event: `PROFILE_PUBLISHED`
   - Trigger: Admin publishes profile

4. **Awaiting Funding** - Created when published with funding needed
   - Event: `AWAITING_FUNDING`
   - Trigger: Publish with `funding_required > funding_received`
   - Marked as `is_current_state = True`

5. **Funding Milestones** - Created at 25%, 50%, 75% funding
   - Event: `FUNDING_MILESTONE`
   - Trigger: Funding crosses milestone threshold
   - Marked as `is_milestone = True`

6. **Fully Funded** - Created when 100% funded
   - Event: `FULLY_FUNDED`
   - Trigger: `funding_received >= funding_required`
   - Status changes to `FULLY_FUNDED`

7. **Status Changes** - Track all status transitions
   - Event: `STATUS_CHANGED`
   - Trigger: Any status field change

---

## Workflow Summary

### Patient Submission Flow

1. **Patient registers** → Profile created with status `SUBMITTED`
2. **Auto-event:** "PROFILE SUBMITTED" timeline event created
3. **Admin reviews** via `GET /admin/patients/`
4. **Admin edits** medical details via `PATCH /admin/patients/{id}/`
5. **Admin approves** via `POST /admin/patients/{id}/approve/`
   - User verified and activated
   - "Profile Approved" event created
6. **Admin publishes** via `POST /admin/patients/{id}/publish/`
   - Status → `PUBLISHED`
   - "Profile Published" event created
   - If funding needed → "Awaiting Funding" event + status → `AWAITING_FUNDING`
7. **Profile visible** on `GET /public/patients/`

### Timeline Management Flow

1. **Admin adds manual event** via `POST /admin/timeline/create/`
2. **Admin marks as current state** via `PATCH /admin/timeline/{id}/update/`
3. **Admin adds TBD event** with future `event_date`
4. **System auto-generates** events for status/funding changes

---

## Error Handling

All admin endpoints return consistent error responses:

```json
{
  "error": true,
  "error_code": "PERMISSION_DENIED",
  "message": "You do not have permission to perform this action.",
  "details": {}
}
```

Common error codes:
- `PERMISSION_DENIED` - Not an admin user
- `NOT_FOUND` - Patient/Timeline not found
- `VALIDATION_ERROR` - Invalid data
- `BAD_REQUEST` - Business logic violation

---

## Testing with Swagger

All endpoints are documented in Swagger UI at:
```
http://localhost:8091/swagger/
```

Use the "Authorize" button to add your admin JWT token.
