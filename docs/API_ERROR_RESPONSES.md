# API Error Responses Documentation

## Overview
All API errors return a consistent JSON structure with descriptive messages to help developers and users understand what went wrong.

## Error Response Format

All error responses follow this structure:

```json
{
  "error": true,
  "error_code": "specific_error_code",
  "message": "Human-readable error message",
  "details": {
    "field_name": ["Specific field error message"]
  }
}
```

### Fields:
- **error** (boolean): Always `true` for error responses
- **error_code** (string): Machine-readable error code for programmatic handling
- **message** (string): Human-readable description of the error
- **details** (object, optional): Additional field-specific validation errors

## HTTP Status Codes

- **400 Bad Request**: Invalid input data or validation errors
- **401 Unauthorized**: Authentication failed or token invalid
- **403 Forbidden**: Authenticated but not authorized to access resource
- **404 Not Found**: Requested resource doesn't exist
- **500 Internal Server Error**: Server-side error

---

## Authentication & Authorization Errors

### Email Already Exists
**Status Code:** `400 Bad Request`

**Occurs when:** Registering with an email that's already in use

**Response:**
```json
{
  "error": true,
  "error_code": "email_already_exists",
  "message": "An account with this email address already exists. Please use a different email or try logging in.",
  "details": null
}
```

**How to fix:** Use a different email address or try logging in if you already have an account.

---

### Invalid Credentials
**Status Code:** `401 Unauthorized`

**Occurs when:** Login with wrong email or password

**Response:**
```json
{
  "error": true,
  "error_code": "invalid_credentials",
  "message": "Invalid email or password. Please check your credentials and try again.",
  "details": null
}
```

**How to fix:** Double-check your email and password. Ensure caps lock is not on.

---

### Email Not Verified
**Status Code:** `403 Forbidden`

**Occurs when:** Attempting to login before verifying email

**Response:**
```json
{
  "error": true,
  "error_code": "email_not_verified",
  "message": "Your email address has not been verified. Please check your email for a verification link or contact support.",
  "details": null
}
```

**How to fix:** Check your email inbox (and spam folder) for a verification link. Resend verification email if needed.

**Development Note:** During development/testing, activate users manually:
```python
user.is_verified = True
user.save()
```

---

### Account Inactive
**Status Code:** `403 Forbidden`

**Occurs when:** Account has been deactivated by admin

**Response:**
```json
{
  "error": true,
  "error_code": "account_inactive",
  "message": "Your account has been deactivated. Please contact support for assistance.",
  "details": null
}
```

**How to fix:** Contact support to reactivate your account.

---

### Insufficient Permissions
**Status Code:** `403 Forbidden`

**Occurs when:** Trying to access a resource for a different user type (e.g., donor accessing patient endpoint)

**Response:**
```json
{
  "error": true,
  "error_code": "insufficient_permissions",
  "message": "Only donors can access this endpoint. Please ensure you registered as a donor.",
  "details": null
}
```

**How to fix:** Ensure you're accessing the correct endpoint for your account type (donor vs patient).

---

## Validation Errors

### Password Too Short
**Status Code:** `400 Bad Request`

**Occurs when:** Password is less than 8 characters

**Response:**
```json
{
  "error": true,
  "error_code": "password_too_short",
  "message": "Password is too short. Please use at least 8 characters.",
  "details": null
}
```

**How to fix:** Use a password with at least 8 characters.

---

### Invalid Date
**Status Code:** `400 Bad Request`

**Occurs when:** Date is in the future or invalid format

**Response:**
```json
{
  "error": true,
  "error_code": "invalid_date",
  "message": "Invalid date provided. Please ensure the date is in the correct format (YYYY-MM-DD) and is not in the future.",
  "details": null
}
```

**How to fix:** Use correct date format (YYYY-MM-DD) and ensure date is not in the future.

---

### File Size Too Large
**Status Code:** `400 Bad Request`

**Occurs when:** Uploading a file larger than 5MB

