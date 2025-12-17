"""
Custom middleware for debugging and logging
"""
import logging

logger = logging.getLogger('django.request')


class RequestLoggingMiddleware:
    """Log all incoming requests for debugging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log incoming request
        logger.info(f"📨 Incoming Request:")
        logger.info(f"  Method: {request.method}")
        logger.info(f"  Path: {request.path}")
        logger.info(f"  Origin: {request.META.get('HTTP_ORIGIN', 'No Origin')}")
        logger.info(f"  User-Agent: {request.META.get('HTTP_USER_AGENT', 'No User-Agent')}")
        logger.info(f"  Content-Type: {request.META.get('CONTENT_TYPE', 'No Content-Type')}")
        
        # Process request
        response = self.get_response(request)
        
        # Log response
        logger.info(f"📤 Response Status: {response.status_code}")
        if hasattr(response, 'get'):
            logger.info(f"  CORS Headers: {response.get('Access-Control-Allow-Origin', 'Not Set')}")
        
        return response


class CORSDebugMiddleware:
    """Debug CORS issues"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        origin = request.META.get('HTTP_ORIGIN')
        
        if origin:
            logger.info(f"🌐 CORS Request from: {origin}")
        
        response = self.get_response(request)
        
        # Log CORS headers in response
        if origin:
            logger.info(f"🔓 CORS Response Headers:")
            logger.info(f"  Access-Control-Allow-Origin: {response.get('Access-Control-Allow-Origin', 'NOT SET')}")
            logger.info(f"  Access-Control-Allow-Credentials: {response.get('Access-Control-Allow-Credentials', 'NOT SET')}")
        
        return response


class ErrorLoggingMiddleware:
    """Log all errors with full details"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log errors
        if response.status_code >= 400:
            logger.error(f"❌ Error Response:")
            logger.error(f"  Status: {response.status_code}")
            logger.error(f"  Path: {request.path}")
            logger.error(f"  Method: {request.method}")
            logger.error(f"  Origin: {request.META.get('HTTP_ORIGIN', 'No Origin')}")
            
            if hasattr(response, 'content'):
                logger.error(f"  Response Content: {response.content[:500]}")  # First 500 chars
        
        return response
    
    def process_exception(self, request, exception):
        """Log unhandled exceptions"""
        logger.error(f"💥 Unhandled Exception:")
        logger.error(f"  Path: {request.path}")
        logger.error(f"  Method: {request.method}")
        logger.error(f"  Exception: {str(exception)}")
        logger.error(f"  Exception Type: {type(exception).__name__}")
        
        return None  # Let Django handle the exception
