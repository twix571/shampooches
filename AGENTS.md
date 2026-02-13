# Django Project Conventions Guide

This document outlines the conventions, patterns, and best practices used throughout this Django groomer salon application. Agents should follow these guidelines when working on this codebase.

## Essential Project Tools & Analysis Scripts

### Project Documentation Generator (CRITICAL - DO NOT DELETE)
**`python manage.py auto_document_project`**
- **Purpose**: Generates living documentation that stays in sync with the codebase
- **Why Essential**: Onboards AI agents with project architecture understanding; documents models, URLs, business logic, and deployment requirements
- **Status**: Referenced throughout this file; DELETING WILL BREAK AI SYSTEMS' ABILITY TO UNDERSTAND THE CODEBASE
- **Run When**: After major structural changes or when onboarding new AI agents

### Database State Analysis (`analyze_db_state.py`)
**Purpose**: Analyzes database integrity, particularly the User-Customer relationship
- Detects orphaned users (customer type users without Customer profile)
- Provides breakdown by user type (admin, customer, groomer)
- Lists all existing Customer records with their User associations
- Use this script when debugging authentication or user creation issues

**How to run:**
```bash
python analyze_db_state.py
```

**Important**: This script identifies cases where a User of type='customer' was created but the corresponding Customer profile was not created via signals. This is a known issue and should be checked regularly.

### Authentication System Diagnostics (`diagnostic_auth_system.py`)
**Purpose**: Comprehensive authentication system debugging
- Tests admin login with various credentials
- Checks superuser creation and authentication
- Verifies User-Customer relationship integrity
- Tests custom authentication backends
- Provides detailed diagnostic output for auth issues

**How to run:**
```bash
python diagnostic_auth_system.py
```

**Use for**: Debugging login failures, authentication middleware issues, permission problems

### Fix Orphaned Users (`fix_orphaned_users.py`)
**Purpose**: Automated fix for orphaned customer users
- Identifies Users without Customer profiles
- Automatically creates missing Customer profiles
- Handles data migration for orphaned records
- Provides log of all corrections made

**How to run:**
```bash
python fix_orphaned_users.py
```

**Note**: Use `analyze_db_state.py` first to understand the extent of the issue before running the fix script.

### Admin Auth Debug Script (`debug_admin_auth.py`)
**Purpose**: Debug admin authentication specifically
- Tests admin login flow
- Checks superuser authentication
- Verifies admin access permissions
- Identifies middleware or settings issues affecting admin

**How to run:**
```bash
python debug_admin_auth.py
```

### Test Admin Login (`test_admin_login.py`)
**Purpose**: Automated testing of admin login functionality
- Tests various admin credentials
- Verifies login success/failure scenarios
- Checks admin session management
- Provides test results for admin authentication

**How to run:**
```bash
python test_admin_login.py
```

### Other Diagnostic Utilities
- `create_superuser.py`: Creates superuser with environment variable configuration
- `delete_orphaned_users_now.py`: Immediate deletion of orphaned users (use with caution)
- `manage_superusers.py`: Script for managing superuser accounts
- `test_auth_debug.py`: Additional authentication testing utility

### Code Size Analysis (`analyze_code_size.py`)
**Purpose**: Analyzes codebase size and identifies optimization opportunities
- Counts total lines of code across all Python files
- Identifies largest files (top 20)
- Estimates potential code reduction opportunities
- Provides optimization recommendations

**How to run:**
```bash
python analyze_code_size.py
```

**Use for**: Code refactoring, identifying large files for splitting, tracking codebase growth

## Recent Frontend Simplifications (February 2026)

### Overview
The frontend has undergone significant simplification to reduce bundle size, improve maintainability, and eliminate redundant code. All changes preserve functionality while reducing complexity.

### Files Removed
- `static/css/tailwind.css` (50KB) - Unused (using Tailwind CDN)
- `static/js/comprehensive-logger.js` (21KB) - Overkill for production
- `static/js/modal-utils.js` (3KB) - Consolidated into modal.js
- `mainapp/static/js/services-modal-state.js` - Unused
- `mainapp/static/js/schedule-modal.js` - Duplicate, consolidated

### Templates Removed (unused partials)
- `mainapp/templates/mainapp/partials/loading_spinner.html`
- `mainapp/templates/mainapp/partials/empty_state.html`
- `mainapp/templates/mainapp/partials/tabs.html`
- `mainapp/templates/mainapp/partials/time_slots_list.html`
- `mainapp/templates/mainapp/partials/booking_form_inner.html`

