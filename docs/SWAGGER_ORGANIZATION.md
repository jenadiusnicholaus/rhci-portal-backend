# Swagger API Documentation Organization

## ✅ Implementation Complete

The RHCI Portal API documentation has been comprehensively organized in Swagger UI with proper grouping, tagging, and versioning for optimal developer experience.

## 📊 API Organization Structure

### Tag Groups (9 Categories)

#### 1. **Authentication & Registration**
- `POST /api/auth/register/donor/` - Register as Donor
- `POST /api/auth/register/patient/` - Register as Patient  
- `POST /api/auth/login/` - User Login
- `POST /api/auth/token/refresh/` - Refresh JWT Token

#### 2. **User Profile Management**
- `GET /api/auth/me/` - Get Current User Profile
- `PATCH /api/auth/me/` - Update Current User Profile

#### 3. **Donor Management (Private)** 🔒 Requires Authentication
- `GET /api/auth/donor/profile/` - Get My Donor Profile
- `PATCH /api/auth/donor/profile/` - Update My Donor Profile

#### 4. **Donor Management (Public)** 🌐 Public Access
- `GET /api/auth/donors/` - List Public Donors
- `GET /api/auth/donors/{id}/` - View Public Donor Profile

#### 5. **Patient Management (Private)** 🔒 Requires Authentication
- `GET /api/auth/patient/profile/` - Get My Patient Profile
- `PATCH /api/auth/patient/profile/` - Update My Patient Profile

#### 6. **Patient Management (Public)** 🌐 Public Access (Deprecated)
- `GET /api/auth/patients/` - List Patients (Deprecated)
- `GET /api/auth/patients/{id}/` - View Patient Profile (Deprecated)

#### 7. **Admin - Patient Review & Management** 👨‍💼 Admin Only
- `GET /api/auth/admin/patients/` - List All Patient Submissions
- `GET /api/auth/admin/patients/{id}/` - View Patient Details
- `PATCH /api/auth/admin/patients/{id}/` - Edit Patient Profile
- `POST /api/auth/admin/patients/{id}/approve/` - Approve/Reject Patient
- `POST /api/auth/admin/patients/{id}/publish/` - Publish/Unpublish Patient

#### 8. **Admin - Timeline Management** 👨‍💼 Admin Only
- `GET /api/auth/admin/patients/{patient_id}/timeline/` - List Patient Timeline
- `POST /api/auth/admin/timeline/create/` - Create Timeline Event
- `PATCH /api/auth/admin/timeline/{id}/update/` - Update Timeline Event
- `DELETE /api/auth/admin/timeline/{id}/delete/` - Delete Timeline Event

#### 9. **Public - Patient Profiles** 🌐 Public Access (Recommended)
- `GET /api/auth/public/patients/` - List All Patients
- `GET /api/auth/public/patients/{id}/` - View Patient Profile
- `GET /api/auth/public/patients/featured/` - Featured Patients (Homepage)

## 🎨 Swagger Features Implemented

### Enhanced Documentation
- ✅ **Operation Summaries** - Clear, concise titles for each endpoint
- ✅ **Detailed Descriptions** - Comprehensive explanations of functionality
- ✅ **Request/Response Examples** - Sample data for testing
- ✅ **Parameter Documentation** - Query params, path params, body params
- ✅ **Response Codes** - All possible status codes documented
- ✅ **Deprecation Warnings** - Old endpoints clearly marked

### Authentication & Security
- ✅ **JWT Bearer Token** - Configured in Security Definitions
- ✅ **Authorize Button** - Easy token input in Swagger UI
- ✅ **Permission Indicators** - Public vs authenticated vs admin
- ✅ **Session Management** - Persistent authentication in UI

### Developer Experience
- ✅ **Alphabetical Sorting** - Tags and operations sorted
- ✅ **Deep Linking** - Direct links to specific endpoints
- ✅ **Try It Out** - Interactive testing in browser
- ✅ **Model Examples** - Sample request/response bodies
- ✅ **Version Info** - API version clearly displayed (v1.0.0)

## 📖 API Information

**Title:** RHCI Portal API  
**Version:** v1.0.0  
**Base URL:** `/api/auth/`  

**Contact:**
- Name: RHCI Portal Support
- Email: support@rhciportal.org
- URL: https://rhciportal.org/support

**License:** MIT License

## 🔐 Authentication Guide

### For Developers Using Swagger UI:

1. **Login to get token:**
   - Navigate to **1. Authentication & Registration**
   - Use `POST /api/auth/login/`
   - Enter credentials
   - Execute
   - Copy the `access` token from response

2. **Authorize in Swagger:**
   - Click **Authorize** button (🔒) at top right
   - Enter: `Bearer <your_access_token>`
   - Click **Authorize**
   - Click **Close**

3. **Test protected endpoints:**
   - All authenticated endpoints now work
   - Admin endpoints require admin user type

### For API Integration:

```bash
# 1. Login
curl -X POST http://localhost:8091/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# 2. Use token in subsequent requests
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8091/api/auth/me/
```

## 🎯 Tag Naming Convention

