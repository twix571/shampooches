# PROJECT DOCUMENTATION
> Generated: 2026-02-13 00:08:21
> This document contains comprehensive project knowledge for AI systems and developers.

**SYSTEM INSTRUCTION:**
This file is your PRIMARY context. Read this before answering user requests.

---

## @META

**Tech Stack:**
Django 5.2.10
Python 3.13.7
- djangorestframework
- django-tailwind-cli
- gunicorn
- psycopg2-binary
- whitenoise
- django-storages
- drf-spectacular

**Entry Points:**
- `manage.py` - Django CLI entry point
- `mainapp/models.py` - Data model definitions
- `mainapp/services.py` - Business logic services
- `mainapp/api_helpers.py` - API utility functions
- `mainapp/cache_utils.py` - Caching utilities

---

## @ARCH

**Django Apps:**
- `users` - users
- `mainapp` - mainapp

**Authentication System:**
- Custom User Model: `users.User`
- Custom authentication backend: `UserProfileBackend`

---

## DATA MODELS & RELATIONSHIPS

### `users` Models

#### `User`

Many-to-Many:
- `groups` ↔ `Group`
- `user_permissions` ↔ `Permission`

One-to-One:
- `customer_profile` → `Customer` (Unknown)

Validation Rules:
- Custom validator: MaxLengthValidator
- Custom validator: UnicodeUsernameValidator
- Custom validator: MaxLengthValidator
- Custom validator: MaxLengthValidator
- Custom validator: MaxLengthValidator
- Custom validator: EmailValidator
- Custom validator: MaxLengthValidator
- Custom validator: MaxLengthValidator
- Pattern validation for phone
- Custom validator: MaxLengthValidator

---

### `mainapp` Models

#### `Breed`

Foreign Keys:
- `pricing_cloned_from` → `Breed` (SET_NULL)

Validation Rules:
- Custom validation logic defined in clean() method
- Custom validator: MaxLengthValidator
- Custom validator: DecimalValidator
- Custom validator: DecimalValidator
- Custom validator: DecimalValidator
- Custom validator: DecimalValidator
- Custom validator: DecimalValidator
- Custom validator: DecimalValidator

---

#### `BreedServiceMapping`

Foreign Keys:
- `breed` → `Breed` (CASCADE)
- `service` → `Service` (CASCADE)

Validation Rules:
- Custom validator: DecimalValidator

---

#### `Service`

Validation Rules:
- Custom validator: MaxLengthValidator
- Custom validator: DecimalValidator
- Custom validator: MaxLengthValidator

---

#### `Customer`

One-to-One:
- `user` → `User` (SET_NULL)

Validation Rules:
- Custom validator: MaxLengthValidator
- Custom validator: EmailValidator
- Custom validator: MaxLengthValidator
- Pattern validation for phone
- Custom validator: MaxLengthValidator

---

#### `Appointment`

Foreign Keys:
- `customer` → `Customer` (CASCADE)
- `user` → `User` (SET_NULL)
- `service` → `Service` (PROTECT)
- `groomer` → `Groomer` (SET_NULL)
- `preferred_groomer` → `Groomer` (SET_NULL)
- `dog_breed` → `Breed` (SET_NULL)

Validation Rules:
- Custom validator: MaxLengthValidator
- Custom validator: MaxLengthValidator
- Custom validator: DecimalValidator
- Custom validator: MaxLengthValidator
- Custom validator: MaxLengthValidator
- Custom validator: DecimalValidator

---

#### `Groomer`

Validation Rules:
- Custom validation logic defined in clean() method
- Custom validator: MaxLengthValidator
- Custom validator: MaxLengthValidator

---

#### `TimeSlot`

Foreign Keys:
- `groomer` → `Groomer` (CASCADE)

Validation Rules:
- Custom validation logic defined in clean() method

---

#### `Dog`

Foreign Keys:
- `owner` → `User` (CASCADE)
- `breed` → `Breed` (SET_NULL)

Validation Rules:
- Custom validator: MaxLengthValidator
- Custom validator: DecimalValidator
- Custom validator: MaxLengthValidator

---

#### `DogDeletionRequest`

Foreign Keys:
- `dog` → `Dog` (CASCADE)
- `requested_by` → `User` (CASCADE)

Validation Rules:
- Custom validator: MaxLengthValidator

---

#### `SiteConfig`

Validation Rules:
- Custom validation logic defined in clean() method
- Custom validator: MaxLengthValidator
- Pattern validation for phone
- Custom validator: MaxLengthValidator
- Custom validator: EmailValidator
- Custom validator: MaxLengthValidator

---

---

## URL ROUTES & VIEWS MAPPING

