"""
Logging utilities for comprehensive browser console logging.
"""
import logging
from django.utils import timezone
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class ViewLogger:
    """
    Helper class for logging view actions that will be displayed in browser console.
    """
    
    def __init__(self, request: HttpRequest):
        self.request = request
        
    def log_action(self, action: str, details: dict = None, category: str = 'View Action'):
        """
        Log a specific view action.
        
        Args:
            action: Description of the action being performed
            details: Additional details about the action
            category: Category of the action (e.g., 'Database Query', 'Form Submission')
        """
        if hasattr(self.request, 'log_action'):
            return self.request.log_action(category, action, details)
        return None
    
    def log_form_submission(self, form_data: dict, form_name: str = 'Unknown Form'):
        """Log form submission with sanitized data."""
        sanitized_data = {}
        for key, value in form_data.items():
            if any(secret in key.lower() for secret in ['password', 'secret', 'token', 'credit_card']):
                sanitized_data[key] = '[REDACTED]'
            else:
                sanitized_data[key] = value
        
        return self.log_action(
            f'Form submission: {form_name}',
            {'fields': sanitized_data},
            'Form Submission'
        )
    
    def log_database_operation(self, operation: str, query_details: dict):
        """Log database operations."""
        return self.log_action(
            f'{operation} database operation',
            query_details,
            'Database Query'
        )
    
    def log_api_call(self, endpoint: str, method: str, params: dict = None):
        """Log API calls made within a view."""
        sanitized_params = {}
        if params:
            for key, value in params.items():
                if any(secret in key.lower() for secret in ['password', 'secret', 'token']):
                    sanitized_params[key] = '[REDACTED]'
                else:
                    sanitized_params[key] = value
        
        return self.log_action(
            f'API call: {method} {endpoint}',
            {'params': sanitized_params},
            'API Call'
        )
    
    def log_business_logic(self, logic_description: str, details: dict = None):
        """Log business logic execution."""
        return self.log_action(
            f'Business logic: {logic_description}',
            details,
            'Business Logic'
        )
    
    def log_error(self, error_message: str, error_details: dict = None):
        """Log errors that occur during view execution."""
        return self.log_action(
            f'Error: {error_message}',
            error_details,
            'Error'
        )


def get_view_logger(request: HttpRequest) -> ViewLogger:
    """
    Get a view logger instance for the current request.
    
    Args:
        request: The current HTTP request object
        
    Returns:
        ViewLogger instance configured for this request
    """
    return ViewLogger(request)