### Key Refactoring Changes

#### 1. Modal System Consolidation
- **Before**: ~300 lines of modal JavaScript duplicated in `base.html` inline script
- **After**: Extracted to `static/js/modal.js` (10KB)
- **Benefits**: Eliminates code duplication, improves maintainability, cached across page loads

#### 2. Schedule Modal Simplification
- **Before**: 21.7 KB with custom confirmation dialog, complex date parsing
- **After**: 16.3 KB (~25% reduction)
- **Changes**:
  - Replaced custom confirm dialog (~65 lines) with native `confirm()`
  - Simplified date parsing (removed multi-strategy approach)
  - Consolidated utility functions
- **Benefits**: Smaller bundle, simpler code, native browser UI

#### 3. JavaScript Structure Reorganization
- **Global static files** (`static/js/`):
  - `modal.js` - Global modal/torch system
  - `schedule-modal.js` - Scheduling functionality
- **App-specific files** (`mainapp/static/js/`):
  - `weight-pricing-modal.js` - Pricing management

### Total Impact
- **Removed**: ~92KB of unused code (JavaScript + CSS)
- **Reduced**: Schedule-modal.js by 25% (21.7KB → 16.3KB)
- **Deleted**: 5 unused partial templates
- **Result**: Cleaner codebase, faster page loads, easier maintenance

### When Adding New JavaScript
1. Prefer existing patterns (HTMX for server interactions, minimal JS)
2. Avoid large utility libraries when native solutions exist
3. Use `static/js/` for global functionality, `mainapp/static/js/` for app-specific
4. Always run `collectstatic` after changes
5. Document purpose and usage in AGENTS.md

### Project Rules & Standards (`alwaysRead.txt`)
**CRITICAL**: This file contains the core Django development standards that MUST be followed. It contains comprehensive rules covering:

**I. Project Foundation & Structure**
- Custom User Model usage (already implemented)
- Virtual environment isolation
- Dependency version pinning
- Modular application structure
- Thin views, fat models
- Separate settings files (base.py, development.py, production.py)

**II. Security & Environment**
- Environment variables (use `.env` files, never commit secrets)
- SECRET_KEY management
- DEBUG mode control
- ALLOWED_HOSTS configuration
- HTTPS enforcement in production
- Content Security Policy (CSP) headers
- Admin URL renaming

**III. Database & ORM Performance**
- Use `select_related()` for ForeignKey relationships
- Use `prefetch_related()` for ManyToMany relationships
- Add `db_index=True` to frequently queried fields
- Use `transaction.atomic()` for multi-write operations
- Use `bulk_create()` and `bulk_update()` for lists
- Avoid GenericForeignKey
- Enable persistent connections (`CONN_MAX_AGE`)

**IV. Code Quality & Maintainability**
- Use Python type hints (PEP 484)
- Enforce PEP 8 with black, isort, flake8
- Fat models, skinny views
- Prefer Class-Based Views for CRUD, FBVs for complex logic
- Use reverse URL lookups, never hardcode URLs

**V. Static & Media Files**
- Use WhiteNoise for static files in production
- Store media on cloud storage (not local filesystem)
- Use ManifestStaticFilesStorage for cache busting

**VI. Testing & CI/CD**
- Write unit tests for models, views, forms
- Use factory_boy for test data generation
- Run tests and linters in CI pipeline

**VII. Production Deployment Architecture**
- Use Gunicorn (WSGI) or Uvicorn (ASGI), never runserver
- Use reverse proxy (Nginx/Apache)
- Configure logging to monitoring service
- Implement `/health/` endpoint

**VIII. Specific Django Pitfalls**
- Store datetimes in UTC (USE_TZ = True)
- Never alter migration files manually
- Use native JSONField for unstructured data (not as relational substitute)

**Agents MUST read and follow all rules in `alwaysRead.txt` before making any changes!**

## Project Architecture

### Application Structure
- **Frontend apps**: `mainapp` (core business logic), `users` (authentication)
- **Settings**: Split across `base.py`, `development.py`, and `production.py`
- **Custom user model**: `users.User` (extends `AbstractUser`)
- **Deployment**: Railway with PostgreSQL, gunicorn, and persistent media storage

