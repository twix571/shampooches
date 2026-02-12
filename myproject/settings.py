"""
Django settings for myproject project.

This settings module includes production-ready configurations,
proper security settings, and logging configuration.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import sys
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-placeholder-key')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Security warning in development mode
if DEBUG:
    print("=" * 80)
    print("WARNING: DEBUG mode is enabled. Do not use in production!")
    print("=" * 80)

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')


# ============================================================================
# Application Definition
# ============================================================================

INSTALLED_APPS = [
    'django_browser_reload',
    'whitenoise.runserver_nostatic',
    'django_cleanup',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tailwind_cli',
    'mainapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
    'mainapp.middleware.SecurityHeadersMiddleware',
    'mainapp.middleware.ExceptionHandlingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mainapp.middleware.QueryLoggingMiddleware',
    'mainapp.middleware.ActionLoggingMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mainapp.context_processors.logging_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'


# ============================================================================
# Database Configuration
# ============================================================================

# Use DATABASE_URL if provided (Railway, production, or local PostgreSQL)
# Otherwise fallback to SQLite for development
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # For PostgreSQL, ensure database name is provided
    if 'postgres' in DATABASE_URL:
        # PostgreSQL specific settings
        DATABASES['default']['OPTIONS'] = {
            'connect_timeout': 10,
        }
else:
    # Default to SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ============================================================================
# Password Validation
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================================================
# Internationalization
# ============================================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_TZ = True


# ============================================================================
# Static Files
# ============================================================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files - Configure for Railway Volumes in production
# Railway provides persistent storage at /data by default
# For local development, use media/ directory
if not DEBUG:
    # Production: Use Railway Volumes (/data)
    MEDIA_ROOT = Path('/data/media')
else:
    # Development: Use media/ directory
    MEDIA_ROOT = BASE_DIR / 'media'

MEDIA_URL = 'media/'


# ============================================================================
# Default Primary Key Field Type
# ============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================================
# Authentication Configuration
# ============================================================================

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

AUTHENTICATION_BACKENDS = [
    'mainapp.backends.UserProfileBackend',
    'django.contrib.auth.backends.ModelBackend',
]


# ============================================================================
# REST Framework Configuration
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '500/day',
    },
    'EXCEPTION_HANDLER': 'mainapp.api_helpers.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema',
}


# ============================================================================
# Caching Configuration
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_KEY_PREFIX = 'grooming_service'


# ============================================================================
# Logging Configuration
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'mainapp': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
}


# ============================================================================
# Security Settings (Production)
# ============================================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    # Production security settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Additional production logging
    LOGGING['handlers']['file']['level'] = 'WARNING'
else:
    # Development settings
    LOGGING['handlers']['console']['level'] = 'DEBUG'


# ============================================================================
# Environment-Specific Settings
# ============================================================================

if os.environ.get('ENVIRONMENT') == 'production':
    # Production environment settings
    DEBUG = False
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

    # Use Redis for caching in production (if REDIS_URL is provided)
    if os.getenv('REDIS_URL'):
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            }
        }

elif os.environ.get('ENVIRONMENT') == 'testing':
    # Testing environment settings
    TESTING = True
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }


# ============================================================================
# Custom Settings
# ============================================================================

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


# ============================================================================
# Static File Optimization
# ============================================================================

# Whitenoise configuration for static files with caching
WHITENOISE_USE_FINDERS = True
WHITENOISE_STATIC_PREFIX = 'static/'
WHITENOISE_SKIP_SERVE_VERIFY = False

# Enable static file caching for long periods in production
if not DEBUG:
    # Enable GZIP compression
    WHITENOISE_GZIP_ALL_EXTENSIONS = True
    WHITENOISE_GZIP_EXCLUDE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    # Set long cache times for static assets (1 year)
    WHITENOISE_MAX_AGE = 365 * 24 * 60 * 60

    # Enable immutable caching for versioned files
    WHITENOISE_IMMUTABLE_FILE_TEST = lambda f: '?' in f

    # Enable brotli compression (if available)
    try:
        import brotli
        WHITENOISE_USE_FINDERS = True
        WHITENOISE_USE_MANIFEST = True
    except ImportError:
        pass
else:
    WhitenoiseMiddleware = None
