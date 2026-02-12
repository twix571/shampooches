"""
Production Django settings for myproject project.
"""
import logging
import dj_database_url

from .base import *

# Email Backend Configuration (Production)
# Using Anymail for transactional email via SendGrid or Mailgun
# Supported backends: sendgrid, mailgun, sparkpost, ses, postmark, etc.
ANYMAIL = {
    'EMAIL_BACKEND': 'anymail.backends.sendgrid.EmailBackend',
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
    # Alternative: Use Mailgun instead
    # 'MAILGUN_API_KEY': os.getenv('MAILGUN_API_KEY'),
    # 'MAILGUN_SENDER_DOMAIN': os.getenv('MAILGUN_SENDER_DOMAIN'),
}

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'anymail.backends.sendgrid.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@shampooches.com')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'admin@shampooches.com')

# Email timeout and retry settings
EMAIL_TIMEOUT = 30
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None

# Production-specific email settings
EMAIL_SUBJECT_PREFIX = '[Shampooches] '

# Anymail integration
INSTALLED_APPS += ['anymail']

# Remove development-only apps
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_browser_reload' and app != 'debug_toolbar']

DEBUG = False

# WhiteNoise for static file serving in production
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

# Remove development-only middleware
MIDDLEWARE = [m for m in MIDDLEWARE if 'django_browser_reload' not in m and 'debug_toolbar' not in m]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

WHITENOISE_USE_FINDERS = True
WHITENOISE_IGNORE_MISSING_FILE = True
WHITENOISE_MANIFEST_STRICT = True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database (Production - Railway PostgreSQL via DATABASE_URL)
# Railway automatically provides DATABASE_URL environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# Media files - Railway Volumes for persistent storage
# Railway provides persistent storage at /data by default
# Ensure a volume is mounted at /data in Railway
MEDIA_ROOT = Path('/data/media')
MEDIA_URL = 'media/'

# Security Settings (Production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging Configuration (Production)
# Configure Django logging to send errors to console
# Sentry integration is configured separately below

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"levelname": "%(levelname)s", "asctime": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'mainapp': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Sentry Integration for Production (if SENTRY_DSN is set)
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
    )

# Content Security Policy (CSP)
# Implement CSP headers to strictly define where scripts, styles, and media can load from.
# Override with more restrictive settings for production

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "https://cdn.tailwindcss.com", "https://cdn.jsdelivr.net", "https://jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "https://fonts.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:",)
CSP_FONT_SRC = ("'self'", "data:", "https://fonts.googleapis.com", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_MEDIA_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_REPORT_URI = os.getenv('CSP_REPORT_URI',)

# Rename Admin URL
# Change the default admin/ URL path to something unpredictable to reduce brute-force attempts.
# This is handled in myproject/urls.py - ensure it's renamed in production.