### Django REST Framework (DRF)
- DRF is used for API endpoints with ViewSets in `mainapp.viewsets`
- API routes organized in `mainapp.api_v1_urls`
- DRF Spectacular for API documentation
- Serializers in `mainapp.serializers`

## Model Conventions

### Database Models
- All foreign keys MUST include `related_name` parameter
- Use `db_index=True` on frequently queried fields
- Models should have `created_at` and `updated_at` timestamps (auto_now_add, auto_now)
- Include `is_active` boolean for soft deletes where applicable
- Use `verbose_name` and `verbose_name_plural` for admin display
- Implement `clean()` method for custom validation
- Use `ordering` in Meta class to define default query ordering

### Example Model Pattern
```python
class ExampleModel(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    related_field = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_instances'  # REQUIRED
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Example'
        verbose_name_plural = 'Examples'

    def __str__(self):
        return self.name

    def clean(self):
        """Validate business rules."""
        super().clean()
        # Custom validation logic
```

## Views and URLs

### URL Conventions
- Use `path()` not `url()` for URL patterns
- All non-views URLs should be named (used in templates and redirects)
- Organize URLs by functionality (auth, booking, admin, etc.)
- Include HTMX-specific URLs with `htmx/` prefix for partial rendering

### View Conventions
- Use function-based views for simple operations
- Use class-based views (generics) for CRUD operations
- All views should have proper authentication decorators (`@login_required`)
- Handle both GET and POST where appropriate
- Use custom context processors for shared template data
- Modal-style views for dynamic content (HTMX interactions)

### URL Organization
```
myproject/urls.py → Main URL configuration
- Auth URLs: /login/, /customer/sign-up/, /customer/profile/
- Dog management: /customer/dogs/*/
- Appointments: /customer/appointments/*/
- Admin management: /admin/*/
- API endpoints: /api/v1/ and /api/
```

## Testing Conventions

