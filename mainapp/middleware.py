"""
Custom middleware for better error handling and request processing.
"""
import logging
import time
from django.http import JsonResponse
from django.core.exceptions import ValidationError, PermissionDenied
from django.conf import settings

logger = logging.getLogger(__name__)


class ExceptionHandlingMiddleware:
    """
    Middleware to catch all exceptions and return consistent error responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        try:
            response = self.get_response(request)
            # Log request processing time
            duration = time.time() - start_time
            if duration > 2:  # Log slow requests
                logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")
            return response

        except ValidationError as e:
            logger.error(f"ValidationError at {request.path}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Validation error',
                'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)
            }, status=400)

        except PermissionDenied as e:
            logger.warning(f"PermissionDenied at {request.path}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Permission denied',
                'errors': str(e)
            }, status=403)

        except Exception as e:
            logger.error(f"Unhandled exception at {request.path}: {str(e)}", exc_info=True)
            if settings.DEBUG:
                # Return detailed error in debug mode
                return JsonResponse({
                    'success': False,
                    'message': 'Server error',
                    'errors': str(e)
                }, status=500)
            else:
                # Return generic error in production
                return JsonResponse({
                    'success': False,
                    'message': 'Internal server error',
                    'errors': None
                }, status=500)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy - relaxed for development
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self';"
            )

        return response


class QueryLoggingMiddleware:
    """
    Middleware to log database queries in DEBUG mode for performance analysis.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)

        # Import here to avoid import overhead in production
        from django.db import connection

        response = self.get_response(request)

        # Log query count and time
        queries = connection.queries
        if queries:
            total_time = sum(float(q['time']) for q in queries)
            logger.info(
                f"{request.method} {request.path} - "
                f"{len(queries)} queries in {total_time:.3f}s"
            )
            # Log slow queries (>50ms)
            for query in queries:
                if float(query['time']) > 0.05:
                    logger.warning(f"Slow query ({query['time']}s): {query['sql'][:100]}...")

        return response


class ActionLoggingMiddleware:
    """
    Simplified middleware for basic request/response logging.
    Debug details now provided by Django Debug Toolbar.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        try:
            response = self.get_response(request)
            duration = time.time() - start_time
            logger.info(f"{request.method} {request.path} - {response.status_code} in {duration:.3f}s")
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{request.method} {request.path} - {e.__class__.__name__} in {duration:.3f}s", exc_info=True)
            raise
