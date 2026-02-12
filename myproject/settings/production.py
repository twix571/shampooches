"""
Production Django settings for myproject project.
"""
import logging
from pathlib import Path
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

DEBUG = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = Path('/app/staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

WHITENOISE_USE_FINDERS = True
WHITENOISE_IGNORE_MISSING_FILE = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_MAX_AGE = 31536000  # 1 year
WHITENOISE_GZIP_ALL_EXTENSIONS = True
WHITENOISE_GZIP_EXCLUDE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.woff', '.woff2']
WHITENOISE_ROOT = Path('/app/staticfiles')

ALLOWED_HOSTS_setting = os.getenv('ALLOWED_HOSTS', '').strip()
if ALLOWED_HOSTS_setting:
    ALLOWED_HOSTS = ALLOWED_HOSTS_setting.split(',')
else:
    # Fallback to allow all Railway domains
    ALLOWED_HOSTS = ['*']

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

# Media files - Use Railway volume for persistent storage
# Volume should be mounted at /data in Railway dashboard
MEDIA_ROOT = Path('/data/media')
MEDIA_URL = 'media/'

# Security Settings (Production)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# SSL Redirect - Only enable if explicitly set, to avoid health check issues
# Railway handles SSL termination, so this should generally be False in Railway
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging Configuration (Production)
# Configure Django logging to send errors to console
# Sentry integration is configured separately below

# Simplify middleware for production to avoid blocking issues
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mainapp.middleware.ExceptionHandlingMiddleware',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARN',
            'propagate': False,
        },
        'mainapp': {
            'handlers': ['console'],
            'level': 'DEBUG',
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
# Override with more restrictive settings for production - no 'unsafe-inline' or 'unsafe-eval'

# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = ("'self'", "https://cdn.tailwindcss.com", "https://cdn.jsdelivr.net", "https://jsdelivr.net", "https://unpkg.com")
# CSP_STYLE_SRC = ("'self'", "https://fonts.googleapis.com", "https://fonts.gstatic.com")
# CSP_IMG_SRC = ("'self'", "data:", "https:")
# CSP_FONT_SRC = ("'self'", "data:", "https://fonts.googleapis.com", "https://fonts.gstatic.com")
# CSP_CONNECT_SRC = ("'self'",)
# CSP_FORM_ACTION = ("'self'",)
# CSP_MEDIA_SRC = ("'self'",)
# CSP_FRAME_ANCESTORS = ("'none'",)
# CSP_BASE_URI = ("'self'",)
# CSP_FRAME_SRC = ("'none'",)
# CSP_OBJECT_SRC = ("'none'",)
# CSP_REPORT_URI = os.getenv('CSP_REPORT_URI',)
# CSP_ENFORCE = True

# Security Note: Consider renaming the admin URL from /admin/ to something unpredictable
# to reduce brute-force attacks. This can be done in myproject/urls.py.
