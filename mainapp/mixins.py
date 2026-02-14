"""
View mixins for common Django view functionality.

This module provides reusable mixins for common view patterns such as
authentication checks, admin access control, and request validation.
"""

from typing import Any, Callable, Optional

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponseBase, JsonResponse
from django.shortcuts import redirect


class LoginRequiredMixin:
    """Mixin that ensures a user is logged in.

    Redirects to login page if user is not authenticated.
    """

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Dispatch method that checks authentication.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response or redirect to login.

        Raises:
            PermissionDenied: If authentication fails.
        """
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin:
    """Mixin that ensures a user has admin access.

    Redirects non-admin users to customer landing page.
    """

    login_url = 'customer_landing'

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Dispatch method that checks admin access.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response or redirect to login.

        Raises:
            PermissionDenied: If not admin.
        """
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(
                request,
                'You do not have permission to access this page.'
            )
            return redirect(self.login_url)

        return super().dispatch(request, *args, **kwargs)


class GroomerRequiredMixin:
    """Mixin that ensures a user is a groomer or admin.

    Redirects unauthorized users to customer landing page.
    """

    login_url = 'customer_landing'

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Dispatch method that checks groomer access.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response or redirect to login.

        Raises:
            PermissionDenied: If not groomer or admin.
        """
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        user_type = getattr(request.user, 'user_type', None)
        if user_type not in ['admin', 'groomer_manager', 'groomer']:
            messages.error(
                request,
                'You do not have permission to access this page.'
            )
            return redirect(self.login_url)

        return super().dispatch(request, *args, **kwargs)


class JsonRequestMixin:
    """Mixin for handling JSON requests in views.

    Provides automatic JSON parsing and validation helpers.
    """

    def parse_json_body(self, request: HttpRequest) -> tuple[bool, Optional[dict], Optional[JsonResponse]]:
        """Parse JSON request body.

        Args:
            request: HTTP request object.

        Returns:
            Tuple of (success, data, error_response).
        """
        try:
            data = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
            import json
            return True, json.loads(data), None
        except json.JSONDecodeError as e:
            return False, None, JsonResponse(
                {'success': False, 'error': f'Invalid JSON: {str(e)}'},
                status=400
            )
        except Exception as e:
            return False, None, JsonResponse(
                {'success': False, 'error': f'Error parsing request: {str(e)}'},
                status=500
            )

    def validate_required_fields(
        self,
        data: dict,
        required_fields: list[str]
    ) -> tuple[bool, Optional[JsonResponse]]:
        """Validate that required fields are present.

        Args:
            data: Request data dictionary.
            required_fields: List of required field names.

        Returns:
            Tuple of (valid, error_response).
        """
        missing = [field for field in required_fields if field not in data or not data.get(field)]
        if missing:
            return False, JsonResponse(
                {
                    'success': False,
                    'error': 'Validation failed',
                    'errors': {'missing': missing}
                },
                status=400
            )
        return True, None


class FormValidationMixin:
    """Mixin for handling form validation."""

    def form_invalid(self, form: Any) -> HttpResponseBase:
        """Handle invalid form submission.

        Args:
            form: Form that failed validation.

        Returns:
            JSON response with errors for AJAX, or default behavior.
        """
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': dict(form.errors.items())
            }, status=400)
        return super().form_invalid(form)

    def form_valid(self, form: Any) -> HttpResponseBase:
        """Handle valid form submission.

        Args:
            form: Form that passed validation.

        Returns:
            JSON response for AJAX, or default behavior.
        """
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True}, status=200)
        return super().form_valid(form)


class JsonResponseMixin:
    """Mixin for views that return JSON responses."""

    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def json_response(
        self,
        success: bool = True,
        message: str = '',
        data: Optional[dict] = None,
        status: int = 200,
        **kwargs: Any
    ) -> JsonResponse:
        """Create a standardized JSON response.

        Args:
            success: Whether the request was successful.
            message: Optional success/error message.
            data: Optional data to include.
            status: HTTP status code.
            **kwargs: Additional response fields.

        Returns:
            JsonResponse object.
        """
        response: dict[str, Any] = {'success': success}
        if message:
            response['message'] = message
        if data is not None:
            response['data'] = data
        response.update(kwargs)
        return JsonResponse(response, status=status)

    def json_success(
        self,
        message: str = '',
        data: Optional[dict] = None,
        **kwargs: Any
    ) -> JsonResponse:
        """Create a success JSON response.

        Args:
            message: Success message.
            data: Optional data to include.
            **kwargs: Additional response fields.

        Returns:
            JsonResponse with status 200.
        """
        return self.json_response(
            success=True,
            message=message,
            data=data,
            status=200,
            **kwargs
        )

    def json_error(
        self,
        message: str,
        status: int = 400,
        errors: Optional[dict[str, Any]] = None,
        **kwargs: Any
    ) -> JsonResponse:
        """Create an error JSON response.

        Args:
            message: Error message.
            status: HTTP status code.
            errors: Optional error details.
            **kwargs: Additional response fields.

        Returns:
            JsonResponse with specified status.
        """
        response: dict[str, Any] = {
            'success': False,
            'error': message
        }
        if errors:
            response['errors'] = errors
        response.update(kwargs)
        return JsonResponse(response, status=status)


class ObjectPermissionMixin:
    """Mixin for object-level permissions.

    Subclasses must implement check_object_permission method.
    """

    def check_object_permission(
        self,
        request: HttpRequest,
        obj: Any
    ) -> bool:
        """Check if user has permission to access object.

        Args:
            request: HTTP request object.
            obj: Object to check permission for.

        Returns:
            True if user has permission, False otherwise.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement check_object_permission()"
        )

    def get_object(self, queryset: Optional[Any] = None) -> Any:
        """Get object and check permission.

        Args:
            queryset: Optional queryset.

        Returns:
            Object instance.

        Raises:
            PermissionDenied: If user lacks permission.
        """
        obj = super().get_object(queryset)

        if not self.check_object_permission(self.request, obj):
            raise PermissionDenied(
                "You do not have permission to access this object."
            )

        return obj


class StaffOnlyMixin:
    """Mixin that restricts access to staff members (admin or superuser)."""

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Dispatch method that checks staff status.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response or raises PermissionDenied.

        Raises:
            PermissionDenied: If user is not staff.
        """
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        if not request.user.is_staff:
            raise PermissionDenied(
                "This page is restricted to staff members."
            )

        return super().dispatch(request, *args, **kwargs)


class SuperuserOnlyMixin:
    """Mixin that restricts access to superusers only."""

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Dispatch method that checks superuser status.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response or raises PermissionDenied.

        Raises:
            PermissionDenied: If user is not a superuser.
        """
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        if not request.user.is_superuser:
            raise PermissionDenied(
                "This page is restricted to administrators."
            )

        return super().dispatch(request, *args, **kwargs)
