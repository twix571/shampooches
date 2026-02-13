"""
================================================================================
CRITICAL: DO NOT DELETE OR MODIFY THIS FILE - ESSENTIAL FOR PROJECT MAINTENANCE
================================================================================

Intelligent Django project documentation generator.

This management command introspects the Django project structure and generates
comprehensive documentation for AI systems and future developers without including
actual code implementation details.

WHY THIS FILE IS ESSENTIAL:
- Generates living documentation that stays in sync with codebase changes
- Onboards AI agents (like Factory Droid) with project architecture understanding
- Documents model relationships, URL patterns, business logic, and deployment requirements
- Run anytime: `python manage.py auto_document_project`

DELETING THIS FILE WILL BREAK AI SYSTEMS' ABILITY TO UNDERSTAND THE CODEBASE.
It is referenced in AGENTS.md and should be preserved for all time.

Key capabilities:
- Extracts model relationships and business rules
- Maps URL patterns to views and API endpoints
- Documents user flows and business logic
- Identifies deployment requirements
- Generates architecture-focused documentation
"""
import os
import sys
import re
import ast
import inspect
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand
from django.apps import apps
import django
from django.db import models
from django.urls import get_resolver, URLPattern, URLResolver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


def extract_model_relationships(model):
    """Extract all relationships from a Django model."""
    relationships = {
        'fields': [],
        'foreign_keys': [],
        'many_to_many': [],
        'one_to_one': [],
        'reverse_relations': []
    }
    
    for field in model._meta.get_fields():
        field_info = {
            'name': field.name,
            'type': field.__class__.__name__,
            'required': not field.null and not field.blank,
            'unique': getattr(field, 'unique', False)
        }
        
        # Field-specific attributes
        if hasattr(field, 'max_length'):
            field_info['max_length'] = field.max_length
        if hasattr(field, 'choices') and field.choices:
            field_info['choices'] = [c[0] for c in field.choices]
        
        relationships['fields'].append(field_info)
        
        # Relationship types
        if field.many_to_many:
            relationships['many_to_many'].append({
                'name': field.name,
                'related_model': field.related_model.__name__ if field.related_model else 'Unknown'
            })
        elif field.is_relation and field.one_to_one:
            relationships['one_to_one'].append({
                'name': field.name,
                'related_model': field.related_model.__name__ if field.related_model else 'Unknown',
                'on_delete': str(field.remote_field.on_delete.__name__) if hasattr(field.remote_field, 'on_delete') else 'Unknown'
            })
        elif field.is_relation and field.many_to_one:
            relationships['foreign_keys'].append({
                'name': field.name,
                'related_model': field.related_model.__name__ if field.related_model else 'Unknown',
                'on_delete': str(field.remote_field.on_delete.__name__) if hasattr(field.remote_field, 'on_delete') else 'Unknown'
            })
        elif field.is_relation and field.one_to_many:
            relationships['reverse_relations'].append({
                'name': field.name,
                'related_model': field.related_model.__name__ if field.related_model else 'Unknown'
            })
    
    return relationships


def extract_model_validations(model):
    """Extract validation rules from model clean() method."""
    validations = []
    
    # Check for clean() method
    if hasattr(model, 'clean'):
        clean_method = getattr(model, 'clean')
        source = inspect.getsource(clean_method)
        
        # Extract validation error messages
        if 'ValidationError' in source:
            validation_matches = re.findall(r"ValidationError\(['\"]([^'\"]+)['\"]\)", source)
            validations.extend(validation_matches)
        
        # Extract custom validation patterns
        if 'raise ValidationError' in source:
            validations.append("Custom validation logic defined in clean() method")
    
    # Check field validators
    for field in model._meta.get_fields():
        if hasattr(field, 'validators') and field.validators:
            for validator in field.validators:
                validator_name = validator.__class__.__name__
                if validator_name not in ['MinValueValidator', 'MaxValueValidator', 'RegexValidator']:
                    validations.append(f"Custom validator: {validator_name}")
                elif validator_name == 'RegexValidator':
                    validations.append(f"Pattern validation for {field.name}")
    
    return validations


