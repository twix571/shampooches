# PROJECT BRAIN
> **SYSTEM INSTRUCTION FOR AI:**
> This file is your PRIMARY context. You must read this before answering user requests.
>
> **YOUR MANDATE:**
> 1. **Adopt Context**: Use the `@META` and `@RULES` below to format your code without asking questions.
> 2. **Enforce Style**: Reject any user request that violates the `@RULES` unless explicitly overridden.
> 3. **Auto-Update**: At the end of your session, if you have added features, fixed bugs, or found new constraints, you MUST update this file.
>    - *Remove* completed tasks from `@STATE`.
>    - *Add* new tech to `@META` or `@ARCH`.
>    - *Log* unresolved conflicts to `Known_Issues`.
> 4. **Prune**: Keep this file under 200 lines. Delete obsolete info.

---

## @META
- **Stack**: Django 5.0.2, Python 3.13.9, Django REST Framework 3.15.2, Tailwind CSS (django-tailwind-cli), HTMX for reactive interactions, SQLite (dev), PostgreSQL (production on Railway), python-dotenv 1.1.1, Pillow 10.2.0, gunicorn 21.2.0, django-cleanup 8.1.0, django-browser-reload 1.21.0, drf-spectacular 0.27.2, django-storages 1.14.4, dj-database-url 2.3.0
- **DevTools**: flake8, black, isort, coverage
- **Features**: API v1 with pagination & rate limiting, standardized responses, query optimization, security middleware, input sanitization, caching utilities
- **Env**: Python 3.13.9, venv or .venv, run.bat for dev server
- **Entry**: manage.py, myproject/settings.py, mainapp/api_helpers.py, mainapp/cache_utils.py
- **Commands**: run.bat, python3 manage.py migrate, python3 manage.py makemigrations, python3 manage.py test
- **Deployment**: Railway (PostgreSQL, Volumes for persistent media)

## @ARCH
- **Pattern**: MVT (Model-View-Template), DRF APIView classes for API endpoints, Service layer in utils.py
- **State**: Django session-based auth, custom UserProfile model with admin/groomer/customer roles
- **Auth**: UserProfileBackend, admin_required decorator for protected views
- **Data**: SQLite (dev), PostgreSQL (production via Railway DATABASE_URL), Django ORM with UserProfile, Breed, Service, Customer, Appointment, Groomer, TimeSlot, BreedServiceMapping, SiteConfig, Dog
- **Storage**: MEDIA_ROOT = media/ (dev), /data/media (Railway Volumes - production)
- **API**: REST via DRF ViewSets & APIViews (25 endpoints), /api/v1/ standardized routing with serializers
- **Pricing**: Server-side rendered admin page at /admin/pricing/ for breed pricing management
- **Deployment**: Railway (PostgreSQL automatic via DATABASE_URL, Volumes at /data for persistent media storage)

## @RULES
- **Strict**: PEP 8, snake_case vars/functions, CamelCase classes, 4-space indent, absolute imports, FBV preferred, render() shortcut, URL name= parameters, templates extend base.html
- **Workflow**: PRE-FLIGHT CHECK REQUIRED. 1) Run existing tests. 2) If no test exists for target feature, CREATE ONE. 3) Apply changes. 4) Run tests again to ensure zero regressions.
- **Style**: Tailwind CSS utility-first, mobile-first responsive, {% tailwind_css %} tag, templates in mainapp/templates/mainapp/
- **Forbidden**: Class-Based Views (CBVs) unless needed, hardcoded URLs, DEBUG=True in production, commit secrets, db.sqlite3, __pycache__, .env, media files

## @MAP
myproject/ (Django config, settings.py, urls.py, settings/production.py, custom auth backend)
mainapp/ (main app with models, views, serializers, admin, services, apiviews, viewsets)
mainapp/templates/mainapp/ (HTML templates: base.html, customer_landing.html, admin_landing.html, groomer_landing.html, booking_modal.html, schedule_modal.html, login.html, pricing/ directory)
  pricing/ (pricing templates: pricing_management.html, breed_cloning_wizard_modal.html, pricing_preview_modal.html, weight_pricing_modal.html, weight_range_templates_modal.html)
static/ (CSS: tailwind.css, js/modal-utils.js)
media/ (user uploads: groomer_images/) - dev only
manage.py (Django CLI entry point)
railway.toml (Railway deployment configuration)
RAILWAY_DEPLOYMENT.md (Deployment guide and troubleshooting)