### Test Framework
- **pytest** is the testing framework (not Django's default unittest)
- **factory-boy** for creating test data fixtures
- Test files should replicate the module structure they test (e.g., `test_services.py` alongside `services.py`)
- Test factories defined in `tests/factories.py` for each model

### Factory Bot Usage
- All models should have corresponding factories
- Use `@factory.Sequence` for unique fields
- Use `@factory.Faker` for realistic data generation
- Create specialized factories for different scenarios (e.g., `ComplexBreedFactory`)
- Factories should handle cross-app relationships (e.g., `DogFactory` requires User from users app)

### Test Organization
```python
# tests/factories.py
class MyModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MyModel
    field = factory.Sequence(lambda n: f"Value {n}")

# tests/test_services.py
class MyServiceTestCase(TestCase):
    def setUp(self):
        self.test_data = MyModelFactory()
    
    def test_service_function(self):
        result = my_service_function(self.test_data)
        self.assertEqual(result.status_code, 200)
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest mainapp/tests/test_services.py

# Run specific test class
pytest mainapp/tests/test_services.py::CreateBookingTestCase
```

## Business Logic Conventions

### Service Layer Pattern
- Complex business logic should be extracted to `services.py` module
- Services should be standalone functions, not methods on models
- Use custom exceptions derived from `ValidationError` for business rule violations
- Services should handle database transactions explicitly with `@transaction.atomic`

### Example Service Pattern
```python
# services.py
class CustomBusinessError(ValidationError):
    """Raised when business rule violation occurs."""
    pass

def my_service_function(param1, param2):
    """Perform business operation with validation and error handling."""
    with transaction.atomic():
        # Validate inputs
        try:
            result = perform_operation()
            log_completion()
            return result
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise CustomBusinessError("Operation failed")
```

## Signals and Email

### Signal Conventions
- Signals defined in `signals.py` module
- Use thread-local storage for tracking state changes between pre_save and post_save
- Email notifications triggered by post_save signals
- Always use `@receiver` decorator
- Use `django.core.mail.send_mail` for email sending
- Templates rendered with `render_to_string` for email bodies

### Thread-Local Storage Pattern
```python
from threading import local
_thread_local = local()

@receiver(pre_save, sender=MyModel)
def track_state_change(sender, instance, **kwargs):
    if instance.pk:
        old_instance = MyModel.objects.get(pk=instance.pk)
        _thread_local.old_state = old_instance.state
    else:
        _thread_local.old_state = None

@receiver(post_save, sender=MyModel)
def react_to_state_change(sender, instance, created, **kwargs):
    old_state = getattr(_thread_local, 'old_state', None)
    if old_state != instance.state:
        send_notification(instance)
```

## Security and Authentication

### Custom User Model
- Uses `users.User` extending `AbstractUser`
- Custom `user_type` field (admin, groomer, customer)
- Phone field with regex validation
- Set `AUTH_USER_MODEL = 'users.User'` in settings

### Security Middleware
- Custom middleware in `mainapp.middleware`
- Security headers middleware
- Exception handling middleware
- Query logging middleware
- Action logging middleware
- CSP (Content Security Policy) configured with django-csp

### CSRF and XSS Protection
- All views must be CSRF-protected
- Use `django.middleware.csrf.CsrfViewMiddleware`
- Use `django.middleware.clickjacking.XFrameOptionsMiddleware`
- Templates should escape all variable output (Django default)
- HTMX interactions should properly handle CSRF tokens

## Deployment Conventions

### Railway Deployment
- PostgreSQL database auto-provided as `DATABASE_URL`
- Persistent media storage at `/data/media`
- Use `wait_for_db.py` script before starting gunicorn
- Health check endpoint at `/health/`
- Use `start.sh` script for production startup
- Gunicorn with 2 workers, 300s timeout

### Startup Sequence (Railway)
```
1. wait_for_db.py → Wait for PostgreSQL connection
2. python manage.py migrate --noinput
3. python manage.py create_superuser_if_not_exists (if environment variables set)
4. python manage.py collectstatic --noinput
5. start_gunicorn → gunicorn with production settings
```

**Special Superuser Creation:**
- Superuser can be created via environment variables (`SUPERUSER_USERNAME`, `SUPERUSER_EMAIL`, `SUPERUSER_PASSWORD`)
- Custom admin reset command available: `python manage.py reset_admin` (resets BrittTheBoss password)

### Breeds Data Loading
The application relies on breed data for pricing calculations. Use the `populate_breeds` management command:
```bash
python manage.py populate_breeds
```
This populates the database with common US dog breeds organized by size categories (Small, Medium, Large, Giant) with appropriate base prices for the Eastern US market. Run this after migrations in new deployments.

### Environment Variables
```
DATABASE_URL (auto-set by Railway)
SECRET_KEY (required, in production)
DEBUG=False (production)
ALLOWED_HOSTS=<railway-domain>.railway.app
DJANGO_SETTINGS_MODULE=myproject.settings.production
PORT (set by Railway, default 8080)
```

## Frontend Conventions

### HTML Templates
- HTMX for dynamic partial page updates
- Tailwind CSS for styling (use CDN in both development and production)
- Templates in `templates/` directory following app structure
- Custom context processors in `mainapp.context_processors`

### HTMX Patterns
- Use `hx-get`, `hx-post`, `hx-put`, `hx-delete` for interactions
- Use `hx-target` to specify update target
- Use `hx-swap` to control insertion method
- Return HTML fragments for partial updates
- Modal-like interactions for forms and confirmations

### Static Files
- Compiled with `collectstatic` command
- Serve with WhiteNoise in production
- Separate `static/` (source) from `staticfiles/` (compiled) directories

### JavaScript Structure

**Global Static Files (`static/js/`):**
- `modal.js` - Global Modal System (10KB)
  - Functions: `showNotification()`, `openModal()`, `closeModal()`, `closeModalOverlay()`
  - Handles modal opening/closing, toast notifications
  - Manages static modal content (about, contact)
  - CSRF token handling
  - Event delegation for modal buttons
  - Loaded via `{% static 'js/modal.js' %}` in `base.html`

- `schedule-modal.js` - Schedule Modal Application (16.3 KB after simplification)
  - Handles time slot management (add/delete/save)
  - Processes groomer selection and availability
  - Used in scheduling-related modals
  - Loaded inline in specific templates
  - **Recent simplifications (Feb 2026):**
    - Removed custom confirm dialog (~65 lines) - replaced with native confirm()
    - Simplified date parsing (removed multi-strategy approach)
    - Consolidated showMessage() function
    - Reduced file size from 21.7KB to 16.3KB (~25% reduction)

**App-Specific Static Files (`mainapp/static/js/`):**
- `weight-pricing-modal.js` - Weight-Based Pricing Modal (9KB)
  - Used in pricing management
  - Loaded via `{% static 'js/weight-pricing-modal.js' %}` in weight_pricing_modal.html

**Deleted/Removed Files:**
- `comprehensive-logger.js` - Removed (overkill for production, 21KB)
- `modal-utils.js` - Removed (consolidated into modal.js)
- `services-modal-state.js` - Removed (unused)
- `mainapp/static/js/services-modal-state.js` - Removed (unused)
- `mainapp/static/js/schedule-modal.js` - Removed (duplicate, kept the version in static/js/)

### CSS Files
- `tailwind.css` - Removed (using Tailwind CDN instead)
- All styling via Tailwind CDN for performance and simplicity

### Partial Templates (`mainapp/templates/mainapp/partials/`)
**Active Partials:**
- `action_card_partial.html` - Admin action cards (used in admin_landing.html)
- `customer_nav.html` - Customer navigation (used in customer_profile.html)
- `groomer_card.html` - Groomer display cards (used in services_list_modal.html)
- `groomer_options.html` - Groomer selection options (used in admin templates)
- `modal_header.html` - Modal header component (used in admin templates)

**Deleted Particles (not referenced anywhere):**
- `loading_spinner.html` - Removed
- `empty_state.html` - Removed
- `tabs.html` - Removed
- `time_slots_list.html` - Removed
- `booking_form_inner.html` - Removed

**Adding New JavaScript Files:**
1. Create the JS file in `static/js/`
2. Load it with `{% load static %} <script src="{% static 'js/yourfile.js' %}"></script>`
3. Run `python manage.py collectstatic` to compile for production
4. Test locally before committing

**Modifying Existing JavaScript:**
- Edit files in `static/js/` (not `staticfiles/`)
- Run `collectstatic` after changes to update production files
- Follow existing patterns (IIFE wrapping, error handling)

## Code Quality

### Linting and Formatting
- Use **black** for code formatting: `black .`
- Use **isort** for import sorting: `isort .`
- Use **flake8** for linting: `flake8 .`
- All three should pass before committing

### Python Version
- Python 3.13.12
- Django 4.2.16

### Required Packages (requirements.txt)
```
Django==4.2.16
djangorestframework==3.15.2
drf-spectacular==0.27.2 (API docs)
factory-boy==3.3.3 (testing)
pytest (dev dependencies)
```

## Database Migration Conventions

### Migration Workflow
1. Create migration: `python manage.py makemigrations`
2. Review migration files before applying
3. Apply migration: `python manage.py migrate`
4. Test migration in development environment thoroughly
5. Consider data migration scripts for breaking changes

### Migration Safety
- Always test migrations on copy of production data
- Use `RunPython` for complex data migrations
- Include data validation in migration scripts
- Consider backwards compatibility for rollback scenarios
- Document breaking migrations in migration comments

## Admin Conventions

### Django Admin
- Register all models in `admin.py`
- Custom admin classes for complex models
- Use `list_display`, `list_filter`, `search_fields` for usability
- Use `readonly_fields` for computed fields
- Custom admin actions for bulk operations
- Organize admin with ModelAdmin and InlineModelAdmin

### Admin URLs
- All admin URLs under `/admin/`
- Custom admin views in `mainapp/views/admin_views.py`
- Admin landing page at `/admin-landing/`

## Development Workflow

### Git Workflow
- Main development branch: `master`
- Work on feature branches then merge to master
- Use descriptive commit messages following conventional commits
- Test changes with pytest before committing
- Run linting (black, isort, flake8) before pushing

### Quick Reference Commands
```bash
# Development
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

# Testing
pytest
pytest --cov
pytest mainapp/tests/test_services.py -v

# Code Quality
black .
isort .
flake8 .

# Production Deployment (Railway)
# Automatic via start.sh and wait_for_db.py
```

## Constants and Error Messages

### Constants Module
- Keep magic numbers and strings in `mainapp/constants.py`
- Define error messages as constants
- Use descriptive names for constants

### Error Handling
- Use custom exceptions for business logic errors
- Log errors appropriately with `logging` module
- Provide user-friendly error messages
- Handle ValidationError from forms/views gracefully

## Diagnostic & Analysis Command Reference

### Database & User Management
```bash
# Analyze database state and detect orphaned users
python analyze_db_state.py

# Fix orphaned customer users automatically
python fix_orphaned_users.py

# Delete orphaned users immediately (use with caution)
python delete_orphaned_users_now.py

# Create superuser from environment variables
python create_superuser.py

# Manage superuser accounts
python manage_superusers.py
```

### Authentication & Admin Debugging
```bash
# Comprehensive auth system diagnostics
python diagnostic_auth_system.py

# Debug admin authentication specifically
python debug_admin_auth.py

# Test admin login functionality
python test_admin_login.py

# Test authentication debugging
python test_auth_debug.py
```

### Code Analysis
```bash
# Analyze codebase size and optimization opportunities
python analyze_code_size.py
```

### Standard Django Management Commands
```bash
# Development
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

# Custom Management Commands
python manage.py populate_breeds  # Populate common US dog breeds with base prices
python manage.py reset_admin  # Reset admin password for BrittTheBoss
python manage.py auto_document_project  # Auto-generate project documentation

# Testing
pytest
pytest --cov
pytest mainapp/tests/test_services.py -v

# Code Quality
black .
isort .
flake8 .
```

### Production Deployment (Railway)
```bash
# Manual testing of deployment scripts (typically automatic)
python wait_for_db.py
bash start.sh
```

## Important Files to Reference

- **Project Standards**: `alwaysRead.txt` (CRITICAL - Django best practices and rules)
- **Settings**: `myproject/settings/base.py`, `myproject/settings/production.py`
- **URLs**: `myproject/urls.py`, `mainapp/api_v1_urls.py`
- **Models**: `mainapp/models.py`, `users/models.py`
- **Views**: `mainapp/views/`, `mainapp/viewsets.py`
- **Services**: `mainapp/services.py`, `mainapp/signals.py`
- **Tests**: `mainapp/tests/factories.py`, `mainapp/test_*.py`
- **Middleware**: `mainapp/middleware.py`
- **Management Commands**: `mainapp/management/commands/`
- **Deployment**: `wait_for_db.py`, `start.sh`, `railway.toml`, `Procfile`
- **Diagnostics**: `analyze_db_state.py`, `diagnostic_auth_system.py`, `fix_orphaned_users.py`, `create_superuser.py`
- **Analysis**: `analyze_code_size.py`
- **Environment**: `.env`, `.env.template`

## When Working on This Project

1. **Read AGENTS.md AND alwaysRead.txt first** to understand conventions and Django best practices
2. **Follow existing patterns** - look at similar code for guidance
3. **Check for orphaned users** with `analyze_db_state.py` after user-related changes
4. **Add tests** for all new functionality using factory-boy factories
5. **Run linting** (black, isort, flake8) before committing
6. **Consider migrations** carefully - they affect production
7. **Test locally** with pytest before deploying
8. **Document breaking changes** in appropriate places
9. **Use proper error handling** with custom exceptions and logging
10. **Follow security best practices** (CSRF, XSS, input validation)
11. **Use diagnostic scripts** when debugging authentication or database issues
12. **Maintain consistency** - keep the codebase coherent
13. **Check User-Customer relationship integrity** after user management operations

## Special Considerations

### Customer-User Relationship (Known Issue)
- Custom User model in users app with `user_type` field (admin, groomer, customer)
- Customer model in mainapp has OneToOne relationship with User
- **CRITICAL ISSUE**: Signals (`mainapp/signals.py`) should auto-create Customer profiles when Users are created, but this sometimes fails
- **Use `analyze_db_state.py`** regularly to detect orphaned users (customer-type Users without Customer profiles)
- When creating Users manually, ensure Customer profile is created or signals are properly connected
- Always check User-Customer relationship consistency after user management operations

**Example of the issue:**
```python
# Problem: User created but Customer profile missing
orphaned_users = User.objects.filter(user_type='customer').exclude(customer_profile__isnull=False)

# Solution: Fix with proper signal handling or manual Customer creation
```

**Debugging User Issues:**
1. Run `python analyze_db_state.py` to identify orphaned users
2. Check signal connections in `mainapp/signals.py`
3. Verify User creation flows (sign-up, admin creation) properly trigger Customer creation
4. Use `diagnostic_auth_system.py` for comprehensive auth system diagnostics

### Pricing Complexity
- Some breeds have `breed_pricing_complex=True`
- Weight-based pricing for many breeds
- Cloned pricing from parent breeds
- Be careful when modifying pricing logic

### Appointment Booking
- Status workflow: pending → confirmed → completed/cancelled
- Email notifications on status changes
- Time slot availability checks
- Conflict detection required
