"""
URL configuration for settings project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Information for Swagger
api_info = openapi.Info(
    title="RHCI Portal API",
    default_version='v1.0.0',
    description="""
# RHCI Portal - Comprehensive Medical Crowdfunding Platform API

## Overview
The RHCI Portal API provides comprehensive endpoints for managing medical crowdfunding campaigns, 
patient profiles, donor management, and administrative workflows.

## Authentication
Most endpoints require JWT authentication. Use the `/api/auth/login/` endpoint to obtain tokens.

### How to Authenticate:
1. Login via `/api/auth/login/` to get access token
2. Click the **Authorize** button (🔒) at the top right
3. Enter: `Bearer <your_access_token>`
4. Click **Authorize**

## API Features
- **Patient Management** - Submit, review, approve, and publish patient profiles
- **Donor Management** - Public and private donor profiles
- **Timeline Tracking** - Automated and manual event tracking
- **Funding Management** - Track donations and funding milestones
- **Admin Workflows** - Complete administrative control

## Versioning
Current Version: **v1.0.0**  
Base URL: `/api/auth/`

## Support
- Documentation: `/docs/`
- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`
    """,
    terms_of_service="https://rhciportal.org/terms/",
    contact=openapi.Contact(
        name="RHCI Portal Support",
        email="support@rhciportal.org",
        url="https://rhciportal.org/support"
    ),
    license=openapi.License(name="MIT License"),
    x_logo={
        "url": "https://rhciportal.org/logo.png",
        "altText": "RHCI Portal"
    }
)

schema_view = get_schema_view(
    api_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Swagger documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Auth app endpoints
    path('api/auth/', include('auth_app.urls')),
    
    # DRF browsable API login/logout
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
