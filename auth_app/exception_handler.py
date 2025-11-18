"""
Custom exception handler for consistent error responses
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses
    with descriptive messages and proper error codes.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response format
        custom_response_data = {
            'error': True,
            'error_code': getattr(exc, 'default_code', 'error'),
            'message': None,
            'details': None
        }

        # Handle different response formats
        if isinstance(response.data, dict):
            # If there's a detail field, use it as the main message
            if 'detail' in response.data:
                custom_response_data['message'] = response.data['detail']
            # If there are field errors, include them in details
            elif any(key != 'detail' for key in response.data.keys()):
                custom_response_data['message'] = 'Validation error occurred'
                custom_response_data['details'] = response.data
            else:
                custom_response_data['message'] = str(response.data)
        elif isinstance(response.data, list):
            custom_response_data['message'] = response.data[0] if response.data else 'An error occurred'
        else:
            custom_response_data['message'] = str(response.data)

        response.data = custom_response_data

    return response
