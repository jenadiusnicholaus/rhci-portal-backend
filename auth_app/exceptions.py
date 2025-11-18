"""
Custom exceptions for auth_app to provide clear, descriptive error messages
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class EmailAlreadyExistsException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An account with this email address already exists. Please use a different email or try logging in.'
    default_code = 'email_already_exists'


class InvalidCredentialsException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid email or password. Please check your credentials and try again.'
    default_code = 'invalid_credentials'


class EmailNotVerifiedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Your email address has not been verified. Please check your email for a verification link or contact support.'
    default_code = 'email_not_verified'


class AccountInactiveException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Your account has been deactivated. Please contact support for assistance.'
    default_code = 'account_inactive'


class InsufficientPermissionsException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to access this resource. Please ensure you are logged in with the correct account type.'
    default_code = 'insufficient_permissions'


class PatientProfileNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Patient profile not found. Only users registered as patients can access this endpoint.'
    default_code = 'patient_profile_not_found'


class DonorProfileNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Donor profile not found. Only users registered as donors can access this endpoint.'
    default_code = 'donor_profile_not_found'


class InvalidFileTypeException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid file type. Please upload a valid image file (JPEG, PNG, or GIF).'
    default_code = 'invalid_file_type'


class FileSizeTooLargeException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'File size too large. Please upload an image smaller than 5MB.'
    default_code = 'file_size_too_large'


class PasswordTooShortException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Password is too short. Please use at least 8 characters.'
    default_code = 'password_too_short'


class InvalidDateException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid date provided. Please ensure the date is in the correct format (YYYY-MM-DD) and is not in the future.'
    default_code = 'invalid_date'


class MissingRequiredFieldException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Required field is missing. Please provide all required information.'
    default_code = 'missing_required_field'
    
    def __init__(self, field_name=None):
        if field_name:
            self.detail = f'The field "{field_name}" is required but was not provided. Please include this field in your request.'
        else:
            self.detail = self.default_detail
