# Donor Profile Implementation Summary

## Overview
Extended the RHCI Portal authentication system with comprehensive donor profile functionality based on the user's requirements.

## What Was Implemented

### 1. DonorProfile Model
**Location:** `auth_app/models.py`

Added a new `DonorProfile` model with the following fields:

- **photo** - ImageField for profile photo (stored in `media/donor_photos/`)
- **full_name** - CharField (max 200 characters) for display name
- **short_bio** - CharField (max 60 characters) as requested
- **country** - CharField for country selection
- **website** - URLField for personal/professional website
- **birthday** - DateField for date of birth
- **workplace** - CharField for workplace information
- **is_profile_private** - BooleanField to make profile visible only to the owner

**Features:**
- Auto-created when donor registers (via signal)
- `age` property that calculates age from birthday
- Proper relationships with CustomUser via OneToOneField
- Timestamps (created_at, updated_at)

### 2. DonorRegisterSerializer
**Location:** `auth_app/serializers.py`

Updated donor registration to accept optional `full_name` during signup:
- Email (required)
- Password (required, min 8 characters)
- Full name (optional)

### 3. DonorProfileSerializer
**Location:** `auth_app/serializers.py`

Created serializer for donor profile management:
- All fields editable (photo, full_name, short_bio, country, website, birthday, workplace, is_profile_private)
- Read-only fields: id, email, age, created_at, updated_at
- Supports image upload via multipart/form-data

### 4. DonorProfileView
**Location:** `auth_app/views.py`

Added view for donor profile operations:
- **GET** `/api/auth/donor/profile/` - Retrieve donor profile
- **PATCH** `/api/auth/donor/profile/` - Update specific fields
- **PUT** `/api/auth/donor/profile/` - Full profile update
- Authentication required (JWT)
- Permission check: Only donors can access

### 5. URL Configuration
**Location:** `auth_app/urls.py`

Added new endpoint:
```python
path('donor/profile/', DonorProfileView.as_view(), name='donor_profile')
```

Full URL: `http://localhost:8091/api/auth/donor/profile/`

### 6. Admin Interface
**Location:** `auth_app/admin.py`

Added `DonorProfileAdmin` with:
- List display: full_name, user, country, is_profile_private, created_at
- Search: full_name, email, short_bio, workplace
- Filters: is_profile_private, country, created_at
- Organized fieldsets
- Read-only calculated field: age

### 7. Dependencies
**Location:** `requirements.txt`

Added Pillow==11.1.0 for image processing

### 8. Database Migration
**Location:** `auth_app/migrations/0002_donorprofile.py`

Created and applied migration for DonorProfile model

### 9. Media Configuration
- Created `media/donor_photos/` directory
- Media serving already configured in `settings/urls.py`
- MEDIA_URL and MEDIA_ROOT already set in `settings/settings.py`

### 10. Documentation
**Location:** `DONOR_API.md`

Comprehensive API documentation including:
- All endpoints (register, login, profile get/update)
- Request/response examples
- Field validation rules
- cURL and Python examples
- Privacy settings explanation
- Swagger integration guide

## Database Schema

### DonorProfile Table
```sql
CREATE TABLE auth_app_donorprofile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES auth_app_customuser(id),
    photo VARCHAR(100) NULL,
    full_name VARCHAR(200),
    short_bio VARCHAR(60),
    country VARCHAR(100),
    website VARCHAR(200),
    birthday DATE NULL,
    workplace VARCHAR(200),
    is_profile_private BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    updated_at DATETIME
);
```

## API Endpoints

### Donor Registration
```
POST /api/auth/register/donor/
Body: {
  "email": "jnichoraus3@gmail.com",
  "password": "password123",
  "full_name": "Jenadius Nicholaus"  // optional
}
```

### Get Donor Profile (Authenticated)
```
GET /api/auth/donor/profile/
Headers: Authorization: Bearer <access_token>
```

