# Admin Patient Management API Documentation

Complete API reference for administrators to manage patient profiles, submissions, and donation configurations.

---

## Table of Contents
1. [Patient Review & Approval](#patient-review--approval)
2. [Comprehensive Patient Management](#comprehensive-patient-management)
3. [Donation Amount Management](#donation-amount-management)
4. [Statistics & Analytics](#statistics--analytics)

---

## Patient Review & Approval

### 1. List All Patient Submissions
**Endpoint:** `GET /patients/admin/`  
**Name:** `patients_admin_list`  
**Description:** Retrieve all patient submissions for admin review

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status` (optional): Filter by approval status (`pending`, `approved`, `rejected`)
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://api.example.com/patients/admin/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "status": "pending",
      "is_approved": false,
      "is_published": false,
      "created_at": "2025-11-20T10:30:00Z"
    }
  ]
}
```

---

### 2. View Patient Details
**Endpoint:** `GET /patients/admin/{id}/`  
**Name:** `patients_admin_read`  
**Description:** Get detailed information about a specific patient

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `id` (required): Patient ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 5,
    "email": "patient@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "full_name": "John Doe",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "country": "Kenya",
  "medical_condition": "Heart condition requiring surgery",
  "funding_goal": "50000.00",
  "current_funding": "12500.00",
  "photo": "http://api.example.com/media/patient_photos/patient_1.jpg",
  "photo_url": "http://api.example.com/media/patient_photos/patient_1.jpg",
  "status": "pending",
  "is_approved": false,
  "is_published": false,
  "created_at": "2025-11-20T10:30:00Z",
  "updated_at": "2025-11-20T10:30:00Z"
}
```

---

### 3. Edit Patient Profile (Full Update)
**Endpoint:** `PUT /patients/admin/{id}/`  
**Name:** `patients_admin_update`  
**Description:** Completely update a patient's profile (all fields required)

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `id` (required): Patient ID

**Request Body:**
```json
{
  "full_name": "John Doe",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "country": "Kenya",
  "medical_condition": "Updated medical condition",
  "funding_goal": "60000.00"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "medical_condition": "Updated medical condition",
  "funding_goal": "60000.00",
  "updated_at": "2025-11-22T14:30:00Z"
}
```

---

### 4. Edit Patient Profile (Partial Update)
**Endpoint:** `PATCH /patients/admin/{id}/`  
**Name:** `patients_admin_partial_update`  
**Description:** Update specific fields of a patient's profile

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `id` (required): Patient ID

**Request Body (any fields):**
```json
{
  "funding_goal": "55000.00",
  "medical_condition": "Updated condition description"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "funding_goal": "55000.00",
  "medical_condition": "Updated condition description",
  "updated_at": "2025-11-22T14:35:00Z"
}
```

---

### 5. Approve/Reject Patient
**Endpoint:** `POST /patients/admin/{id}/approve/`  
**Name:** `patients_admin_approve_create`  
**Description:** Approve or reject a patient submission

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `id` (required): Patient ID

**Request Body:**
```json
{
  "is_approved": true,
  "admin_notes": "Profile verified and approved for fundraising"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "is_approved": true,
  "status": "approved",
  "admin_notes": "Profile verified and approved for fundraising",
  "approved_at": "2025-11-22T15:00:00Z"
}
```

---

### 6. Publish/Unpublish Patient
**Endpoint:** `POST /patients/admin/{id}/publish/`  
**Name:** `patients_admin_publish_create`  
**Description:** Make patient profile visible or hidden on public platform

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `id` (required): Patient ID

**Request Body:**
```json
{
  "is_published": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "is_published": true,
  "published_at": "2025-11-22T15:10:00Z",
  "message": "Patient profile is now live on the platform"
}
```

---

## Comprehensive Patient Management

### 7. List All Patients (Advanced)
**Endpoint:** `GET /patients/admin/manage/`  
**Name:** `patients_admin_manage_list`  
**Description:** Advanced patient listing with comprehensive filtering and search

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status` (optional): Filter by approval status
- `country` (optional): Filter by country
- `gender` (optional): Filter by gender (`male`, `female`, `other`)
- `is_published` (optional): Filter by publication status (`true`, `false`)
- `funding_status` (optional): Filter by funding progress (`not_started`, `in_progress`, `completed`)
- `search` (optional): Search across name, email, medical condition
- `created_from` (optional): Filter by creation date (YYYY-MM-DD)
- `created_to` (optional): Filter by creation date (YYYY-MM-DD)
- `ordering` (optional): Sort results (`-created_at`, `funding_goal`, `full_name`)
- `page` (optional): Page number
- `page_size` (optional): Results per page

**Example Request:**
```http
GET /patients/admin/manage/?status=approved&country=Kenya&search=heart&ordering=-created_at&page=1&page_size=20
```

**Response (200 OK):**
```json
{
  "count": 45,
  "next": "http://api.example.com/patients/admin/manage/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 5,
        "email": "patient@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "full_name": "John Doe",
      "date_of_birth": "1990-05-15",
      "gender": "male",
      "country": "Kenya",
      "medical_condition": "Heart surgery required",
      "funding_goal": "50000.00",
      "current_funding": "12500.00",
      "funding_percentage": 25,
      "photo_url": "http://api.example.com/media/patient_photos/patient_1.jpg",
      "status": "approved",
      "is_approved": true,
      "is_published": true,
      "created_at": "2025-11-20T10:30:00Z",
      "updated_at": "2025-11-22T15:10:00Z"
    }
  ]
}
```

---

### 8. Create New Patient
**Endpoint:** `POST /patients/admin/manage/`  
**Name:** `patients_admin_manage_create`  
**Description:** Admin creates a new patient profile with user account

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```json
{
  "email": "newpatient@example.com",
  "password": "SecurePassword123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "full_name": "Jane Smith",
  "date_of_birth": "1985-03-20",
  "gender": "female",
  "country": "Uganda",
  "medical_condition": "Cancer treatment needed",
  "funding_goal": "75000.00",
  "photo": "<file_upload>",
  "is_approved": true,
  "is_published": false
}
```

**Response (201 Created):**
```json
{
  "id": 25,
  "user": {
    "id": 50,
    "email": "newpatient@example.com",
    "first_name": "Jane",
    "last_name": "Smith"
  },
  "full_name": "Jane Smith",
  "medical_condition": "Cancer treatment needed",
  "funding_goal": "75000.00",
  "is_approved": true,
  "is_published": false,
  "created_at": "2025-11-22T16:00:00Z",
  "message": "Patient profile and user account created successfully"
}
```

---

### 9. Get Patient Details (Management)
**Endpoint:** `GET /patients/admin/manage/{id}/`  
**Name:** `patients_admin_manage_read`  
**Description:** Get comprehensive patient details including user account info

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `id` (required): Patient ID

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 5,
    "email": "patient@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "date_joined": "2025-11-20T10:00:00Z"
  },
  "full_name": "John Doe",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "country": "Kenya",
  "medical_condition": "Heart condition requiring surgery",
  "funding_goal": "50000.00",
  "current_funding": "12500.00",
  "funding_percentage": 25,
  "photo_url": "http://api.example.com/media/patient_photos/patient_1.jpg",
  "status": "approved",
  "is_approved": true,
  "is_published": true,
  "admin_notes": "Verified medical records",
  "created_at": "2025-11-20T10:30:00Z",
  "updated_at": "2025-11-22T15:10:00Z",
  "approved_at": "2025-11-21T09:00:00Z",
  "published_at": "2025-11-22T15:10:00Z"
}
```

---

### 10. Update Patient (Full)
**Endpoint:** `PUT /patients/admin/manage/{id}/`  
**Name:** `patients_admin_manage_update`  
**Description:** Completely update patient profile (all fields required)

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `id` (required): Patient ID

**Request Body:**
```json
{
  "full_name": "John Doe",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "country": "Kenya",
  "medical_condition": "Updated comprehensive medical condition",
  "funding_goal": "65000.00",
  "is_approved": true,
  "is_published": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "full_name": "John Doe",
  "funding_goal": "65000.00",
  "medical_condition": "Updated comprehensive medical condition",
  "is_approved": true,
  "is_published": true,
  "updated_at": "2025-11-22T16:30:00Z"
}
```

---

### 11. Partial Update Patient
**Endpoint:** `PATCH /patients/admin/manage/{id}/`  
**Name:** `patients_admin_manage_partial_update`  
**Description:** Update specific patient fields

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `id` (required): Patient ID

**Request Body (any fields):**
```json
{
  "medical_condition": "Updated medical notes",
  "is_published": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "medical_condition": "Updated medical notes",
  "is_published": true,
  "updated_at": "2025-11-22T16:35:00Z"
}
```

---

### 12. Delete Patient
**Endpoint:** `DELETE /patients/admin/manage/{id}/`  
**Name:** `patients_admin_manage_delete`  
**Description:** Permanently delete a patient profile

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `id` (required): Patient ID

**Response (204 No Content):**
```
(Empty response body)
```

**Note:** This action is irreversible and will also delete associated data.

---

### 13. Bulk Patient Actions
**Endpoint:** `POST /patients/admin/manage/bulk-actions/`  
**Name:** `patients_admin_manage_bulk-actions_create`  
**Description:** Perform bulk operations on multiple patients

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "action": "approve",
  "patient_ids": [1, 2, 3, 4, 5],
  "notes": "Bulk approval after verification"
}
```

**Available Actions:**
- `approve` - Approve multiple patients
- `reject` - Reject multiple patients
- `publish` - Publish multiple patients
- `unpublish` - Unpublish multiple patients
- `delete` - Delete multiple patients

**Response (200 OK):**
```json
{
  "success": true,
  "action": "approve",
  "processed_count": 5,
  "successful_ids": [1, 2, 3, 4, 5],
  "failed_ids": [],
  "message": "Successfully approved 5 patients"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "action": "approve",
  "processed_count": 3,
  "successful_ids": [1, 2, 3],
  "failed_ids": [4, 5],
  "errors": {
    "4": "Patient already approved",
    "5": "Patient does not exist"
  },
  "message": "Processed 3 of 5 patients. 2 failed."
}
```

---

## Donation Amount Management

### 14. List Patient Donation Amounts
**Endpoint:** `GET /patients/admin/{patient_id}/donation-amounts/`  
**Name:** `patients_admin_donation-amounts_list`  
**Description:** Get all donation amount options for a patient

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `patient_id` (required): Patient ID

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "patient": 1,
    "amount": "10.00",
    "label": "Basic Support",
    "is_active": true,
    "display_order": 1,
    "created_at": "2025-11-20T10:30:00Z"
  },
  {
    "id": 2,
    "patient": 1,
    "amount": "25.00",
    "label": "Standard Support",
    "is_active": true,
    "display_order": 2,
    "created_at": "2025-11-20T10:30:00Z"
  }
]
```

---

### 15. Create Donation Amount Option
**Endpoint:** `POST /patients/admin/{patient_id}/donation-amounts/`  
**Name:** `patients_admin_donation-amounts_create`  
**Description:** Add a new donation amount option for patient

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `patient_id` (required): Patient ID

**Request Body:**
```json
{
  "amount": "100.00",
  "label": "Premium Support",
  "is_active": true,
  "display_order": 5
}
```

**Response (201 Created):**
```json
{
  "id": 10,
  "patient": 1,
  "amount": "100.00",
  "label": "Premium Support",
  "is_active": true,
  "display_order": 5,
  "created_at": "2025-11-22T17:00:00Z"
}
```

---

### 16. Get Donation Amount Details
**Endpoint:** `GET /patients/admin/{patient_id}/donation-amounts/{id}/`  
**Name:** `patients_admin_donation-amounts_read`  
**Description:** Get details of a specific donation amount option

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `patient_id` (required): Patient ID
- `id` (required): Donation amount ID

**Response (200 OK):**
```json
{
  "id": 1,
  "patient": 1,
  "amount": "10.00",
  "label": "Basic Support",
  "is_active": true,
  "display_order": 1,
  "created_at": "2025-11-20T10:30:00Z",
  "updated_at": "2025-11-20T10:30:00Z"
}
```

---

### 17. Update Donation Amount (Full)
**Endpoint:** `PUT /patients/admin/{patient_id}/donation-amounts/{id}/`  
**Name:** `patients_admin_donation-amounts_update`  
**Description:** Completely update a donation amount option

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `patient_id` (required): Patient ID
- `id` (required): Donation amount ID

**Request Body:**
```json
{
  "amount": "15.00",
  "label": "Updated Basic Support",
  "is_active": true,
  "display_order": 1
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "patient": 1,
  "amount": "15.00",
  "label": "Updated Basic Support",
  "is_active": true,
  "display_order": 1,
  "updated_at": "2025-11-22T17:10:00Z"
}
```

---

### 18. Partially Update Donation Amount
**Endpoint:** `PATCH /patients/admin/{patient_id}/donation-amounts/{id}/`  
**Name:** `patients_admin_donation-amounts_partial_update`  
**Description:** Update specific fields of a donation amount option

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `patient_id` (required): Patient ID
- `id` (required): Donation amount ID

**Request Body (any fields):**
```json
{
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "is_active": false,
  "updated_at": "2025-11-22T17:15:00Z"
}
```

---

### 19. Delete Donation Amount
**Endpoint:** `DELETE /patients/admin/{patient_id}/donation-amounts/{id}/`  
**Name:** `patients_admin_donation-amounts_delete`  
**Description:** Remove a donation amount option

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `patient_id` (required): Patient ID
- `id` (required): Donation amount ID

**Response (204 No Content):**
```
(Empty response body)
```

---

### 20. Bulk Create Default Donation Amounts
**Endpoint:** `POST /patients/admin/{patient_id}/donation-amounts/bulk-create/`  
**Name:** `patients_admin_donation-amounts_bulk-create_create`  
**Description:** Automatically create standard donation amount options

**Headers:**
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Path Parameters:**
- `patient_id` (required): Patient ID

**Request Body (optional):**
```json
{
  "amounts": [10, 25, 50, 100, 250, 500],
  "labels": ["$10 - Basic", "$25 - Standard", "$50 - Plus", "$100 - Premium", "$250 - Generous", "$500 - Champion"]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "created_count": 6,
  "donation_amounts": [
    {
      "id": 11,
      "amount": "10.00",
      "label": "$10 - Basic",
      "display_order": 1
    },
    {
      "id": 12,
      "amount": "25.00",
      "label": "$25 - Standard",
      "display_order": 2
    }
  ],
  "message": "Successfully created 6 donation amount options"
}
```

---

## Statistics & Analytics

### 21. Patient Statistics Dashboard
**Endpoint:** `GET /patients/admin/stats/`  
**Name:** `patients_admin_stats`  
**Description:** Get comprehensive patient statistics and analytics

**Headers:**
```http
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `date_from` (optional): Start date for statistics (YYYY-MM-DD)
- `date_to` (optional): End date for statistics (YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "overview": {
    "total_patients": 250,
    "approved_patients": 180,
    "pending_patients": 50,
    "rejected_patients": 20,
    "published_patients": 150
  },
  "funding_stats": {
    "total_funding_goal": "12500000.00",
    "total_current_funding": "5600000.00",
    "average_funding_percentage": 44.8,
    "fully_funded_count": 45,
    "not_funded_count": 30
  },
  "demographics": {
    "by_country": {
      "Kenya": 80,
      "Uganda": 60,
      "Tanzania": 50,
      "Rwanda": 30,
      "Other": 30
    },
    "by_gender": {
      "male": 120,
      "female": 110,
      "other": 20
    },
    "by_age_group": {
      "0-18": 60,
      "19-35": 80,
      "36-55": 70,
      "56+": 40
    }
  },
  "recent_activity": {
    "new_submissions_today": 5,
    "new_submissions_this_week": 28,
    "new_submissions_this_month": 95,
    "approved_this_week": 15,
    "published_this_week": 12
  },
  "medical_conditions": {
    "top_conditions": [
      {"condition": "Heart Surgery", "count": 45},
      {"condition": "Cancer Treatment", "count": 38},
      {"condition": "Kidney Transplant", "count": 25},
      {"condition": "Orthopedic Surgery", "count": 20},
      {"condition": "Other", "count": 122}
    ]
  },
  "funding_trends": {
    "last_7_days": [
      {"date": "2025-11-16", "amount": "12500.00"},
      {"date": "2025-11-17", "amount": "15200.00"},
      {"date": "2025-11-18", "amount": "18900.00"},
      {"date": "2025-11-19", "amount": "14300.00"},
      {"date": "2025-11-20", "amount": "16700.00"},
      {"date": "2025-11-21", "amount": "19200.00"},
      {"date": "2025-11-22", "amount": "21400.00"}
    ]
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": {
    "funding_goal": ["This field must be a positive number"],
    "email": ["Enter a valid email address"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Patient not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "An unexpected error occurred",
  "message": "Please contact support if this persists"
}
```

---

## Authentication

All admin endpoints require authentication using a Bearer token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

To obtain a token, authenticate through the login endpoint:

```http
POST /auth/login/
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin_password"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "is_staff": true
  }
}
```

---

## Rate Limiting

Admin endpoints are rate-limited to:
- **1000 requests per hour** for list/read operations
- **100 requests per hour** for write/update operations
- **50 requests per hour** for bulk operations

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1700658000
```

---

## Best Practices

1. **Use Bulk Operations**: When processing multiple patients, use bulk action endpoints instead of individual requests
2. **Implement Pagination**: Always use pagination for list endpoints to improve performance
3. **Filter Results**: Use query parameters to filter results and reduce data transfer
4. **Cache Statistics**: Cache statistics responses for at least 5 minutes to reduce server load
5. **Handle Errors Gracefully**: Always implement proper error handling for all API calls
6. **Use Partial Updates**: Use PATCH instead of PUT when updating only specific fields
7. **Validate Data**: Always validate input data on the client side before sending requests

---

## Changelog

**v1.0.0** (2025-11-22)
- Initial release of comprehensive admin patient management API
- Added bulk operations support
- Enhanced statistics and analytics endpoints
- Improved filtering and search capabilities

---

## Support

For API support or questions:
- **Email**: api-support@rhci.org
- **Documentation**: https://api.rhci.org/docs
- **Status Page**: https://status.rhci.org

---

*Last Updated: November 22, 2025*
