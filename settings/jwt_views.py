from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseTokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
    TokenVerifyView as BaseTokenVerifyView,
)
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class TokenObtainPairView(BaseTokenObtainPairView):
    """
    Obtain JWT access and refresh tokens with custom validation.
    """
    @swagger_auto_schema(
        operation_summary="Login / Obtain JWT Tokens",
        operation_description="Authenticate with email and password to receive JWT access and refresh tokens. Checks account status (active, verified).",
        tags=['1. Authentication & Registration'],
        responses={
            200: openapi.Response(
                'Login successful',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                    }
                )
            ),
            401: 'Unauthorized - Invalid credentials, account inactive, or email not verified'
        }
    )
    def post(self, request, *args, **kwargs):
        # Get credentials
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'detail': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response(
                {'detail': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if account is active
        if not user.is_active:
            return Response(
                {'detail': 'Account is inactive. Please contact support.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if email is verified
        if not user.is_verified:
            return Response(
                {'detail': 'Email not verified. Please check your inbox for verification email.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If all checks pass, generate tokens
        return super().post(request, *args, **kwargs)


class TokenRefreshView(BaseTokenRefreshView):
    """
    Refresh JWT access token.
    """
    @swagger_auto_schema(
        operation_summary="Refresh Access Token",
        operation_description="Obtain a new access token using a valid refresh token.",
        tags=['1. Authentication & Registration'],
        responses={
            200: openapi.Response(
                'Token refreshed successfully',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='New JWT access token'),
                    }
                )
            ),
            401: 'Unauthorized - Invalid or expired refresh token'
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenVerifyView(BaseTokenVerifyView):
    """
    Verify JWT token validity.
    """
    @swagger_auto_schema(
        operation_summary="Verify Token",
        operation_description="Verify if a given token is valid and not expired.",
        tags=['1. Authentication & Registration'],
        responses={
            200: openapi.Response('Token is valid', openapi.Schema(type=openapi.TYPE_OBJECT)),
            401: 'Unauthorized - Invalid or expired token'
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