**Response:**
```json
{
  "error": true,
  "error_code": "file_size_too_large",
  "message": "File size too large. Please upload an image smaller than 5MB.",
  "details": null
}
```

**How to fix:** Compress or resize your image to be under 5MB.

---

### Invalid File Type
**Status Code:** `400 Bad Request`

**Occurs when:** Uploading a file that's not an image

**Response:**
```json
{
  "error": true,
  "error_code": "invalid_file_type",
  "message": "Invalid file type. Please upload a valid image file (JPEG, PNG, or GIF).",
  "details": null
}
```

**How to fix:** Only upload JPEG, PNG, or GIF image files.

---

### Missing Required Field
**Status Code:** `400 Bad Request`

**Occurs when:** Required field is not provided

**Response:**
```json
{
  "error": true,
  "error_code": "missing_required_field",
  "message": "The field \"email\" is required but was not provided. Please include this field in your request.",
  "details": null
}
```

**How to fix:** Include all required fields in your request.

---

## Profile Errors

### Donor Profile Not Found
**Status Code:** `404 Not Found`

**Occurs when:** User is not a donor or profile doesn't exist

**Response:**
```json
{
  "error": true,
  "error_code": "donor_profile_not_found",
  "message": "Donor profile not found. Only users registered as donors can access this endpoint.",
  "details": null
}
```

**How to fix:** Register as a donor or access the correct endpoint for your account type.

---

### Patient Profile Not Found
**Status Code:** `404 Not Found`

**Occurs when:** User is not a patient or profile doesn't exist

**Response:**
```json
{
  "error": true,
  "error_code": "patient_profile_not_found",
  "message": "Patient profile not found. Only users registered as patients can access this endpoint.",
  "details": null
}
```

**How to fix:** Register as a patient or access the correct endpoint for your account type.

---

## Field Validation Errors

When multiple fields have validation errors, the response includes details:

**Example:**
```json
{
  "error": true,
  "error_code": "error",
  "message": "Validation error occurred",
  "details": {
    "email": ["Enter a valid email address."],
    "password": ["This field is required."],
    "short_bio": ["Ensure this field has no more than 60 characters."]
  }
}
```

---

## Examples by Endpoint

### Registration Errors

#### Donor Registration - Email Already Exists
```bash
curl -X POST http://localhost:8091/api/auth/register/donor/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "existing@example.com",
    "password": "password123"
  }'
```

**Response (400):**
```json
{
  "error": true,
  "error_code": "email_already_exists",
  "message": "An account with this email address already exists. Please use a different email or try logging in.",
  "details": null
}
```

#### Patient Registration - Password Too Short
```bash
curl -X POST http://localhost:8091/api/auth/register/patient/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "short"
  }'
```

**Response (400):**
```json
{
  "error": true,
  "error_code": "password_too_short",
  "message": "Password is too short. Please use at least 8 characters.",
  "details": null
}
```

---

### Login Errors

#### Invalid Credentials
```bash
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "wrongpassword"
  }'
```

**Response (401):**
```json
{
  "error": true,
  "error_code": "invalid_credentials",
  "message": "Invalid email or password. Please check your credentials and try again.",
  "details": null
}
```

#### Email Not Verified
```bash
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "unverified@example.com",
    "password": "password123"
  }'
```

**Response (403):**
```json
{
  "error": true,
  "error_code": "email_not_verified",
  "message": "Your email address has not been verified. Please check your email for a verification link or contact support.",
  "details": null
}
```

#### Account Inactive
```bash
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "inactive@example.com",
    "password": "password123"
  }'
```

**Response (403):**
```json
{
  "error": true,
  "error_code": "account_inactive",
  "message": "Your account has been deactivated. Please contact support for assistance.",
  "details": null
}
```

---

### Profile Update Errors

#### File Size Too Large
```bash
curl -X PATCH http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "photo=@large_image.jpg"
```

**Response (400):**
```json
{
  "error": true,
  "error_code": "file_size_too_large",
  "message": "File size too large. Please upload an image smaller than 5MB.",
  "details": null
}
```

