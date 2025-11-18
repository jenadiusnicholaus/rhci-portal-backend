# RHCI Portal - Documentation

Welcome to the RHCI Portal documentation. This folder contains comprehensive documentation for all API endpoints and features.

## 📚 Documentation Index

### Admin Management API
- **[Admin API Documentation](./ADMIN_API_DOCUMENTATION.md)** - Complete API reference for admin endpoints with examples
- **[Admin Implementation Summary](./ADMIN_IMPLEMENTATION_SUMMARY.md)** - Detailed implementation overview and features
- **[Admin API Quick Reference](./ADMIN_API_QUICK_REFERENCE.md)** - Quick command reference card

### Donor Management
- **[Donor API Documentation](./DONOR_API.md)** - Donor profile and registration endpoints
- **[Donor Implementation](./DONOR_IMPLEMENTATION.md)** - Donor feature implementation details

### Security & Access Control
- **[API Error Responses](./API_ERROR_RESPONSES.md)** - Standard error codes and responses
- **[Public Profile Access](./PUBLIC_PROFILE_ACCESS.md)** - Public vs private profile access control

## 🚀 Quick Start

### For Administrators
1. Review [Admin API Documentation](./ADMIN_API_DOCUMENTATION.md)
2. Use [Admin API Quick Reference](./ADMIN_API_QUICK_REFERENCE.md) for common tasks
3. Run the test script: `python auth_app/test_admin_api.py`

### For Developers
1. Check [API Error Responses](./API_ERROR_RESPONSES.md) for error handling
2. Review implementation summaries for architecture details
3. Test endpoints via Swagger UI: `http://localhost:8091/swagger/`

### For Integration
1. Public endpoints require no authentication
2. Admin endpoints require JWT token with `user_type='ADMIN'`
3. All endpoints follow REST conventions

## 📖 Main Features

### Admin Features
- Patient review and approval
- Medical details management
- Timeline event management
- Publishing and featuring patients
- Filtering and search

### Public Features
- Browse published patients
- View patient stories and timelines
- Filter by country, medical partner, funding status
- Featured patients for homepage

### Automation
- Auto-generated timeline events
- Funding milestone tracking
- Status change tracking
- Treatment scheduling events

## 🔗 Related Resources

- **Swagger UI**: http://localhost:8091/swagger/
- **Django Admin**: http://localhost:8091/admin/
- **Test Script**: `auth_app/test_admin_api.py`

## 📝 Last Updated

November 18, 2025
