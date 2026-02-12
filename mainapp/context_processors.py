"""
Template context processors for browser console logging.
"""
from django.http import HttpRequest


def logging_context(request: HttpRequest) -> dict:
    """
    Context processor that adds logging-related context to templates.
    
    Args:
        request: The current HTTP request object
        
    Returns:
        Dictionary with logging context variables
    """
    context = {
        'debug_consoleLogging': True,  # Enable console logging
        'debug_loggingEnabled': True,  # General logging enabled flag
    }
    
    # Add action logs if they exist from the middleware
    if hasattr(request, 'action_logs') and hasattr(request.action_logs, 'logs'):
        context['action_logs'] = request.action_logs.logs[:10]  # Limit to last 10 actions
        context['has_action_logs'] = True
    else:
        context['has_action_logs'] = False
        context['action_logs'] = []
    
    return context