#### Invalid Date (Birthday in Future)
```bash
curl -X PATCH http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "birthday": "2030-01-01"
  }'
```

**Response (400):**
```json
{
  "error": true,
  "error_code": "invalid_date",
  "message": "Invalid date provided. Please ensure the date is in the correct format (YYYY-MM-DD) and is not in the future.",
  "details": null
}
```

#### Wrong Account Type
```bash
# Patient trying to access donor endpoint
curl -X GET http://localhost:8091/api/auth/donor/profile/ \
  -H "Authorization: Bearer PATIENT_TOKEN"
```

**Response (403):**
```json
{
  "error": true,
  "error_code": "insufficient_permissions",
  "message": "Only donors can access this endpoint. Please ensure you registered as a donor.",
  "details": null
}
```

---

## Error Handling in Client Code

### JavaScript/TypeScript Example
```javascript
async function loginUser(email, password) {
  try {
    const response = await fetch('http://localhost:8091/api/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      
      // Handle specific error codes
      switch (errorData.error_code) {
        case 'invalid_credentials':
          alert('Wrong email or password');
          break;
        case 'email_not_verified':
          alert('Please verify your email first');
          showResendVerificationButton();
          break;
        case 'account_inactive':
          alert('Your account is inactive. Contact support.');
          break;
        default:
          alert(errorData.message);
      }
      
      return;
    }

    const data = await response.json();
    // Handle successful login
    localStorage.setItem('access_token', data.tokens.access);
  } catch (error) {
    console.error('Network error:', error);
    alert('Connection error. Please try again.');
  }
}
```

### Python Example
```python
import requests

def register_donor(email, password, full_name):
    try:
        response = requests.post(
            'http://localhost:8091/api/auth/register/donor/',
            json={
                'email': email,
                'password': password,
                'full_name': full_name
            }
        )
        
        if response.status_code != 201:
            error_data = response.json()
            error_code = error_data.get('error_code')
            message = error_data.get('message')
            
            if error_code == 'email_already_exists':
                print(f"Error: {message}")
                print("Try logging in instead.")
            elif error_code == 'password_too_short':
                print(f"Error: {message}")
            else:
                print(f"Error: {message}")
            
            return None
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
```

---

## Testing Error Responses

### Test Invalid Credentials
```bash
# Should return 401 with invalid_credentials error
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "wrongpass"}'
```

### Test Unverified Account
```bash
# Create unverified user first
# Should return 403 with email_not_verified error
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test_unverified@example.com", "password": "password123"}'
```

### Test Inactive Account
```bash
# Should return 403 with account_inactive error
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test_inactive@example.com", "password": "password123"}'
```

---

## Best Practices

1. **Always check the `error_code`** field for programmatic error handling
2. **Display the `message`** field to users for human-readable feedback
3. **Use `details`** for field-specific validation errors
4. **Log errors** on the client side for debugging
5. **Provide helpful UI** based on error codes (e.g., show "Resend Verification" button for email_not_verified)
6. **Test error scenarios** during development

---

## Summary of Error Codes

| Error Code | Status | Description |
|------------|--------|-------------|
| `email_already_exists` | 400 | Email is already registered |
| `invalid_credentials` | 401 | Wrong email or password |
| `email_not_verified` | 403 | Email not verified yet |
| `account_inactive` | 403 | Account deactivated by admin |
| `insufficient_permissions` | 403 | Wrong account type for endpoint |
| `password_too_short` | 400 | Password less than 8 characters |
| `invalid_date` | 400 | Invalid or future date |
| `file_size_too_large` | 400 | File exceeds 5MB limit |
| `invalid_file_type` | 400 | File is not JPEG/PNG/GIF |
| `missing_required_field` | 400 | Required field not provided |
| `donor_profile_not_found` | 404 | Donor profile doesn't exist |
| `patient_profile_not_found` | 404 | Patient profile doesn't exist |

---

**Last Updated:** November 18, 2025
