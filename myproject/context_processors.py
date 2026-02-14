"""
Context processors for myproject.

This module provides context processors that add data to all template contexts.
"""
from mainapp.models import SiteConfig


def site_config_context_processor(request):
    """
    Add site_config to all template contexts.

    This context processor retrieves the active SiteConfig and adds it to
    the template context. If no active SiteConfig exists, it returns None.

    Args:
        request: The HTTP request object

    Returns:
        dict: Dictionary with 'site_config' key
    """
    site_config = SiteConfig.get_active_config()
    return {'site_config': site_config}
