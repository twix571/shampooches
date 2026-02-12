"""
Constants module for the grooming salon application.

This module centralizes all magic numbers, status codes, and configuration constants
to improve maintainability and avoid hardcoding values throughout the codebase.
"""

from decimal import Decimal

# ============================================================================
# APPOINTMENT STATUS CONSTANTS
# ============================================================================

class AppointmentStatus:
    """Constants for appointment status values."""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    # Valid status choices
    VALID_STATUSES = [PENDING, CONFIRMED, COMPLETED, CANCELLED]

    # Active statuses for booking conflicts
    ACTIVE_STATUSES = [PENDING, CONFIRMED]

    # Status display mapping
    DISPLAY_MAPPING = {
        PENDING: 'Pending',
        CONFIRMED: 'Confirmed',
        COMPLETED: 'Completed',
        CANCELLED: 'Cancelled',
    }

    @classmethod
    def is_valid(cls, status):
        """Check if a status value is valid."""
        return status in cls.VALID_STATUSES

    @classmethod
    def is_active(cls, status):
        """Check if a status represents an active appointment."""
        return status in cls.ACTIVE_STATUSES


# ============================================================================
# USER TYPE CONSTANTS
# ============================================================================

class UserType:
    """Constants for user profile types."""
    ADMIN = 'admin'
    GROOMER = 'groomer'
    CUSTOMER = 'customer'

    # Valid user types
    VALID_TYPES = [ADMIN, GROOMER, CUSTOMER]

    # Types that can access admin features
    ADMIN_ACCESS_TYPES = [ADMIN, GROOMER]

    @classmethod
    def is_valid(cls, user_type):
        """Check if a user type is valid."""
        return user_type in cls.VALID_TYPES

    @classmethod
    def has_admin_access(cls, user_type):
        """Check if user type has admin access."""
        return user_type in cls.ADMIN_ACCESS_TYPES


# ============================================================================
# HTTP STATUS CODE CONSTANTS
# ============================================================================