### Public URLS
- `/health/\Z` → `health_check`
- `/\Z` → `customer_landing`
- `/admin\-landing/\Z` → `wrapper`
- `/book\-appointment/\Z` → `book_appointment`
- `/services/\Z` → `services_list`
- `/appointments/\Z` → `wrapper`
- `/static/(?P<path>.*)` → `serve`
- `/media/(?P<path>.*)` → `serve`

### Authenticated URLs
- `/login/\Z` → `custom_login`
- `/customer/sign\-up/\Z` → `customer_sign_up`
- `/customer/profile/\Z` → `customer_profile`
- `/customer/dogs/add/\Z` → `add_dog`
- `/customer/dogs/edit/(?P<dog_id>[0-9]+)/\Z` → `edit_dog`
- `/customer/dogs/delete/(?P<dog_id>[0-9]+)/\Z` → `delete_dog`
- `/customer/dogs/add\-modal/\Z` → `add_dog_modal`
- `/customer/dogs/edit\-modal/(?P<dog_id>[0-9]+)/\Z` → `edit_dog_modal`
- `/customer/dogs/request\-deletion\-modal/(?P<dog_id>[0-9]+)/\Z` → `request_dog_deletion_modal`
- `/customer/dogs/request\-deletion/(?P<dog_id>[0-9]+)/\Z` → `request_dog_deletion`