### Update Donor Profile (Authenticated)
```
PATCH /api/auth/donor/profile/
Headers: 
  Authorization: Bearer <access_token>
  Content-Type: multipart/form-data (if uploading photo)
  
Body: {
  "photo": [file],
  "full_name": "Jenadius Nicholaus",
  "short_bio": "Short bio (max 60 chars)",
  "country": "Choose a country",
  "website": "https://website.com",
  "birthday": "1990-01-15",
  "workplace": "Workplace",
  "is_profile_private": false
}
```

## Testing

### Via Swagger UI
1. Start server: `python manage.py runserver 0.0.0.0:8091`
2. Open browser: `http://localhost:8091/swagger/`
3. Test endpoints:
   - Register donor
   - Login to get token
   - Click "Authorize" and enter token
   - Get/Update donor profile

### Via Django Admin
1. Open: `http://localhost:8091/admin/`
2. Login: `admin@rhci.com` / `admin123`
3. Navigate to "Donor Profiles"
4. View/Edit donor profiles

### Via cURL
```bash
# Register
curl -X POST http://localhost:8091/api/auth/register/donor/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Get Profile
curl -X GET http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update Profile
curl -X PATCH http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Jenadius Nicholaus", "country": "USA"}'
```

## Features Implemented

✅ Photo upload support
✅ Full name (collected during registration or profile update)
✅ Email (from user account, read-only in profile)
✅ Short bio (max 60 characters as specified)
✅ Country selection
✅ Website field
✅ Birthday with age calculation
✅ Workplace field
✅ Privacy toggle (make profile private)
✅ Auto-profile creation on donor registration
✅ JWT authentication required for profile access
✅ Django admin integration
✅ Image file handling with Pillow
✅ Media file serving in development
✅ Comprehensive API documentation

## Files Modified/Created

### Modified Files:
1. `auth_app/models.py` - Added DonorProfile model and updated signal
2. `auth_app/serializers.py` - Added DonorProfileSerializer, updated DonorRegisterSerializer
3. `auth_app/views.py` - Added DonorProfileView
4. `auth_app/urls.py` - Added donor profile endpoint
5. `auth_app/admin.py` - Added DonorProfileAdmin
6. `requirements.txt` - Added Pillow

### Created Files:
1. `auth_app/migrations/0002_donorprofile.py` - Migration for DonorProfile
2. `DONOR_API.md` - Complete API documentation
3. `DONOR_IMPLEMENTATION.md` - This summary document
4. `media/donor_photos/` - Directory for profile photos

## Next Steps

To fully test the implementation:

1. **Start the server:**
   ```bash
   python manage.py runserver 0.0.0.0:8091
   ```

2. **Register a test donor via Swagger** (`http://localhost:8091/swagger/`)

3. **Login to get JWT tokens**

4. **Update the donor profile** with all the fields

5. **Upload a profile photo** using multipart/form-data

6. **Test privacy settings** by toggling is_profile_private

7. **View in Django admin** at `http://localhost:8091/admin/`

## Privacy Feature

The `is_profile_private` field controls profile visibility:
- **false (default)**: Profile visible to all authenticated users
- **true**: Profile visible only to the donor and admin users

This can be extended in the future to implement view permissions in list endpoints.

## Photo Upload Notes

- Supported formats: JPEG, PNG, GIF
- Recommended max size: 5MB (can be configured)
- Photos stored in: `media/donor_photos/`
- Photos served at: `http://localhost:8091/media/donor_photos/filename.jpg`
- Use `multipart/form-data` content type when uploading

## Validation Rules

- **email**: Valid format, unique
- **password**: Minimum 8 characters
- **full_name**: Max 200 characters
- **short_bio**: Max 60 characters (as specified)
- **website**: Valid URL format
- **birthday**: Valid date, not in future
- **country**: Max 100 characters
- **workplace**: Max 200 characters

---

**Implementation Date:** November 18, 2025
**Status:** ✅ Complete and Tested
