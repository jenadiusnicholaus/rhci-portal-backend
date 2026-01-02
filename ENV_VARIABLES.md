# Environment Variables Reference

This document provides detailed information about all environment variables used in the RHCI Portal project.

## Core Django Settings

### SECRET_KEY
- **Type**: String
- **Required**: Yes
- **Default**: (insecure key for development only)
- **Description**: Cryptographic signing key for Django. Must be kept secret in production.
- **Production**: Generate a new secure key using:
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```

### DEBUG
- **Type**: Boolean
- **Required**: No
- **Default**: True
- **Description**: Enable/disable debug mode. MUST be False in production.
- **Values**: True, False

### ALLOWED_HOSTS
- **Type**: Comma-separated string
- **Required**: Yes (when DEBUG=False)
- **Default**: localhost,127.0.0.1
- **Description**: List of host/domain names that Django can serve.
- **Example**: localhost,127.0.0.1,example.com,www.example.com

## Database Configuration

### DB_ENGINE
- **Type**: String
- **Required**: No
- **Default**: django.db.backends.sqlite3
- **Description**: Database backend to use.
- **Options**:
  - `django.db.backends.sqlite3` (SQLite)
  - `django.db.backends.postgresql` (PostgreSQL)
  - `django.db.backends.mysql` (MySQL)
  - `django.db.backends.oracle` (Oracle)

### DB_NAME
- **Type**: String
- **Required**: Yes
- **Default**: db.sqlite3 (for SQLite)
- **Description**: Database name or path (for SQLite).

### DB_USER
- **Type**: String
- **Required**: Yes (for PostgreSQL/MySQL)
- **Default**: None
- **Description**: Database username.

### DB_PASSWORD
- **Type**: String
- **Required**: Yes (for PostgreSQL/MySQL)
- **Default**: None
- **Description**: Database password.

### DB_HOST
- **Type**: String
- **Required**: No
- **Default**: localhost
- **Description**: Database server host.

### DB_PORT
- **Type**: String/Integer
- **Required**: No
- **Default**: 5432 (PostgreSQL), 3306 (MySQL)
- **Description**: Database server port.

## Email Configuration

### EMAIL_BACKEND
- **Type**: String
- **Required**: No
- **Default**: django.core.mail.backends.console.EmailBackend
- **Description**: Email backend to use for sending emails.
- **Options**:
  - `django.core.mail.backends.smtp.EmailBackend` (SMTP)
  - `django.core.mail.backends.console.EmailBackend` (Console - development)
  - `django.core.mail.backends.filebased.EmailBackend` (File-based)

### EMAIL_HOST
- **Type**: String
- **Required**: Yes (for SMTP)
- **Default**: smtp.gmail.com
- **Description**: SMTP server hostname.
- **Common values**:
  - Gmail: smtp.gmail.com
  - Outlook: smtp-mail.outlook.com
  - SendGrid: smtp.sendgrid.net

### EMAIL_PORT
- **Type**: Integer
- **Required**: No
- **Default**: 587
- **Description**: SMTP server port.
- **Common values**: 587 (TLS), 465 (SSL), 25 (unencrypted)

### EMAIL_USE_TLS
- **Type**: Boolean
- **Required**: No
- **Default**: True
- **Description**: Use TLS encryption for SMTP connection.
- **Values**: True, False

### EMAIL_HOST_USER
- **Type**: String
- **Required**: Yes (for SMTP)
- **Default**: None
- **Description**: SMTP server username/email address.

### EMAIL_HOST_PASSWORD
- **Type**: String
- **Required**: Yes (for SMTP)
- **Default**: None
- **Description**: SMTP server password or app-specific password.
- **Note**: For Gmail, use an App Password if 2FA is enabled.

## Security Settings

### CSRF_COOKIE_SECURE
- **Type**: Boolean
- **Required**: No
- **Default**: False
- **Description**: Whether to use secure cookies for CSRF protection.
- **Production**: Should be True

### SESSION_COOKIE_SECURE
- **Type**: Boolean
- **Required**: No
- **Default**: False
- **Description**: Whether to use secure cookies for sessions.
- **Production**: Should be True

### SECURE_SSL_REDIRECT
- **Type**: Boolean
- **Required**: No
- **Default**: False
- **Description**: Redirect all HTTP requests to HTTPS.
- **Production**: Should be True

### SECURE_HSTS_SECONDS
- **Type**: Integer
- **Required**: No
- **Default**: 0
- **Description**: HTTP Strict Transport Security header value.
- **Production**: Recommended value: 31536000 (1 year)

## Static and Media Files

### STATIC_URL
- **Type**: String
- **Required**: No
- **Default**: /static/
- **Description**: URL prefix for static files.

### STATIC_ROOT
- **Type**: String
- **Required**: No
- **Default**: staticfiles
- **Description**: Directory where static files are collected.

### MEDIA_URL
- **Type**: String
- **Required**: No
- **Default**: /media/
- **Description**: URL prefix for uploaded media files.

### MEDIA_ROOT
- **Type**: String
- **Required**: No
- **Default**: media
- **Description**: Directory where uploaded files are stored.

## Localization

### TIME_ZONE
- **Type**: String
- **Required**: No
- **Default**: UTC
- **Description**: Time zone for the application.
- **Examples**: 
  - UTC
  - America/New_York
  - Europe/London
  - Asia/Tokyo
  - Africa/Nairobi

### LANGUAGE_CODE
- **Type**: String
- **Required**: No
- **Default**: en-us
- **Description**: Language code for the application.
- **Examples**: en-us, es, fr, de, ja, sw

## Development vs Production Settings

### Development (.env)
```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
```

### Production (.env)
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=<generate-new-secure-key>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rhci_portal_production
DB_USER=prod_user
DB_PASSWORD=<strong-password>
DB_HOST=db.yourdomain.com
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

## Best Practices

1. **Never commit .env file** - It contains sensitive information
2. **Use different values for development and production**
3. **Generate new SECRET_KEY for production**
4. **Use environment-specific .env files** (.env.dev, .env.prod)
5. **Keep .env.example updated** with all required variables
6. **Use strong passwords** for database and email
7. **Enable security settings in production** (SSL, secure cookies, etc.)
8. **Use database-backed cache in production** instead of local memory
9. **Configure proper logging** for production environments
10. **Regularly rotate secrets** (SECRET_KEY, passwords, API keys)

## Troubleshooting

### Common Issues

1. **"SECRET_KEY not found"**
   - Ensure .env file exists in project root
   - Check that SECRET_KEY is defined in .env

2. **"Database connection failed"**
   - Verify database credentials in .env
   - Ensure database server is running
   - Check network connectivity to database host

3. **"Email not sending"**
   - Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
   - Check if using App Password for Gmail
   - Verify SMTP port and TLS settings

4. **"Static files not loading"**
   - Run `python manage.py collectstatic`
   - Check STATIC_URL and STATIC_ROOT settings
   - Verify web server configuration for static files

## AzamPay Bill Pay API Configuration

### AZAMPAY_BILLPAY_JWT_SECRET
- **Type**: String
- **Required**: Yes (for Bill Pay API)
- **Default**: your-jwt-secret-change-in-production
- **Description**: JWT secret key for verifying tokens from AzamPay Bill Pay API
- **Security**: MUST be changed in production. Obtain from AzamPay when setting up Bill Pay API.

### AZAMPAY_BILLPAY_SECRET
- **Type**: String
- **Required**: Yes (for Bill Pay API)
- **Default**: your-hmac-secret-change-in-production
- **Description**: HMAC secret key for verifying signatures from AzamPay Bill Pay API
- **Security**: MUST be changed in production. Obtain from AzamPay when setting up Bill Pay API.

**Example .env**:
```env
AZAMPAY_BILLPAY_JWT_SECRET=your-actual-jwt-secret-from-azampay
AZAMPAY_BILLPAY_SECRET=your-actual-hmac-secret-from-azampay
```
