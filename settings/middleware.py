"""
Custom middleware for debugging and logging
"""
import logging
import json
import time

logger = logging.getLogger('django.request')


class RequestLoggingMiddleware:
    """Log all incoming requests and responses for debugging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Start timer
        start_time = time.time()
        
        # Log incoming request
        logger.info("=" * 80)
        logger.info(f"📨 INCOMING REQUEST")
        logger.info(f"  Method: {request.method}")
        logger.info(f"  Path: {request.path}")
        logger.info(f"  Full URL: {request.build_absolute_uri()}")
        logger.info(f"  Remote IP: {self._get_client_ip(request)}")
        logger.info(f"  Origin: {request.META.get('HTTP_ORIGIN', 'No Origin')}")
        logger.info(f"  User-Agent: {request.META.get('HTTP_USER_AGENT', 'No User-Agent')[:100]}")
        logger.info(f"  Content-Type: {request.META.get('CONTENT_TYPE', 'No Content-Type')}")
        
        # Log query parameters
        if request.GET:
            logger.info(f"  Query Params: {dict(request.GET)}")
        
        # Log request body for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            self._log_request_body(request)
        
        # Log authentication
        if hasattr(request, 'user'):
            if request.user.is_authenticated:
                logger.info(f"  User: {request.user.username} (ID: {request.user.id})")
            else:
                logger.info(f"  User: Anonymous")
        
        # Process request
        try:
            response = self.get_response(request)
        except Exception as e:
            # Log exception
            duration = time.time() - start_time
            logger.error(f"❌ REQUEST FAILED (Duration: {duration:.3f}s)")
            logger.error(f"  Exception: {type(e).__name__}: {str(e)}")
            logger.exception("Full traceback:")
            raise
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        self._log_response(request, response, duration)
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _log_request_body(self, request):
        """Log request body (safely) - Skip to avoid consuming the stream"""
        try:
            content_type = request.META.get('CONTENT_TYPE', '').lower()
            
            # Don't log multipart/form-data bodies (file uploads, etc.)
            if 'multipart/form-data' in content_type:
                logger.info(f"  Request Body: <multipart form data - not logged>")
                return
            
            # Don't read request.body directly as it consumes the stream
            # DRF will parse it later
            if 'application/json' in content_type:
                logger.info(f"  Request Body: <JSON data - will be parsed by DRF>")
            elif request.POST:
                # For form-encoded data, use POST dict (safe to read)
                post_data = dict(request.POST)
                post_data = self._mask_sensitive_data(post_data)
                logger.info(f"  POST Data: {post_data}")
        except Exception as e:
            logger.warning(f"  Could not log request body: {e}")
    
    def _mask_sensitive_data(self, data):
        """Mask sensitive fields like passwords, tokens, etc."""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = ['password', 'token', 'secret', 'api_key', 'apikey', 'authorization']
        masked_data = data.copy()
        
        for key in masked_data:
            if any(field in key.lower() for field in sensitive_fields):
                masked_data[key] = '***MASKED***'
        
        return masked_data
    
    def _log_response(self, request, response, duration):
        """Log response details"""
        status_icon = "✅" if 200 <= response.status_code < 300 else "❌" if response.status_code >= 400 else "⚠️"
        
        logger.info(f"{status_icon} RESPONSE")
        logger.info(f"  Status: {response.status_code}")
        logger.info(f"  Duration: {duration:.3f}s")
        logger.info(f"  Content-Type: {response.get('Content-Type', 'Not specified')}")
        
        # Log CORS headers
        if hasattr(response, 'get'):
            cors_origin = response.get('Access-Control-Allow-Origin')
            if cors_origin:
                logger.info(f"  CORS Origin: {cors_origin}")
        
        # Log response body for errors or small responses
        if response.status_code >= 400:
            self._log_response_body(response)
        
        logger.info("=" * 80)
    
    def _log_response_body(self, response):
        """Log response body for errors"""
        try:
            if hasattr(response, 'content'):
                content_type = response.get('Content-Type', '').lower()
                
                if 'application/json' in content_type:
                    try:
                        body = json.loads(response.content.decode('utf-8'))
                        logger.error(f"  Response Body: {json.dumps(body, indent=2)[:1000]}")
                    except:
                        logger.error(f"  Response Body: {response.content.decode('utf-8')[:500]}")
                elif 'text/html' in content_type:
                    logger.error(f"  Response Body (HTML): {response.content.decode('utf-8')[:500]}")
                else:
                    logger.error(f"  Response Body: {str(response.content)[:500]}")
        except Exception as e:
            logger.warning(f"  Could not parse response body: {e}")


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


    def _log_response_body(self, response):
        """Log response body for errors"""
        try:
            if hasattr(response, 'content'):
                content_type = response.get('Content-Type', '').lower()
                
                if 'application/json' in content_type:
                    try:
                        body = json.loads(response.content.decode('utf-8'))
                        logger.error(f"  Response Body: {json.dumps(body, indent=2)}")
                    except:
                        logger.error(f"  Response Body: {response.content.decode('utf-8')[:500]}")
                elif 'text/html' in content_type:
                    logger.error(f"  Response Body (HTML): {response.content.decode('utf-8')[:500]}")
                else:
                    logger.error(f"  Response Body: {response.content[:500]}")
        except Exception as e:
            logger.warning(f"  Could not parse response body: {e}")


class ErrorLoggingMiddleware:
    """Log all errors with full details"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Detailed error logging for 4xx and 5xx
        if response.status_code >= 400:
            logger.error("=" * 80)
            logger.error(f"❌ ERROR RESPONSE: {response.status_code}")
            logger.error(f"  Path: {request.path}")
            logger.error(f"  Method: {request.method}")
            logger.error(f"  Remote IP: {self._get_client_ip(request)}")
            logger.error(f"  Origin: {request.META.get('HTTP_ORIGIN', 'No Origin')}")
            logger.error(f"  User-Agent: {request.META.get('HTTP_USER_AGENT', 'No User-Agent')[:100]}")
            
            # Log request details that caused error
            if request.GET:
                logger.error(f"  Query Params: {dict(request.GET)}")
            
            # Don't read request.body as it may already be consumed
            if request.method in ['POST', 'PUT', 'PATCH']:
                logger.error(f"  Request Body: <data sent in {request.content_type}>")
            
            # Log response content
            if hasattr(response, 'content'):
                try:
                    content = response.content.decode('utf-8')
                    logger.error(f"  Response Content: {content[:1000]}")
                except:
                    logger.error(f"  Response Content: <binary data>")
            
            logger.error("=" * 80)
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_exception(self, request, exception):
        """Log unhandled exceptions"""
        logger.error("=" * 80)
        logger.error(f"💥 UNHANDLED EXCEPTION")
        logger.error(f"  Path: {request.path}")
        logger.error(f"  Method: {request.method}")
        logger.error(f"  Remote IP: {self._get_client_ip(request)}")
        logger.error(f"  Exception Type: {type(exception).__name__}")
        logger.error(f"  Exception Message: {str(exception)}")
        logger.exception("Full Traceback:")
        logger.error("=" * 80)
        
        return None  # Let Django handle the exception
