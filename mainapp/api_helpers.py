"""
API helper utilities for standardizing responses and error handling.
Centralized API response formatting and pagination settings.
"""
import logging
from typing import Any, Dict, Optional, Type, Callable
from functools import wraps

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler, APIView
from rest_framework.serializers import Serializer


logger = logging.getLogger(__name__)


class StandardResponse:
    """
    Standard API response wrapper for consistent response format across all endpoints.
    
    Response structure:
    {
        "success": bool,
        "message": str,
        "data": dict|list,
        "errors": dict,
        "meta": dict
    }
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict] = None
    ) -> Response:
        """
        Create a success response.
        
        Args:
            data: The response data
            message: Success message
            status_code: HTTP status code
            meta: Optional metadata (pagination info, etc.)
        
        Returns:
            Response object with standardized format
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "errors": None
        }
        if meta:
            response_data["meta"] = meta
        return Response(response_data, status=status_code)

    @staticmethod
    def error(
        message: str = "Error",
        errors: Optional[Dict] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None
    ) -> Response:
        """
        Create an error response.
        
        Args:
            message: Error message
            errors: Detailed error dictionary
            status_code: HTTP status code
            data: Optional data to return with error
        
        Returns:
            Response object with standardized format
        """
        response_data = {
            "success": False,
            "message": message,
            "data": data,
            "errors": errors
        }
        return Response(response_data, status=status_code)


class StandardPagination(PageNumberPagination):
    """
    Standard pagination class with configurable page size and metadata.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Return paginated response with standard format and metadata.
        """
        return StandardResponse.success(
            data=data,
            message="Data retrieved successfully",
            meta={
                'pagination': {
                    'count': self.page.paginator.count,
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                    'current_page': self.page.number,
                    'total_pages': self.page.paginator.num_pages,
                    'page_size': self.page.paginator.per_page
                }
            }
        )


def custom_exception_handler(exc, context):
    """
    Custom exception handler for better error responses.
    Wraps DRF's default exception handler with standardized format.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Transform DRF response to our standard format
        return StandardResponse.error(
            message=_get_error_message(exc),
            errors=response.data if hasattr(response, 'data') else None,
            status_code=response.status_code
        )

    # Handle non-DRF exceptions (Django validation errors, etc.)
    return StandardResponse.error(
        message=_get_error_message(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _get_error_message(exc: Exception) -> str:
    """Extract meaningful error message from exception."""
    message = str(exc)
    if hasattr(exc, 'detail'):
        return getattr(exc, 'detail')
    if hasattr(exc, 'message'):
        return getattr(exc, 'message')
    return message or "An error occurred"


class StandardAPIView(APIView):
    """
    Base API view that provides standardized request handling.
    
    Features:
    - Automatic serializer validation
    - Consistent error handling
    - Request/response logging
    - Standard response formatting
    
    Usage:
        class MyView(StandardAPIView):
            def post(self, request):
                # Validate request data
                data = self.validate_request(
                    request,
                    MySerializer,
                    error_message='Invalid request data'
                )
                
                # Process logic
                result = process_data(data)
                
                return self.success_response(
                    data=result,
                    message='Success!'
                )
    """
    
    def validate_request(
        self,
        request,
        serializer_class: Type[Serializer],
        error_message: str = 'Validation failed'
    ) -> Optional[Dict]:
        """
        Validate request data using serializer.
        
        Args:
            request: HTTP request object
            serializer_class: Serializer class to validate with
            error_message: Custom error message for validation failures
        
        Returns:
            Validated data dict if validation succeeds, None otherwise
            (Error response is automatically sent on failure)
        """
        serializer = serializer_class(data=request.data)
        if not serializer.is_valid():
            return StandardResponse.error(
                message=error_message,
                errors=serializer.errors
            )
        return serializer.validated_data
    
    def success_response(
        self,
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict] = None
    ) -> Response:
        """
        Create a success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            meta: Optional metadata
        
        Returns:
            Standard success response
        """
        return StandardResponse.success(
            data=data,
            message=message,
            status_code=status_code,
            meta=meta
        )
    
    def error_response(
        self,
        message: str = "Error",
        errors: Optional[Dict] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None
    ) -> Response:
        """
        Create an error response.
        
        Args:
            message: Error message
            errors: Detailed error dictionary
            status_code: HTTP status code
            data: Optional data to return with error
        
        Returns:
            Standard error response
        """
        return StandardResponse.error(
            message=message,
            errors=errors,
            status_code=status_code,
            data=data
        )


def handle_api_errors(view_name: str = None):
    """
    Decorator for handling API errors consistently.
    
    Args:
        view_name: Name of the view for logging purposes
    
    Usage:
        @handle_api_errors('MyView')
        def post(self, request):
            # Implementation
            pass
    
    The decorator will:
    - Catch all exceptions
    - Log them with context
    - Return standardized error responses
    """
    def decorator(method):
        @wraps(method)
        def wrapper(self, request, *args, **kwargs):
            try:
                return method(self, request, *args, **kwargs)
            except Exception as e:
                name = view_name or self.__class__.__name__
                logger.exception(f"Error in {name}: {e}")
                return StandardResponse.error(
                    message=f'Failed to process request',
                    errors=str(e),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return wrapper
    return decorator
