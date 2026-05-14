import logging

logger = logging.getLogger(__name__)

class DebugCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'api/predict' in request.path:
            logger.warning(f"DEBUG: {request.method} {request.path}")
            from django.views.decorators.csrf import csrf_exempt
            logger.warning(f"DEBUG: csrf_exempt value: {getattr(request.resolver_match.func if request.resolver_match else None, 'csrf_exempt', 'NOT FOUND')}")
        
        response = self.get_response(request)
        return response
