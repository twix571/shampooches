#!/usr/bin/env python
"""
Minimal wsgi entry point for testing if the container is accessible.
This bypasses Django to test if Railway can reach the container.
"""

def application(environ, start_response):
    """Minimal WSGI application that always returns 200 OK."""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Container is responding!\n']