## @STATE
- **Status**: Production-ready with Railway deployment. Configured for PostgreSQL database via DATABASE_URL and persistent media storage via Railway Volumes (/data). Local development can use SQLite or PostgreSQL.
- **Active_Features**: Customer booking flow, admin dashboard, groomer portal, breed pricing management (server-side rendered at /admin/pricing/), weight range templates, time slot editor, export/import pricing config, breed cloning wizard, public API read access for groomers/services/breeds, global modal close function, dynamic site configuration for business hours and contact info.
- **Production_Ready**:
  - Database: PostgreSQL via Railway (DATABASE_URL auto-provided)
  - Media Storage: Railway Volumes at /data for persistent groomer images
  - Static Files: WhiteNoise for production static file serving
  - Security: Production security headers, SSL enforcement, CSP
  - Deployment: Full Railway configuration (railway.toml, deployment guide)
- **Known_Issues**: Fixed booking modal API response format issues (JSON data wrapped in StandardResponse structure), added missing get_object_or_404 import in utils.py for time slots endpoint, fixed step 6 validation to update state before checking contact information fields, added customer contact information to step 7 confirmation screen. Fixed customer landing page issues: removed hardcoded service prices, hardcoded business hours, hardcoded URL patterns, confusing navigation auto-hide, added accessibility features (skip-to-content link, aria-labels, keyboard navigation). Test suite: 32 tests passing (1 unrelated pre-existing failure for admin panel URL). API v1 endpoints available with improved code quality.
- **History**: Django 5.0.2 with DRF, custom UserProfile auth system, breed-specific pricing with weight surcharges, Railway deployment configured, dynamic site configuration model added for business hours/contact info management.

## @CODE_QUALITY_IMPROVEMENTS
### Completed Improvements ✓
- **Architecture Simplification**: Replaced complex modal/pricing management with server-side rendered page at /admin/pricing/, eliminating race conditions and timing issues
- **Frontend Migration**: Migrated from Alpine.js to HTMX and vanilla JavaScript for reactive interactions
- **API Standardization**: Migrated 25 ad-hoc endpoints to DRF APIView classes with proper serializers, centralized v1 routing
- **API Versioning**: Added `/api/v1/` endpoints with backward-compatible legacy API support
- **Pagination**: Implemented StandardPagination across all ViewSets (10 per page, configurable)
- **Rate Limiting**: Added DRF throttling (100/day for anon, 500/day for authenticated users)
- **Response Standardization**: Created StandardResponse class with consistent success/error format
- **Query Optimization**: Added select_related/prefetch_related to all ViewSets for N+1 prevention
- **Exception Handling**: Created ExceptionHandlingMiddleware for consistent error responses
- **Security Headers**: Added SecurityHeadersMiddleware (X-Frame-Options, CSP, HSTS)
- **Query Logging**: Added QueryLoggingMiddleware for performance monitoring in DEBUG mode
- **Caching**: Implemented QueryCache class for frequently accessed models with cache invalidation
- **Cache Deprecation Fix**: Fixed deprecated `get_cache` usage in cache_utils.py, updated to modern Django cache API
- **Enhanced Documentation**: Improved docstrings in utils.py with comprehensive examples and detailed parameter descriptions
- **Type Improvements**: Added complete type hints and better documentation for utility functions

### Production Readiness Improvements ✓
- **Cloud Media Storage**: Added django-storages support and configured Railway Volumes (/data) for persistent groomer image storage
- **Database Synchronization**: Configured PostgreSQL support via DATABASE_URL with dj-database-url. Railway auto-provides DATABASE_URL in production. Local dev can use SQLite or PostgreSQL.
- **Deployment Configuration**: Created railway.toml and RAILWAY_DEPLOYMENT.md with complete deployment guide
- **Media Storage**: Production MEDIA_ROOT configured to /data/media (Railway Volumes), dev uses local media/
- **Environment Configuration**: Updated .env and .env.template with DATABASE_URL setup instructions
- **Landing Page Improvements**: Fixed customer landing page with dynamic configuration - removed hardcoded prices, business hours, URLs; added SiteConfig model for business hours/contact info; improved mobile navigation UX with proper hamburger menu; added accessibility features (skip-to-content link, aria-labels, keyboard navigation, ARIA landmarks)

### Remaining Enhancements (Optional)
- **Documentation**: Add OpenAPI/Swagger using drf-spectacular (package added)
- **Soft Delete**: Implement soft delete with is_active field
- **Permissions**: Object-level permissions using Django Guardian
- **Background Tasks**: Celery for heavy operations (import/export, bulk updates)
- **Test Coverage**: Increase to 80%+ using coverage.py
