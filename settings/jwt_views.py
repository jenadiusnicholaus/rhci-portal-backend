from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseTokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
    TokenVerifyView as BaseTokenVerifyView,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class TokenObtainPairView(BaseTokenObtainPairView):
    """
    Obtain JWT access and refresh tokens.
    """
    @swagger_auto_schema(
        operation_summary="Obtain JWT Tokens",
        operation_description="Authenticate with email and password to receive JWT access and refresh tokens.",
        tags=['1. Authentication & Registration'],
        responses={
            200: openapi.Response(
                'Tokens obtained successfully',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                    }
                )
            ),
            401: 'Unauthorized - Invalid credentials'
        }
    )
    def post(self, request, *args, **kwargs):
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