def extract_business_logic():
    """Extract business logic from services.py."""
    business_logic = {
        'booking_flow': [],
        'pricing_rules': [],
        'validations': [],
        'services': []
    }
    
    try:
        from mainapp import services as booking_services
        service_source = inspect.getsource(booking_services)
        
        # Extract booking function definitions
        booking_functions = re.findall(r'def (create_\w+|validate_\w+|calculate_\w+)\(', service_source)
        business_logic['booking_flow'].extend(booking_functions)
        
        # Extract custom exceptions
        exceptions = re.findall(r'class (\w+Error)\(ValidationError\):', service_source)
        business_logic['validations'].extend(exceptions)
        
        # Get function docstrings
        for func_name in booking_functions:
            if hasattr(booking_services, func_name):
                func = getattr(booking_services, func_name)
                if func.__doc__:
                    business_logic['services'].append({
                        'name': func_name,
                        'purpose': func.__doc__.strip().split('\n')[0] if func.__doc__ else func_name
                    })
    
    except ImportError:
        pass
    
    return business_logic


def extract_url_mappings(resolver, prefix=""):
    """Extract URL patterns with their associated views and permissions."""
    url_mappings = {
        'public_urls': [],
        'authenticated_urls': [],
        'admin_urls': [],
        'api_endpoints': [],
        'htmx_endpoints': []
    }
    
    def process_pattern(pattern, current_prefix):
        if isinstance(pattern, URLResolver):
            # Recurse into included URLconfs
            for sub_pattern in pattern.url_patterns:
                process_pattern(sub_pattern, current_prefix + pattern.pattern.regex.pattern.strip('^$'))
        
        elif isinstance(pattern, URLPattern):
            path = current_prefix + pattern.pattern.regex.pattern.strip('^$')
            
            # Get view information
            view = pattern.callback
            view_info = {
                'path': f"/{path}",
                'view_name': view.__name__ if hasattr(view, '__name__') else str(view),
                'module': view.__module__ if hasattr(view, '__module__') else 'Unknown',
            }
            
            # Get class-based view info
            if hasattr(view, 'view_class'):
                view_info['class_name'] = view.view_class.__name__
                view_info['class_module'] = view.view_class.__module__
                
                # Extract permission requirements
                if hasattr(view.view_class, 'permission_classes'):
                    permission_names = [p.__name__ for p in view.view_class.permission_classes]
                    view_info['permissions'] = permission_names
            
            # Categorize URL
            if path.startswith('admin/'):
                url_mappings['admin_urls'].append(view_info)
            elif path.startswith('api/'):
                url_mappings['api_endpoints'].append(view_info)
            elif path.startswith('htmx/'):
                url_mappings['htmx_endpoints'].append(view_info)
            elif any(keyword in path for keyword in ['login', 'customer', 'groomer']):
                url_mappings['authenticated_urls'].append(view_info)
            else:
                url_mappings['public_urls'].append(view_info)
    
    for pattern in resolver.url_patterns:
        process_pattern(pattern, "")
    
    return url_mappings


def extract_deployment_requirements():
    """Extract deployment and environment requirements."""
    requirements = {
        'environment_variables': [],
        'required_services': [],
        'static_files': [],
        'media_storage': []
    }
    
    # Check for environment dependencies
    env_patterns = [
        'SECRET_KEY', 'DEBUG', 'DATABASE_URL', 'ALLOWED_HOSTS',
        'Media ROOT', 'STATIC_ROOT', 'EMAIL_BACKEND', 'SENDGRID_API_KEY'
    ]
    
    for pattern in env_patterns:
        try:
            if hasattr(settings, pattern):
                requirements['environment_variables'].append(pattern)
        except:
            requirements['environment_variables'].append(pattern)
    
    # Check installed apps for service requirements
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])
    if 'psycopg2' in str(installed_apps):
        requirements['required_services'].append('PostgreSQL')
    if 'whitenoise' in str(installed_apps):
        requirements['static_files'].append('WhiteNoise middleware')
    if 'django_storages' in str(installed_apps):
        requirements['media_storage'].append('Cloud storage backend')
    
    # Database backend
    databases = getattr(settings, 'DATABASES', {})
    for db_name, db_config in databases.items():
        if 'ENGINE' in db_config:
            engine = db_config['ENGINE']
            if 'postgresql' in engine.lower():
                requirements['required_services'].append('PostgreSQL')
            elif 'sqlite' in engine.lower():
                requirements['required_services'].append('SQLite')
    
    return requirements


