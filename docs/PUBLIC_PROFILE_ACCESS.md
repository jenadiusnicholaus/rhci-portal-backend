# Public Profile Access Documentation

## Overview
The RHCI Portal supports both private and public profile access for donors and patients.

## Donor Profiles

### Privacy Settings
- **Public Profile** (`is_profile_private=False`): Anyone can view the profile
- **Private Profile** (`is_profile_private=True`): Only the owner can view the profile

---

## Endpoints

### 1. List All Public Donor Profiles

**Endpoint:** `GET /api/auth/donors/`

**Description:** Get a list of all donors with public profiles

**Authentication:** Not required (public access)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "email": "donor1@example.com",
    "photo": "/media/donor_photos/profile1.jpg",
    "full_name": "John Doe",
    "short_bio": "Passionate about helping patients in need",
    "country": "United States",
    "website": "https://johndoe.com",
    "birthday": "1990-05-15",
    "age": 35,
    "workplace": "Tech Company Inc.",
    "is_profile_private": false,
    "created_at": "2025-11-18T10:30:00Z",
    "updated_at": "2025-11-18T15:45:00Z"
  },
  {
    "id": 2,
    "email": "donor2@example.com",
    "photo": null,
    "full_name": "Jane Smith",
    "short_bio": "Supporting healthcare initiatives",
    "country": "Canada",
    "website": "",
    "birthday": "1985-08-20",
    "age": 40,
    "workplace": "Healthcare Corp",
    "is_profile_private": false,
    "created_at": "2025-11-17T08:20:00Z",
    "updated_at": "2025-11-17T08:20:00Z"
  }
]
```

**Note:** Only returns profiles where `is_profile_private=false`

---

### 2. View Single Donor Profile (Public)

**Endpoint:** `GET /api/auth/donors/<id>/`

**Description:** View a specific donor's profile

**Authentication:** Not required for public profiles, required for private profiles (owner only)

**Example:** `GET /api/auth/donors/1/`

**Response (200 OK) - Public Profile:**
```json
{
  "id": 1,
  "email": "donor@example.com",
  "photo": "/media/donor_photos/profile.jpg",
  "full_name": "Jenadius Nicholaus",
  "short_bio": "Passionate about helping patients in need",
  "country": "United States",
  "website": "https://example.com",
  "birthday": "1990-05-15",
  "age": 35,
  "workplace": "Tech Company Inc.",
  "is_profile_private": false,
  "created_at": "2025-11-18T10:30:00Z",
  "updated_at": "2025-11-18T15:45:00Z"
}
```

**Response (403 Forbidden) - Private Profile (non-owner):**
```json
{
  "error": true,
  "error_code": "permission_denied",
  "message": "This profile is private and can only be viewed by the owner.",
  "details": null
}
```

---

### 3. Manage Own Donor Profile (Authenticated)

**Endpoint:** `GET/PATCH/PUT /api/auth/donor/profile/`

**Description:** View and update your own donor profile

**Authentication:** Required (JWT Bearer token, Donor only)

**GET Response (200 OK):**
```json
{
  "id": 1,
  "email": "jnichoraus3@gmail.com",
  "photo": "/media/donor_photos/profile.jpg",
  "full_name": "Jenadius Nicholaus",
  "short_bio": "Passionate about helping patients in need",
  "country": "United States",
  "website": "https://example.com",
  "birthday": "1990-05-15",
  "age": 35,
  "workplace": "Tech Company Inc.",
  "is_profile_private": false,
  "created_at": "2025-11-18T10:30:00Z",
  "updated_at": "2025-11-18T15:45:00Z"
}
```

**PATCH Request - Update Privacy:**
```bash
curl -X PATCH http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_profile_private": true}'
```

**PATCH Response (200 OK):**
```json
{
  "id": 1,
  "email": "jnichoraus3@gmail.com",
  "photo": "/media/donor_photos/profile.jpg",
  "full_name": "Jenadius Nicholaus",
  "short_bio": "Passionate about helping patients in need",
  "country": "United States",
  "website": "https://example.com",
  "birthday": "1990-05-15",
  "age": 35,
  "workplace": "Tech Company Inc.",
  "is_profile_private": true,
  "created_at": "2025-11-18T10:30:00Z",
  "updated_at": "2025-11-18T16:30:00Z"
}
```

---

## Patient Profiles

### Visibility Rules
Patient profiles are visible based on their status:
- **SUBMITTED**: Not visible to public (admin review)
- **SCHEDULED**: Not visible to public (admin processing)
- **PUBLISHED**: Visible to everyone
- **AWAITING_FUNDING**: Visible to everyone
- **FULLY_FUNDED**: Visible to everyone
- **TREATMENT_COMPLETE**: Visible to everyone (success story)

---

### 4. List All Public Patient Profiles

**Endpoint:** `GET /api/auth/patients/`

**Description:** Get a list of all published patient profiles

**Authentication:** Not required (public access)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": 2,
    "full_name": "Sarah Johnson",
    "age": 28,
    "gender": "F",
    "country": "Kenya",
    "short_description": "Young mother needs heart surgery",
    "long_story": "Sarah is a 28-year-old mother of two...",
    "medical_partner": "Nairobi General Hospital",
    "diagnosis": "Congenital heart defect",
    "treatment_needed": "Open heart surgery",
    "treatment_date": "2025-12-15",
    "funding_required": 15000.00,
    "funding_received": 7500.00,
    "total_treatment_cost": 18000.00,
    "funding_percentage": 50.0,
    "funding_remaining": 7500.00,
    "other_contributions": 3000.00,
    "cost_breakdowns": [
      {
        "id": 1,
        "expense_type": 1,
        "expense_type_name": "Hospital Fees",
        "expense_type_slug": "hospital-fees",
        "amount": 8000.00,
        "notes": "Surgery and room charges",
        "created_at": "2025-11-18T10:00:00Z"
      },
      {
        "id": 2,
        "expense_type": 2,
        "expense_type_name": "Medical Staff",
        "expense_type_slug": "medical-staff",
        "amount": 5000.00,
        "notes": "Surgeon and anesthesiologist fees",
        "created_at": "2025-11-18T10:05:00Z"
      }
    ],
    "cost_breakdown_notes": "Total cost breakdown for heart surgery",
    "cost_breakdown_total": 13000.00,
    "status": "AWAITING_FUNDING",
    "created_at": "2025-11-15T09:00:00Z",
    "updated_at": "2025-11-18T14:30:00Z"
  }
]
```