class HTTPStatus:
    """Constants for HTTP status codes."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ============================================================================
# TIME AND SCHEDULING CONSTANTS
# ============================================================================

class Scheduling:
    """Constants for scheduling and time-related operations."""
    # Number of days to display in booking calendar
    BOOKING_DAYS_AHEAD = 14

    # Number of days in a work week
    WORK_WEEK_DAYS = 5

    # Days of the week names
    WEEKDAY_NAMES = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
    ]

    # Maximum appointment duration in minutes (for scheduling conflicts)
    MAX_APPOINTMENT_DURATION_MINUTES = 180

    # Minimum time between appointments in minutes
    MIN_APPOINTMENT_GAP_MINUTES = 15


# ============================================================================
# PRICING CONSTANTS
# ============================================================================

class Pricing:
    """Constants for pricing calculations."""
    # Default price for new services if not specified
    DEFAULT_SERVICE_PRICE = '0.00'

    # Default duration for new services in minutes
    DEFAULT_SERVICE_DURATION_MINUTES = 60

    # Maximum decimal places for prices
    PRICE_DECIMAL_PLACES = 2

    # Maximum digits for prices
    PRICE_MAX_DIGITS = 10

    # Minimum allowed price
    MIN_PRICE = Decimal('0.00')

    # Maximum weight value in lbs
    MAX_WEIGHT_LBS = Decimal('999.99')

    # Maximum weight field digits
    WEIGHT_MAX_DIGITS = 6

    # Weight decimal places
    WEIGHT_DECIMAL_PLACES = 2


# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

class Validation:
    """Constants for validation rules."""
    # Maximum length for text fields
    MAX_TEXT_LENGTH = 255

    # Maximum length for description fields
    MAX_DESCRIPTION_LENGTH = 2000

    # Maximum length for notes fields
    MAX_NOTES_LENGTH = 1000

    # Phone number regex pattern
    PHONE_REGEX_PATTERN = r'^\+?1?\d{9,15}$'

    # Phone number format description
    PHONE_FORMAT_DESC = 'Phone number must be entered in the format: +1234567890 or 1234567890'

    # Email regex pattern
    EMAIL_REGEX_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Minimum dog age in years
    MIN_DOG_AGE_YEARS = 0

    # Maximum dog age in years
    MAX_DOG_AGE_YEARS = 30

    # Dog names should contain only letters, spaces, and hyphens
    DOG_NAME_REGEX_PATTERN = r'^[a-zA-Z\s\-]+$'

    # Minimum length for names
    MIN_NAME_LENGTH = 2

    # Maximum length for names
    MAX_NAME_LENGTH = 100


# ============================================================================
# DATABASE QUERY CONSTANTS
# ============================================================================

class DatabaseQuery:
    """Constants for database query optimizations."""
    # Batch size for bulk operations
    BATCH_SIZE = 500

    # Maximum number of records to fetch in a single query
    MAX_QUERY_SIZE = 1000

    # Cache timeout for frequently accessed data (in seconds)
    CACHE_TIMEOUT_SECONDS = 300


# ============================================================================
# ERROR MESSAGE TEMPLATES
# ============================================================================

class ErrorMessages:
    """Templates for common error messages."""
    # Validation errors
    REQUIRED_FIELD = '{field} is required'
    INVALID_FORMAT = 'Invalid {field} format: {value}'
    OUT_OF_RANGE = '{field} must be between {min} and {max}'

    # Business logic errors
    PAST_BOOKING = 'Bookings must be made for a future date. Attempted to book for {date}, which is in the past.'
    INACTIVE_SERVICE = 'The service "{service}" is not currently available for booking.'
    INACTIVE_GROOMER = 'The groomer "{groomer}" is not currently available for bookings.'
    BOOKING_CONFLICT = 'There is already an appointment booked for {groomer} on {date} at {time}.'

    # Object not found errors
    OBJECT_NOT_FOUND = '{model} not found'
    BREED_NOT_FOUND = 'Breed "{name}" not found'
    SERVICE_NOT_FOUND = 'Service "{name}" not found'
    GROOMER_NOT_FOUND = 'Groomer "{name}" not found'
    CUSTOMER_NOT_FOUND = 'Customer with email "{email}" not found'
    APPOINTMENT_NOT_FOUND = 'Appointment #{id} not found'

    # Permission errors
    UNAUTHORIZED_ACCESS = 'Authentication required'
    INSUFFICIENT_PERMISSIONS = 'You do not have permission to access this page'
    ADMIN_REQUIRED = 'Admin access required'

    # General errors
    UNKNOWN_ERROR = 'An unexpected error occurred'
    OPERATION_FAILED = 'Operation failed: {error}'


# ============================================================================
# SUCCESS MESSAGE TEMPLATES
# ============================================================================

class SuccessMessages:
    """Templates for common success messages."""
    CREATED = '{model} created successfully'
    UPDATED = '{model} updated successfully'
    DELETED = '{model} deleted successfully'
    BOOKING_CREATED = 'Appointment booked successfully!'

    # Pricing messages
    PRICING_CLONED = 'Pricing cloned from {source} to {target} successfully ({count} items)'
    PRICING_IMPORTED = 'Import completed successfully'
    PRICING_EXPORTED = 'Pricing configuration exported successfully'
    WEIGHT_RANGES_APPLIED = 'Weight ranges applied to {count} breeds successfully'

    # Time slot messages
    TIME_SLOTS_CREATED = 'Created {count} time slots'
    TIME_SLOTS_DELETED = 'Deleted {count} time slot(s)'
    TIME_SLOTS_SET = 'Set {count} time slots for {date}'


# ============================================================================
# EXPORT ALL PUBLIC MODULES
# ============================================================================

__all__ = [
    'AppointmentStatus',
    'UserType',
    'HTTPStatus',
    'Scheduling',
    'Pricing',
    'Validation',
    'DatabaseQuery',
    'ErrorMessages',
    'SuccessMessages',
    'Decimal',
]