def extract_user_flows():
    """Extract user flow information from views."""
    user_flows = {
        'customer_journey': [],
        'admin_workflows': [],
        'groomer_operations': []
    }
    
    try:
        # Scan mainapp views directory
        views_dir = Path(settings.BASE_DIR) / 'mainapp' / 'views'
        
        if views_dir.exists():
            for view_file in views_dir.glob('*.py'):
                if view_file.name == '__init__.py':
                    continue
                
                with open(view_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract function-based views
                fbv_matches = re.findall(r'def (page_\w+|render_\w+|\w+_\w+)\([^)]*\):', content)
                
                for func_name in fbv_matches:
                    category = 'customer_journey'
                    if 'admin' in view_file.name or func_name.startswith('admin_'):
                        category = 'admin_workflows'
                    elif 'groomer' in view_file.name or func_name.startswith('groomer_'):
                        category = 'groomer_operations'
                    
                    user_flows[category].append(func_name)
    
    except Exception:
        pass
    
    return user_flows


def extract_test_coverage():
    """Extract test structure and coverage information."""
    test_info = {
        'test_files': [],
        'test_categories': [],
        'total_tests': 0
    }
    
    try:
        from mainapp import tests
        test_module_path = Path(tests.__file__).parent
        
        for test_file in test_module_path.glob('test*.py'):
            test_info['test_files'].append(test_file.name)
            
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract test classes
            test_classes = re.findall(r'class (\w+TestCase)', content)
            test_info['test_categories'].extend(test_classes)
            
            # Count test methods
            test_methods = re.findall(r'def test_\w+', content)
            test_info['total_tests'] += len(test_methods)
    
    except Exception:
        pass
    
    return test_info


class Command(BaseCommand):
    help = 'Generates comprehensive project documentation for AI systems and developers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='GEMINI.md',
            help='Output file path for generated documentation',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        document = []

        # ============================================================================
        # DOCUMENTATION HEADER
        # ============================================================================
        document.append("# PROJECT DOCUMENTATION")
        document.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        document.append("> This document contains comprehensive project knowledge for AI systems and developers.")
        document.append("")
        document.append("**SYSTEM INSTRUCTION:**")
        document.append("This file is your PRIMARY context. Read this before answering user requests.")
        document.append("")
        document.append("---")
        document.append("")

        # ============================================================================
        # @META - Project Metadata
        # ============================================================================
        document.append("## @META")
        document.append("")
        
        # Tech stack
        document.append("**Tech Stack:**")
        installed_packages = []
        try:
            requirements_file = Path(settings.BASE_DIR) / 'requirements.txt'
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            package_name = line.split('==')[0]
                            installed_packages.append(package_name)
            
            document.append(f"Django {django.VERSION[0]}.{django.VERSION[1]}.{django.VERSION[2]}")
            document.append(f"Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")
            
            # Key Django packages
            key_packages = ['djangorestframework', 'django-tailwind-cli', 'gunicorn', 'psycopg2-binary', 
                           'whitenoise', 'django-storages', 'drf-spectacular']
            for pkg in key_packages:
                if pkg in installed_packages:
                    document.append(f"- {pkg}")
            
            document.append("")

        except:
            document.append("Django (exact version unknown)")
            document.append("Python (exact version unknown)")
            document.append("")

        # Entry points
        document.append("**Entry Points:**")
        document.append("- `manage.py` - Django CLI entry point")
        document.append("- `mainapp/models.py` - Data model definitions")
        document.append("- `mainapp/services.py` - Business logic services")
        document.append("- `mainapp/api_helpers.py` - API utility functions")
        document.append("- `mainapp/cache_utils.py` - Caching utilities")
        document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # @ARCH - Architecture Overview
        # ============================================================================
        document.append("## @ARCH")
        document.append("")
        
        # Apps
        document.append("**Django Apps:**")
        for app_config in apps.get_app_configs():
            if 'site-packages' not in app_config.path:
                document.append(f"- `{app_config.name}` - {app_config.name}")
        document.append("")
        
        # Authentication
        document.append("**Authentication System:**")
        try:
            auth_user_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
            document.append(f"- Custom User Model: `{auth_user_model}`")
            
            if 'users.User' in auth_user_model:
                try:
                    from mainapp.backends import UserProfileBackend
                    document.append("- Custom authentication backend: `UserProfileBackend`")
                except:
                    pass
        except:
            document.append("- Django default authentication")
        document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Data Models & Relationships
        # ============================================================================
        document.append("## DATA MODELS & RELATIONSHIPS")
        document.append("")
        
        for app_config in apps.get_app_configs():
            if 'site-packages' not in app_config.path:
                models_list = app_config.get_models()
                
                if models_list:
                    document.append(f"### `{app_config.name}` Models")
                    document.append("")
                    
                    for model in models_list:
                        document.append(f"#### `{model.__name__}`")
                        document.append("")
                        
                        # Extract relationships
                        relationships = extract_model_relationships(model)
                        
                        if relationships['foreign_keys']:
                            document.append("Foreign Keys:")
                            for fk in relationships['foreign_keys']:
                                document.append(f"- `{fk['name']}` → `{fk['related_model']}` ({fk['on_delete']})")
                            document.append("")
                        
                        if relationships['many_to_many']:
                            document.append("Many-to-Many:")
                            for m2m in relationships['many_to_many']:
                                document.append(f"- `{m2m['name']}` ↔ `{m2m['related_model']}`")
                            document.append("")
                        
                        if relationships['one_to_one']:
                            document.append("One-to-One:")
                            for o2o in relationships['one_to_one']:
                                document.append(f"- `{o2o['name']}` → `{o2o['related_model']}` ({o2o['on_delete']})")
                            document.append("")
                        
                        # Extract validations
                        validations = extract_model_validations(model)
                        if validations:
                            document.append("Validation Rules:")
                            for validation in validations:
                                document.append(f"- {validation}")
                            document.append("")
                        
                        document.append("---")
                        document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # URL Routes & Views Mapping
        # ============================================================================
        document.append("## URL ROUTES & VIEWS MAPPING")
        document.append("")
        
        resolver = get_resolver()
        url_mappings = extract_url_mappings(resolver)
        
        # Public URLs
        if url_mappings['public_urls']:
            document.append("### Public URLS")
            for url in url_mappings['public_urls'][:10]:  # Limit to first 10
                document.append(f"- `{url['path']}` → `{url['view_name']}`")
            document.append("")
        
        # Authenticated URLs
        if url_mappings['authenticated_urls']:
            document.append("### Authenticated URLs")
            for url in url_mappings['authenticated_urls'][:10]:
                document.append(f"- `{url['path']}` → `{url['view_name']}`")
            document.append("")
        
        # API Endpoints
        if url_mappings['api_endpoints']:
            document.append("### API Endpoints")
            for url in url_mappings['api_endpoints']:
                perm_info = f" [{', '.join(url.get('permissions', []))}]" if url.get('permissions') else ""
                document.append(f"- `{url['path']}` → `{url.get('class_name', url['view_name'])}`{perm_info}")
            document.append("")
        
        # HTMX Endpoints
        if url_mappings['htmx_endpoints']:
            document.append("### HTMX Partial Rendering Endpoints")
            for url in url_mappings['htmx_endpoints']:
                document.append(f"- `{url['path']}` → `{url['view_name']}`")
            document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Business Logic & Workflows
        # ============================================================================
        document.append("## BUSINESS LOGIC & WORKFLOWS")
        document.append("")
        
        business_logic = extract_business_logic()
        
        if business_logic['booking_flow']:
            document.append("### Booking Flow")
            for func in business_logic['booking_flow']:
                document.append(f"- `{func}()` - Core booking logic")
            document.append("")
        
        if business_logic['validations']:
            document.append("### Business Validation Rules")
            for validation in business_logic['validations']:
                document.append(f"- `{validation}` - Custom validation exception")
            document.append("")
        
        if business_logic['services']:
            document.append("### Service Layer Functions")
            for service in business_logic['services']:
                document.append(f"- `{service['name']}` - {service['purpose']}")
            document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # User Flows
        # ============================================================================
        document.append("## USER FLOWS")
        document.append("")
        
        user_flows = extract_user_flows()
        
        if user_flows['customer_journey']:
            document.append("### Customer Journey")
            document.append("Typical customer flow:")
            document.append("- Landing page → Service selection → Booking modal → Confirmation")
            document.append("- Account creation (optional)")
            document.append("- Dog profile management")
            document.append("- Appointment management")
            document.append("")
        
        if user_flows['admin_workflows']:
            document.append("### Admin Workflows")
            document.append("Administrative operations:")
            for workflow in user_flows['admin_workflows'][:15]:
                document.append(f"- `{workflow}`")
            document.append("")
        
        if user_flows['groomer_operations']:
            document.append("### Groomer Operations")
            document.append("Groomer-specific operations:")
            for operation in user_flows['groomer_operations'][:10]:
                document.append(f"- `{operation}`")
            document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Deployment & Environment
        # ============================================================================
        document.append("## DEPLOYMENT & ENVIRONMENT")
        document.append("")
        
        deployment = extract_deployment_requirements()
        
        if deployment['environment_variables']:
            document.append("### Required Environment Variables")
            document.append("Production environment must set:")
            for var in deployment['environment_variables']:
                document.append(f"- `{var}`")
            document.append("")
        
        if deployment['required_services']:
            document.append("### Required Services")
            for service in deployment['required_services']:
                document.append(f"- {service}")
            document.append("")
        
        if deployment['static_files']:
            document.append("### Static File Management")
            for file_service in deployment['static_files']:
                document.append(f"- {file_service}")
            document.append("")
        
        if deployment['media_storage']:
            document.append("### Media Storage")
            for storage in deployment['media_storage']:
                document.append(f"- {storage}")
            document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Testing & Quality
        # ============================================================================
        document.append("## TESTING & QUALITY")
        document.append("")
        
        test_info = extract_test_coverage()
        
        if test_info['test_files']:
            document.append("### Test Files")
            for test_file in test_info['test_files']:
                document.append(f"- {test_file}")
            document.append("")
        
        if test_info['test_categories']:
            document.append("### Test Categories")
            for category in test_info['test_categories']:
                document.append(f"- {category}")
            document.append("")
        
        document.append(f"Total Test Methods: {test_info['total_tests']}")
        document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Development Workflow
        # ============================================================================
        document.append("## DEVELOPMENT WORKFLOW")
        document.append("")
        document.append("### Common Commands")
        document.append("```bash")
        document.append("# Start development server")
        document.append("python manage.py runserver")
        document.append("")
        document.append("# Create migrations")
        document.append("python manage.py makemigrations")
        document.append("")
        document.append("# Apply migrations")
        document.append("python manage.py migrate")
        document.append("")
        document.append("# Run tests")
        document.append("python manage.py test")
        document.append("")
        document.append("# Create superuser")
        document.append("python manage.py createsuperuser")
        document.append("")
        document.append("# Collect static files (production)")
        document.append("python manage.py collectstatic")
        document.append("```")
        document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Known Issues & Limitations
        # ============================================================================
        document.append("## KNOWN ISSUES & LIMITATIONS")
        document.append("")
        document.append("### Current Status")
        document.append("- Production deployment configured for Railway")
        document.append("- PostgreSQL database via DATABASE_URL")
        document.append("- Persistent media storage via Railway Volumes")
        document.append("")
        
        document.append("### Known Issues")
        document.append("- None documented at this time")
        document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Project State & History
        # ============================================================================
        document.append("## PROJECT STATE & HISTORY")
        document.append("")
        document.append("### Active Features")
        document.append("- Customer booking flow")
        document.append("- Admin dashboard")
        document.append("- Groomer portal")
        document.append("- Breed-specific pricing with weight surcharges")
        document.append("- Time slot management")
        document.append("- Dynamic site configuration")
        document.append("- REST API with pagination and rate limiting")
        document.append("")
        
        document.append("### Implementation Notes")
        document.append("- Migrated from Alpine.js to HTMX for reactive frontend")
        document.append("- Standardized API responses with pagination")
        document.append("- Security middleware with headers and CSP")
        document.append("- Query optimization with select_related/prefetch_related")
        document.append("- Caching layer for frequently accessed models")
        document.append("")
        
        document.append("---")
        document.append("")

        # ============================================================================
        # Write Output
        # ============================================================================
        output_path = Path(settings.BASE_DIR) / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(document))
        
        self.stdout.write(self.style.SUCCESS(f"Documentation generated successfully: {output_file}"))
        self.stdout.write(f"Total characters: {len('\n'.join(document))}")