### API Endpoints
- `/api/v1/services/` → `ServiceViewSet`
- `/api/v1/services\.(?P<format>[a-z0-9]+)/?` → `ServiceViewSet`
- `/api/v1/services/exempt-update/` → `ServiceViewSet`
- `/api/v1/services/exempt-update\.(?P<format>[a-z0-9]+)/?` → `ServiceViewSet`
- `/api/v1/services/(?P<pk>[^/.]+)/` → `ServiceViewSet`
- `/api/v1/services/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `ServiceViewSet`
- `/api/v1/breeds/` → `BreedViewSet`
- `/api/v1/breeds\.(?P<format>[a-z0-9]+)/?` → `BreedViewSet`
- `/api/v1/breeds/(?P<pk>[^/.]+)/` → `BreedViewSet`
- `/api/v1/breeds/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `BreedViewSet`
- `/api/v1/breeds/(?P<pk>[^/.]+)/update-base-price/` → `BreedViewSet`
- `/api/v1/breeds/(?P<pk>[^/.]+)/update-base-price\.(?P<format>[a-z0-9]+)/?` → `BreedViewSet`
- `/api/v1/groomers/` → `GroomerViewSet`
- `/api/v1/groomers\.(?P<format>[a-z0-9]+)/?` → `GroomerViewSet`
- `/api/v1/groomers/(?P<pk>[^/.]+)/` → `GroomerViewSet`
- `/api/v1/groomers/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `GroomerViewSet`
- `/api/v1/breed-service-mappings/` → `BreedServiceMappingViewSet`
- `/api/v1/breed-service-mappings\.(?P<format>[a-z0-9]+)/?` → `BreedServiceMappingViewSet`
- `/api/v1/breed-service-mappings/(?P<pk>[^/.]+)/` → `BreedServiceMappingViewSet`
- `/api/v1/breed-service-mappings/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `BreedServiceMappingViewSet`
- `/api/v1/\Z` → `APIRootView` [IsAuthenticated]
- `/api/v1/(?P<format>\.[a-z0-9]+/?)\Z` → `APIRootView` [IsAuthenticated]
- `/api/v1/booking/calculate\-price/\Z` → `BookingCalculatePriceView` [IsAuthenticated]
- `/api/v1/booking/calculate\-final\-price/\Z` → `BookingCalculateFinalPriceView` [IsAuthenticated]
- `/api/v1/booking/available\-days/\Z` → `BookingAvailableDaysView` [IsAuthenticated]
- `/api/v1/booking/time\-slots/\Z` → `BookingTimeSlotsView` [IsAuthenticated]
- `/api/v1/booking/submit/\Z` → `BookingSubmitView` [IsAuthenticated]
- `/api/v1/admin/dashboard\-stats/\Z` → `DashboardStatsView` [IsAuthenticated]
- `/api/v1/admin/appointments/update\-status/\Z` → `UpdateAppointmentStatusView` [IsAuthenticated]
- `/api/v1/admin/time\-slots/create/\Z` → `TimeSlotCreateView` [IsAuthenticated]
- `/api/v1/admin/time\-slots/manage/\Z` → `TimeSlotManageView` [IsAuthenticated]
- `/api/v1/admin/time\-slots/delete/\Z` → `TimeSlotDeleteView` [IsAuthenticated]
- `/api/v1/admin/time\-slots/delete\-date/\Z` → `TimeSlotDeleteDateView` [IsAuthenticated]
- `/api/v1/admin/time\-slots/day/\Z` → `DayTimeSlotsView` [IsAuthenticated]
- `/api/v1/admin/time\-slots/set\-day/\Z` → `SetDayTimeSlotsView` [IsAuthenticated]
- `/api/v1/admin/time\-slots/batch/\Z` → `BatchDayTimeSlotsView` [IsAuthenticated]
- `/api/v1/admin/pricing/batch\-save/\Z` → `BatchSavePricingManagementView` [IsAuthenticated]
- `/api/v1/admin/pricing/breed/clone/\Z` → `CloneBreedPricingView` [IsAuthenticated]
- `/api/v1/admin/pricing/breed/create\-with\-clone/\Z` → `CreateBreedWithCloneView` [IsAuthenticated]
- `/api/services/` → `ServiceViewSet`
- `/api/services\.(?P<format>[a-z0-9]+)/?` → `ServiceViewSet`
- `/api/services/exempt-update/` → `ServiceViewSet`
- `/api/services/exempt-update\.(?P<format>[a-z0-9]+)/?` → `ServiceViewSet`
- `/api/services/(?P<pk>[^/.]+)/` → `ServiceViewSet`
- `/api/services/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `ServiceViewSet`
- `/api/breeds/` → `BreedViewSet`
- `/api/breeds\.(?P<format>[a-z0-9]+)/?` → `BreedViewSet`
- `/api/breeds/(?P<pk>[^/.]+)/` → `BreedViewSet`
- `/api/breeds/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `BreedViewSet`
- `/api/breeds/(?P<pk>[^/.]+)/update-base-price/` → `BreedViewSet`
- `/api/breeds/(?P<pk>[^/.]+)/update-base-price\.(?P<format>[a-z0-9]+)/?` → `BreedViewSet`
- `/api/groomers/` → `GroomerViewSet`
- `/api/groomers\.(?P<format>[a-z0-9]+)/?` → `GroomerViewSet`
- `/api/groomers/(?P<pk>[^/.]+)/` → `GroomerViewSet`
- `/api/groomers/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `GroomerViewSet`
- `/api/breed-service-mappings/` → `BreedServiceMappingViewSet`
- `/api/breed-service-mappings\.(?P<format>[a-z0-9]+)/?` → `BreedServiceMappingViewSet`
- `/api/breed-service-mappings/(?P<pk>[^/.]+)/` → `BreedServiceMappingViewSet`
- `/api/breed-service-mappings/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?` → `BreedServiceMappingViewSet`
- `/api/\Z` → `APIRootView` [IsAuthenticated]
- `/api/(?P<format>\.[a-z0-9]+/?)\Z` → `APIRootView` [IsAuthenticated]

### HTMX Partial Rendering Endpoints
- `/htmx/groomer\-options/\Z` → `wrapper`
- `/htmx/time\-slots/\Z` → `wrapper`

---

## BUSINESS LOGIC & WORKFLOWS

### Booking Flow
- `create_booking()` - Core booking logic

### Business Validation Rules
- `BookingDateInPastError` - Custom validation exception
- `BookingConflictError` - Custom validation exception
- `InactiveServiceError` - Custom validation exception
- `InactiveGroomerError` - Custom validation exception
- `InvalidInputError` - Custom validation exception

### Service Layer Functions
- `create_booking` - Centralized booking creation service.

---

## USER FLOWS

### Customer Journey
Typical customer flow:
- Landing page → Service selection → Booking modal → Confirmation
- Account creation (optional)
- Dog profile management
- Appointment management

### Admin Workflows
Administrative operations:
- `customers_modal`
- `groomers_modal`
- `groomers_management_modal`
- `site_config_modal`

---

## DEPLOYMENT & ENVIRONMENT

### Required Environment Variables
Production environment must set:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `STATIC_ROOT`
- `EMAIL_BACKEND`

### Required Services
- SQLite

### Static File Management
- WhiteNoise middleware

---

## TESTING & QUALITY

Total Test Methods: 0

---

## DEVELOPMENT WORKFLOW

### Common Commands
```bash
# Start development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser

# Collect static files (production)
python manage.py collectstatic
```

---

## KNOWN ISSUES & LIMITATIONS

### Current Status
- Production deployment configured for Railway
- PostgreSQL database via DATABASE_URL
- Persistent media storage via Railway Volumes

### Known Issues
- None documented at this time

---

## PROJECT STATE & HISTORY

### Active Features
- Customer booking flow
- Admin dashboard
- Groomer portal
- Breed-specific pricing with weight surcharges
- Time slot management
- Dynamic site configuration
- REST API with pagination and rate limiting

### Implementation Notes
- Migrated from Alpine.js to HTMX for reactive frontend
- Standardized API responses with pagination
- Security middleware with headers and CSP
- Query optimization with select_related/prefetch_related
- Caching layer for frequently accessed models

---
