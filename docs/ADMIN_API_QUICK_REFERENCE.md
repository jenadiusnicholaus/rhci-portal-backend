# RHCI Portal - Admin API Quick Reference

## 🔑 Authentication
```bash
# Login as admin
POST /api/auth/login/
{
  "email": "admin@rhci.org",
  "password": "your_password"
}

# Use token in headers
Authorization: Bearer <access_token>
```

## 👥 Admin Patient Management

### List Patients
```bash
GET /api/auth/admin/patients/
  ?status=SUBMITTED           # Filter by status
  &country=Kenya             # Filter by country
  &verified=false            # Filter by verification
  &search=heart              # Search term
  &ordering=-created_at      # Order results
```

### View/Edit Patient
```bash
# View
GET /api/auth/admin/patients/{id}/

# Edit
PATCH /api/auth/admin/patients/{id}/
{
  "diagnosis": "Heart condition",
  "treatment_needed": "Surgery",
  "medical_partner": "Hospital Name",
  "treatment_date": "2025-12-15",
  "funding_required": "15000.00",
  "total_treatment_cost": "20000.00"
}
```

### Approve/Reject
```bash
POST /api/auth/admin/patients/{id}/approve/

# Approve
{"action": "approve"}

# Reject
{
  "action": "reject",
  "rejection_reason": "Incomplete information"
}
```

### Publish
```bash
POST /api/auth/admin/patients/{id}/publish/
{
  "publish": true,
  "featured": true  # Optional: feature on homepage
}
```

## 📅 Admin Timeline Management

### View Timeline
```bash
GET /api/auth/admin/patients/{patient_id}/timeline/
```

### Create Event
```bash
POST /api/auth/admin/timeline/create/
{
  "patient_profile": 1,
  "event_type": "UPDATE_POSTED",
  "title": "Surgery Successful",
  "description": "Patient completed surgery successfully",
  "event_date": "2025-12-15",       # Optional: for TBD events
  "is_milestone": true,
  "is_visible": true,
  "is_current_state": true,
  "metadata": {"location": "Ward 5"}  # Optional
}
```

### Update Event
```bash
PATCH /api/auth/admin/timeline/{id}/update/
{
  "title": "Updated Title",
  "is_current_state": true  # Unmarks all others
}
```

### Delete Event
```bash
DELETE /api/auth/admin/timeline/{id}/delete/
```

## 🌐 Public Patient API (No Auth)

### List Public Patients
```bash
GET /api/auth/public/patients/
  ?country=Kenya
  &medical_partner=Hospital
  &funding_status=awaiting_funding  # awaiting_funding, fully_funded, partially_funded
  &search=heart
  &ordering=-funding_percentage
```

### View Patient Detail
```bash
GET /api/auth/public/patients/{id}/
```

### Featured Patients (Homepage)
```bash
GET /api/auth/public/patients/featured/
```

## 📊 Event Types

| Event Type | Description | Auto-Generated |
|------------|-------------|----------------|
| `PROFILE_SUBMITTED` | Profile submitted | ✅ On registration |
| `TREATMENT_SCHEDULED` | Treatment scheduled | ✅ When treatment_date set |
| `PROFILE_PUBLISHED` | Profile published | ✅ When published |
| `AWAITING_FUNDING` | Awaiting funding | ✅ When published with funding |
| `FUNDING_MILESTONE` | Funding milestone | ✅ At 25%, 50%, 75% |
| `FULLY_FUNDED` | Fully funded | ✅ At 100% |
| `TREATMENT_STARTED` | Treatment started | ❌ Manual |
| `TREATMENT_COMPLETE` | Treatment complete | ✅ Status change |
| `UPDATE_POSTED` | Update posted | ❌ Manual |
| `STATUS_CHANGED` | Status changed | ✅ On status change |

## 🔐 Patient Statuses

| Status | Visible to Public | Description |
|--------|-------------------|-------------|
| `SUBMITTED` | ❌ No | Awaiting admin review |
| `SCHEDULED` | ❌ No | Treatment scheduled, not yet published |
| `PUBLISHED` | ✅ Yes | Published, no funding needed |
| `AWAITING_FUNDING` | ✅ Yes | Published, seeking funding |
| `FULLY_FUNDED` | ✅ Yes | Funding complete |
| `TREATMENT_COMPLETE` | ✅ Yes | Treatment finished |

## 🔄 Typical Admin Workflow

```
1. Patient Registers
   └─> Status: SUBMITTED
   └─> Event: PROFILE_SUBMITTED (auto)

2. Admin Reviews
   GET /admin/patients/?status=SUBMITTED

3. Admin Edits Details
   PATCH /admin/patients/{id}/
   └─> Event: TREATMENT_SCHEDULED (auto, if date set)

4. Admin Approves
   POST /admin/patients/{id}/approve/
   └─> User verified & activated
   └─> Event: Profile Approved (auto)

5. Admin Publishes
   POST /admin/patients/{id}/publish/
   └─> Status: PUBLISHED → AWAITING_FUNDING
   └─> Events: PROFILE_PUBLISHED, AWAITING_FUNDING (auto)
   └─> Now visible on public API

6. Funding Updates
   (Update funding_received)
   └─> Events: Milestone events (auto at 25%, 50%, 75%)
   └─> Event: FULLY_FUNDED (auto at 100%)

7. Manual Updates
   POST /admin/timeline/create/
   └─> Add treatment progress updates
```

## 🧪 Quick Test

```bash
# 1. Start server
python manage.py runserver 0.0.0.0:8091

# 2. Run test script
python auth_app/test_admin_api.py

# 3. Or use Swagger
# Open: http://localhost:8091/swagger/
```

## 📚 Full Documentation

- **Comprehensive API Docs:** `ADMIN_API_DOCUMENTATION.md`
- **Implementation Summary:** `ADMIN_IMPLEMENTATION_SUMMARY.md`
- **Interactive Test:** `auth_app/test_admin_api.py`
- **Swagger UI:** `http://localhost:8091/swagger/`
- **Django Admin:** `http://localhost:8091/admin/`

## 💡 Common Tasks

### Mark patient as featured
```bash
POST /api/auth/admin/patients/{id}/publish/
{"publish": true, "featured": true}
```

### Add progress update
```bash
POST /api/auth/admin/timeline/create/
{
  "patient_profile": 1,
  "event_type": "UPDATE_POSTED",
  "title": "Surgery Complete",
  "description": "...",
  "is_current_state": true
}
```

### Schedule future event (TBD)
```bash
POST /api/auth/admin/timeline/create/
{
  "patient_profile": 1,
  "event_type": "TREATMENT_STARTED",
  "title": "Surgery Date",
  "description": "...",
  "event_date": "2025-12-15",  # Future date
  "is_milestone": true
}
```

### Filter partially funded patients
```bash
GET /api/auth/public/patients/?funding_status=partially_funded
```

---

**Version:** 1.0.0  
**Last Updated:** November 18, 2025