**Note:** Only returns profiles with status: PUBLISHED, AWAITING_FUNDING, or FULLY_FUNDED

---

### 5. View Single Patient Profile (Public)

**Endpoint:** `GET /api/auth/patients/<id>/`

**Description:** View a specific patient's profile

**Authentication:** Not required (public access for published patients)

**Example:** `GET /api/auth/patients/1/`

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 2,
  "full_name": "Sarah Johnson",
  "age": 28,
  "gender": "F",
  "country": "Kenya",
  "short_description": "Young mother needs heart surgery",
  "long_story": "Sarah is a 28-year-old mother of two who was diagnosed...",
  "medical_partner": "Nairobi General Hospital",
  "diagnosis": "Congenital heart defect",
  "treatment_needed": "Open heart surgery",
  "treatment_date": "2025-12-15",
  "funding_required": 15000.00,
  "funding_received": 7500.00,
  "total_treatment_cost": 18000.00,
  "funding_percentage": 50.0,
  "funding_remaining": 7500.00,
  "other_contributions": 3000.00,
  "cost_breakdowns": [...],
  "cost_breakdown_notes": "Total cost breakdown for heart surgery",
  "cost_breakdown_total": 13000.00,
  "status": "AWAITING_FUNDING",
  "created_at": "2025-11-15T09:00:00Z",
  "updated_at": "2025-11-18T14:30:00Z"
}
```

**Response (404 Not Found) - Unpublished Patient:**
```json
{
  "detail": "Not found."
}
```

---

### 6. Manage Own Patient Profile (Authenticated)

**Endpoint:** `GET/PATCH/PUT /api/auth/patient/profile/`

**Description:** View and update your own patient profile

**Authentication:** Required (JWT Bearer token, Patient only)

**Note:** Patients can only update certain fields (gender, country, short_description, long_story). Medical and funding details are admin-only.

---

## Access Control Summary

| Endpoint | Authentication | Who Can Access |
|----------|----------------|----------------|
| `GET /api/auth/donors/` | No | Everyone (public profiles only) |
| `GET /api/auth/donors/<id>/` | No (public), Yes (private) | Everyone for public profiles, Owner only for private |
| `GET/PATCH /api/auth/donor/profile/` | Yes (Donor) | Donor only (own profile) |
| `GET /api/auth/patients/` | No | Everyone (published patients) |
| `GET /api/auth/patients/<id>/` | No | Everyone (published patients) |
| `GET/PATCH /api/auth/patient/profile/` | Yes (Patient) | Patient only (own profile) |

---

## Examples

### Public Access - View All Donors
```bash
# No authentication needed
curl -X GET http://localhost:8091/api/auth/donors/
```

### Public Access - View Specific Donor
```bash
# No authentication needed for public profiles
curl -X GET http://localhost:8091/api/auth/donors/1/
```

### Authenticated - Update Own Profile Privacy
```bash
# Make profile private
curl -X PATCH http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_profile_private": true}'
```

### Public Access - View All Patients Needing Funding
```bash
# No authentication needed
curl -X GET http://localhost:8091/api/auth/patients/
```

### Public Access - View Specific Patient
```bash
# No authentication needed for published patients
curl -X GET http://localhost:8091/api/auth/patients/1/
```

---

## Privacy Best Practices

### For Donors:
1. **Default:** Profiles are public (`is_profile_private=false`)
2. **Make Private:** Set `is_profile_private=true` to hide from public lists
3. **Share URL:** Even with private profile, you can share the direct URL with specific people (they need to be logged in as you)

### For Patients:
1. **Automatic:** Privacy controlled by admin via status field
2. **SUBMITTED/SCHEDULED:** Not visible to public
3. **PUBLISHED onwards:** Visible to everyone for fundraising

---

## Testing

### Test Public Donor List
```bash
curl http://localhost:8091/api/auth/donors/
```

### Test Public Donor Profile
```bash
curl http://localhost:8091/api/auth/donors/1/
```

### Test Private Profile Access (should fail)
```bash
# First, make profile private via authenticated endpoint
curl -X PATCH http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"is_profile_private": true}'

# Then try accessing without auth (should fail)
curl http://localhost:8091/api/auth/donors/1/
```

### Test Public Patient List
```bash
curl http://localhost:8091/api/auth/patients/
```

---

**Last Updated:** November 18, 2025
