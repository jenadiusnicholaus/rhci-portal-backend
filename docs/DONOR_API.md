# Donor API Documentation

## Overview
This document describes the API endpoints for donor registration and profile management in the RHCI Portal.

## Authentication
All profile endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Donor Registration

**Endpoint:** `POST /api/auth/register/donor/`

**Description:** Register a new donor account. After registration, a donor profile is automatically created.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "jnichoraus3@gmail.com",
  "password": "securePassword123",
  "full_name": "Jenadius Nicholaus"  // Optional
}
```

**Fields:**
- `email` (required, string): Valid email address
- `password` (required, string): Minimum 8 characters
- `full_name` (optional, string): Full name for profile display

**Response (201 Created):**
```json
{
  "message": "Donor registration successful. Check your email to verify.",
  "user": {
    "id": 1,
    "email": "jnichoraus3@gmail.com",
    "user_type": "DONOR",
    "first_name": "",
    "last_name": "",
    "is_verified": false,
    "is_patient_verified": false,
    "date_joined": "2025-11-18T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Email already registered or validation errors
- `400 Bad Request`: Password too short (< 8 characters)

---

### 2. Login

**Endpoint:** `POST /api/auth/login/`

**Description:** Login to get JWT tokens

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "jnichoraus3@gmail.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "jnichoraus3@gmail.com",
    "user_type": "DONOR",
    "first_name": "",
    "last_name": "",
    "is_verified": true,
    "is_patient_verified": false,
    "date_joined": "2025-11-18T10:30:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid credentials
- `400 Bad Request`: Email not verified
- `400 Bad Request`: Account inactive

---

### 3. Get Donor Profile

**Endpoint:** `GET /api/auth/donor/profile/`

**Description:** Retrieve the authenticated donor's profile information

**Authentication:** Required (JWT Bearer token)

**Response (200 OK):**
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

**Fields:**
- `id` (integer): Profile ID
- `email` (string, read-only): User's email
- `photo` (string/null): URL to profile photo
- `full_name` (string): Full name (max 200 characters)
- `short_bio` (string): Short bio (max 60 characters)
- `country` (string): Country name
- `website` (string): Personal or professional website URL
- `birthday` (date/null): Date of birth in YYYY-MM-DD format
- `age` (integer/null, read-only): Calculated from birthday
- `workplace` (string): Current workplace
- `is_profile_private` (boolean): Privacy setting - if true, profile visible only to donor
- `created_at` (datetime, read-only): Profile creation timestamp
- `updated_at` (datetime, read-only): Last update timestamp

**Error Responses:**
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: User is not a donor

---

### 4. Update Donor Profile

**Endpoint:** `PATCH /api/auth/donor/profile/`

**Description:** Update donor profile information. Use `multipart/form-data` when uploading photo.

**Authentication:** Required (JWT Bearer token)

**Request Body (application/json or multipart/form-data):**
```json
{
  "full_name": "Jenadius Nicholaus",
  "short_bio": "Passionate about helping patients in need",
  "country": "United States",
  "website": "https://example.com",
  "birthday": "1990-05-15",
  "workplace": "Tech Company Inc.",
  "is_profile_private": false
}
```

**For photo upload, use multipart/form-data:**
```
Content-Type: multipart/form-data

photo: [binary file]
full_name: Jenadius Nicholaus
short_bio: Passionate about helping patients in need
country: United States
website: https://example.com
birthday: 1990-05-15
workplace: Tech Company Inc.
is_profile_private: false
```

**Updatable Fields:**
- `photo` (file): Image file (JPEG, PNG) - use multipart/form-data
- `full_name` (string): Full name
- `short_bio` (string): Max 60 characters
- `country` (string): Country name
- `website` (string): Valid URL
- `birthday` (date): YYYY-MM-DD format
- `workplace` (string): Workplace name
- `is_profile_private` (boolean): Privacy setting

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "jnichoraus3@gmail.com",
  "photo": "/media/donor_photos/profile_abc123.jpg",
  "full_name": "Jenadius Nicholaus",
  "short_bio": "Passionate about helping patients in need",
  "country": "United States",
  "website": "https://example.com",
  "birthday": "1990-05-15",
  "age": 35,
  "workplace": "Tech Company Inc.",
  "is_profile_private": false,
  "created_at": "2025-11-18T10:30:00Z",
  "updated_at": "2025-11-18T16:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: User is not a donor
- `400 Bad Request`: Validation errors (e.g., bio too long, invalid URL, invalid date)

---

### 5. Full Profile Update

**Endpoint:** `PUT /api/auth/donor/profile/`

**Description:** Replace entire donor profile (requires all fields)

**Authentication:** Required (JWT Bearer token)

**Note:** Use PATCH (partial update) instead for updating specific fields only.

---

## Example Usage

### cURL Example - Register Donor
```bash
curl -X POST http://localhost:8091/api/auth/register/donor/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jnichoraus3@gmail.com",
    "password": "securePassword123",
    "full_name": "Jenadius Nicholaus"
  }'
```

### cURL Example - Update Profile with Photo
```bash
curl -X PATCH http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "photo=@/path/to/photo.jpg" \
  -F "full_name=Jenadius Nicholaus" \
  -F "short_bio=Passionate about helping patients in need" \
  -F "country=United States" \
  -F "website=https://example.com" \
  -F "birthday=1990-05-15" \
  -F "workplace=Tech Company Inc." \
  -F "is_profile_private=false"
```

### Python Example
```python
import requests

# Register
response = requests.post(
    'http://localhost:8091/api/auth/register/donor/',
    json={
        'email': 'jnichoraus3@gmail.com',
        'password': 'securePassword123',
        'full_name': 'Jenadius Nicholaus'
    }
)

# Login
response = requests.post(
    'http://localhost:8091/api/auth/login/',
    json={
        'email': 'jnichoraus3@gmail.com',
        'password': 'securePassword123'
    }
)
tokens = response.json()['tokens']

# Update profile
headers = {'Authorization': f'Bearer {tokens["access"]}'}
response = requests.patch(
    'http://localhost:8091/api/auth/donor/profile/',
    headers=headers,
    json={
        'full_name': 'Jenadius Nicholaus',
        'short_bio': 'Passionate about helping patients in need',
        'country': 'United States',
        'website': 'https://example.com',
        'birthday': '1990-05-15',
        'workplace': 'Tech Company Inc.',
        'is_profile_private': False
    }
)
profile = response.json()
```

---

## Field Validation Rules

### email
- Must be valid email format
- Must be unique
- Required for registration

### password
- Minimum 8 characters
- Required for registration and login

### full_name
- Maximum 200 characters
- Optional

### short_bio
- Maximum 60 characters
- Optional

### country
- Maximum 100 characters
- Optional

### website
- Must be valid URL format (http:// or https://)
- Optional

### birthday
- Must be valid date in YYYY-MM-DD format
- Cannot be future date
- Optional

### workplace
- Maximum 200 characters
- Optional

### is_profile_private
- Boolean: true or false
- Default: false
- When true, profile is only visible to the donor

### photo
- Supported formats: JPEG, PNG, GIF
- Recommended max size: 5MB
- Files stored in media/donor_photos/
- Optional

---

## Privacy Settings

When `is_profile_private` is set to `true`:
- The donor profile is only visible to the donor themselves
- Other users cannot view the profile information
- Admin users can still access the profile through Django admin

---

## Testing with Swagger

Access the interactive API documentation at:
```
http://localhost:8091/swagger/
```

1. Click on the donor endpoints
2. For authenticated endpoints, click "Authorize" and enter your JWT token
3. Test the endpoints directly from the browser

---

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Validation error or invalid data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