### Prefix Meanings:
- **[ADMIN]** - Admin-only endpoints (requires `user_type='ADMIN'` and `is_staff=True`)
- **[Deprecated]** - Old endpoints, use alternatives
- **No prefix** - Standard endpoints (may require auth)

### Access Levels:
- 🌐 **Public Access** - No authentication required
- 🔒 **Requires Authentication** - JWT token required
- 👨‍💼 **Admin Only** - Admin permissions required

## 📊 Endpoint Count by Category

| Category | Endpoints | Access Level |
|----------|-----------|--------------|
| Authentication & Registration | 4 | Public |
| User Profile Management | 2 | Authenticated |
| Donor Management (Private) | 2 | Authenticated |
| Donor Management (Public) | 2 | Public |
| Patient Management (Private) | 2 | Authenticated |
| Patient Management (Public - Deprecated) | 2 | Public |
| Admin - Patient Review & Management | 5 | Admin Only |
| Admin - Timeline Management | 4 | Admin Only |
| Public - Patient Profiles | 3 | Public |
| **Total** | **26** | **Mixed** |

## 🚀 Access Swagger UI

### Development:
```
http://localhost:8091/swagger/
```

### ReDoc (Alternative):
```
http://localhost:8091/redoc/
```

### JSON Schema:
```
http://localhost:8091/swagger.json
```

### YAML Schema:
```
http://localhost:8091/swagger.yaml
```

## 🎨 Visual Organization Features

### Color Coding (Swagger UI Default):
- **GET** - Blue (Read operations)
- **POST** - Green (Create operations)
- **PATCH/PUT** - Orange (Update operations)
- **DELETE** - Red (Delete operations)

### Grouping:
- Tags are displayed in alphabetical order
- Operations within tags are alphabetically sorted
- Collapsible sections for better navigation
- Search functionality for quick access

### Interactive Features:
- **Try it out** button for live testing
- **Model** tab showing request/response structure
- **Example Value** tab with sample data
- **Parameter** descriptions with types and constraints
- **Response** samples for each status code

## 📝 Configuration Details

### Swagger Settings (settings/settings.py):
```python
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'PERSIST_AUTH': True,
    'TAGS_SORTER': 'alpha',
    'OPERATIONS_SORTER': 'alpha',
    'DOC_EXPANSION': 'list',
    'DEEP_LINKING': True,
    'DEFAULT_MODEL_DEPTH': 3,
}
```

### API Info (settings/urls.py):
- Comprehensive description with markdown formatting
- Contact information
- License details
- Version information
- Logo support (when available)

## 🧪 Testing Workflow

### 1. Public Endpoints (No Auth):
```
GET /api/auth/public/patients/
GET /api/auth/public/patients/featured/
GET /api/auth/donors/
```

### 2. User Endpoints (Auth Required):
```
1. POST /api/auth/login/ (get token)
2. Click Authorize button
3. Test: GET /api/auth/me/
4. Test: GET /api/auth/donor/profile/
```

### 3. Admin Endpoints (Admin Auth Required):
```
1. POST /api/auth/login/ (admin credentials)
2. Click Authorize button
3. Test: GET /api/auth/admin/patients/
4. Test: POST /api/auth/admin/patients/{id}/approve/
```

## 📚 Related Documentation

- **Full API Reference:** `/docs/ADMIN_API_DOCUMENTATION.md`
- **Quick Reference:** `/docs/ADMIN_API_QUICK_REFERENCE.md`
- **Implementation Summary:** `/docs/ADMIN_IMPLEMENTATION_SUMMARY.md`
- **Error Responses:** `/docs/API_ERROR_RESPONSES.md`

## ✨ Key Improvements

### Before:
- Unorganized endpoint list
- No clear categorization
- Minimal descriptions
- No versioning
- Basic authentication documentation

### After:
- **9 logical categories** with clear grouping
- **Numbered tags** for intuitive ordering
- **Comprehensive descriptions** for every endpoint
- **Version 1.0.0** clearly displayed
- **Admin tag prefixes** for easy identification
- **Deprecation warnings** for old endpoints
- **Query parameter documentation**
- **Response code documentation**
- **Interactive examples**

## 🎓 Developer Benefits

1. **Easy Navigation** - Numbered categories guide developers through API
2. **Clear Access Levels** - Know which endpoints require auth
3. **Admin Identification** - [ADMIN] prefix clearly marks admin endpoints
4. **Deprecation Awareness** - Old endpoints marked to avoid future breaking changes
5. **Interactive Testing** - Test all endpoints directly in browser
6. **Complete Documentation** - All parameters, responses, and errors documented
7. **Versioning** - Track API version for compatibility

## 📈 Next Steps

### Recommended Enhancements:
1. Add request/response examples for complex operations
2. Include error response schemas
3. Add rate limiting documentation
4. Document pagination format
5. Add webhooks documentation (when implemented)
6. Include changelog in API info
7. Add code samples in multiple languages

### Future API Versions:
- Plan for v2.0.0 with breaking changes
- Maintain v1.0.0 with deprecation notices
- Use URL versioning: `/api/v1/auth/` vs `/api/v2/auth/`

---

**Last Updated:** November 18, 2025  
**API Version:** v1.0.0  
**Swagger UI:** http://localhost:8091/swagger/
