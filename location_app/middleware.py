import traceback
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    """
    Middleware to handle all unhandled exceptions globally and return standardized JSON responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        logger.error(f"Unhandled exception: {exception}\n{traceback.format_exc()}")
        
        # We only want to return JSON for API endpoints
        if request.path.startswith('/api/'):
            status_code = 500
            error_message = "An unexpected error occurred."
            
            if isinstance(exception, ValueError):
                status_code = 400
                error_message = str(exception)
                
            return JsonResponse({
                "success": False,
                "error": error_message,
                "error_type": exception.__class__.__name__
            }, status=status_code)
        
        # Let default error handling take over for non-API routes
        return None
