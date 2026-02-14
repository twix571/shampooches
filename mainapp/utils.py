"""
Utility functions for the grooming salon application.

This module consolidates common patterns and helpers used across views and viewsets,
including JSON response helpers, serializer functions, validation utilities, and
auth decorators.
"""

# Standard library imports
import json
import logging
from collections.abc import Callable
from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, TypedDict, Union

# Django imports
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect

if TYPE_CHECKING:
    from .models import (
        Appointment, Breed, Customer, Groomer, Service, TimeSlot
    )

logger = logging.getLogger(__name__)


# ============================================================================
# AUTH DECORATORS
# ============================================================================

def admin_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Decorator to ensure only admin users can access Django views.

    Redirects unauthenticated users to the login page and non-admin users
    to customer landing page.

    Args:
        view_func: The view function to wrap.

    Returns:
        Wrapped view function with admin access control.
    """
    def wrapper(request, *args, **kwargs):
        logger.info(f"admin_required check: is_authenticated={request.user.is_authenticated}, username={request.user.username if request.user.is_authenticated else 'Anonymous'}, is_staff={request.user.is_staff if request.user.is_authenticated else False}, is_superuser={request.user.is_superuser if request.user.is_authenticated else False}")

        # Check if this is an HTMX request
        is_htmx = request.headers.get('HX-Request') == 'true'

        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            logger.warning(f"Unauthenticated access attempt to {view_func.__name__}")
            if is_htmx:
                return HttpResponse('Authentication required. Please refresh.', status=401)
            return redirect_to_login(request.get_full_path())

        if not (request.user.is_superuser or request.user.is_staff):
            from django.contrib.messages import add_message, constants
            logger.warning(f"Non-admin user {request.user.username} attempted to access {view_func.__name__}")
            if is_htmx:
                return HttpResponse('Admin access required.', status=403)
            add_message(request, constants.ERROR, 'You do not have permission to access this page.')
            return redirect('customer_landing')

        return view_func(request, *args, **kwargs)
    return wrapper


def groomer_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Decorator to ensure only groomers or admins can access Django views.

    Redirects unauthenticated users to the login page and unauthorized users
    to customer landing page.

    Args:
        view_func: The view function to wrap.

    Returns:
        Wrapped view function with groomer access control.
    """
    def wrapper(request, *args, **kwargs):
        logger.info(f"groomer_required check: is_authenticated={request.user.is_authenticated}, username={request.user.username if request.user.is_authenticated else 'Anonymous'}")

        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            logger.warning(f"Unauthenticated access attempt to {view_func.__name__}")
            return redirect_to_login(request.get_full_path())

        user_type = getattr(request.user, 'user_type', None)
        if user_type not in ['admin', 'groomer_manager', 'groomer']:
            from django.contrib.messages import add_message, constants
            logger.warning(f"User {request.user.username} with type {user_type} attempted to access groomer-only view {view_func.__name__}")
            add_message(request, constants.ERROR, 'You do not have permission to access this page.')
            return redirect('customer_landing')

        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_for_viewsets(view_func: Callable) -> Callable:
    """Decorator to ensure only admin users can access the viewset action.

    Raises REST framework exceptions for DRF views.

    Args:
        view_func: The viewset action method to wrap.

    Returns:
        Wrapped viewset method with admin access control.
    """
    def wrapper(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Authentication required')

        if not (self.request.user.is_superuser or self.request.user.is_staff):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Admin access required')

        return view_func(self, *args, **kwargs)
    return wrapper


def success_response(message: str = '', data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> JsonResponse:
    """Standard success response for API endpoints.

    Args:
        message: Success message.
        data: Optional data to include in response.
        **kwargs: Additional fields to include in response.

    Returns:
        Response with success=True.
    """
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    response.update(kwargs)
    return JsonResponse(response)


def error_response(error: Union[str, Exception], status: int = 400) -> JsonResponse:
    """Standard error response for API endpoints.

    Args:
        error: Error message or exception.
        status: HTTP status code (default: 400).

    Returns:
        Response with success=False and error message.
    """
    message = str(error) if not isinstance(error, str) else error
    return JsonResponse({'success': False, 'error': message}, status=status)


def validation_error_response(
    missing_fields: Optional[list[str]] = None,
    invalid_fields: Optional[Dict[str, str]] = None
) -> JsonResponse:
    """Standard validation error response.

    Args:
        missing_fields: List of required fields that are missing.
        invalid_fields: Dict of invalid fields and error messages.

    Returns:
        Response with validation errors.
    """
    errors = {}
    if missing_fields:
        errors['missing'] = missing_fields
    if invalid_fields:
        errors['invalid'] = invalid_fields

    message = 'Validation failed'
    if missing_fields:
        message += f': Missing fields: {", ".join(missing_fields)}'
    if invalid_fields:
        message += f': Invalid fields'

    return JsonResponse({'success': False, 'error': message, 'errors': errors}, status=400)


def validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> Tuple[bool, Optional[JsonResponse]]:
    """Validate that all required fields are present in data.

    Args:
        data: Dictionary of data to validate.
        required_fields: List of required field names.

    Returns:
        Tuple of (bool, JsonResponse) where JsonResponse is None if valid.
    """
    missing = [field for field in required_fields if field not in data or not data.get(field)]
    if missing:
        return False, validation_error_response(missing_fields=missing)
    return True, None


def parse_json_request(request: HttpRequest) -> Tuple[bool, Optional[Dict[str, Any]], Optional[JsonResponse]]:
    """Parse JSON from request body with error handling.

    Args:
        request: HTTP request object.

    Returns:
        Tuple of (bool, dict, JsonResponse) where JsonResponse is None if successful.
    """
    try:
        data = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
        import json
        return True, json.loads(data), None
    except json.JSONDecodeError as e:
        return False, None, error_response(f'Invalid JSON: {str(e)}', status=400)
    except Exception as e:
        return False, None, error_response(f'Error parsing request: {str(e)}', status=400)


def calculate_price_breakdown(
    breed: 'Breed',
    service: 'Service',
    dog_weight: Optional[Decimal]
) -> Dict[str, Any]:
    """Calculate detailed price breakdown for a service.

    Provides a detailed breakdown of how the final price is calculated,
    including the base price, any weight surcharges, and add-on amounts.
    This is particularly useful for the pricing preview feature.

    The pricing logic:
    1. For base_required services: breed_base_price + weight_surcharge + service.addon_amount
    2. For standalone services: breed_service_price or service.price + weight_surcharge (if not exempt)
    3. Weight surcharge calculated using breed's increment-based formula (calculate_weight_surcharge)

    Args:
        breed: Breed instance with pricing configuration.
        service: Service instance being priced.
        dog_weight: Dog's weight in lbs (Optional, defaults to 0 if None).

    Returns:
        Dictionary containing:
        - final_price (float): The total calculated price
        - price_breakdown (list of dict): List of price component objects:
            * label (str): Display name of the component
            * amount (float): The amount for this component

    Example:
        breakdown = calculate_price_breakdown(golden_retriever, bath_service, Decimal('45.0'))
        print(f"Total: ${breakdown['final_price']}")
        for item in breakdown['price_breakdown']:
            print(f"  {item['label']}: ${item['amount']}")
    """
    # Calculate weight surcharge using breed's increment-based formula
    weight_surcharge = 0.0

    if dog_weight is not None and not service.exempt_from_surcharge:
        weight_surcharge = float(breed.calculate_weight_surcharge(dog_weight))

    # Build price breakdown
    if service.pricing_type == 'base_required':
        breed_base = float(breed.base_price) if breed.base_price else 0.0
        service_addon = float(service.price) if service.price else 0.0
        breakdown = [
            {'label': 'Breed Base Price', 'amount': breed_base},
            {'label': 'Weight Surcharge', 'amount': weight_surcharge},
            {'label': f'{service.name} (Add-on)', 'amount': service_addon}
        ]
        final_price = breed_base + weight_surcharge + service_addon
    else:
        base_price = float(breed.get_service_price(service))
        breakdown = [
            {'label': f'{service.name}', 'amount': base_price},
            {'label': 'Weight Surcharge', 'amount': weight_surcharge}
        ]
        final_price = base_price + weight_surcharge

    return {
        'final_price': final_price,
        'price_breakdown': breakdown
    }


def get_available_time_slots_count(groomer: 'Groomer', booking_date: date, customer: Optional['Customer'] = None) -> int:
    """Get count of available time slots for a groomer and date.

    Filters time slots to:
    1. Only slots for the specified groomer and date
    2. Only active slots (is_active=True)
    3. Excludes slots that already have pending, confirmed, or completed appointments
    4. If customer provided, allows their existing appointments to remain visible

    Args:
        groomer: Groomer instance.
        booking_date: Date object to check availability for.
        customer: Optional customer instance to exclude from unavailable check.

    Returns:
        Number of available time slots for the given groomer and date.

    Example:
        groomer = Groomer.objects.first()
        tomorrow = date.today() + timedelta(days=1)
        count = get_available_time_slots_count(groomer, tomorrow)
        print(f'{count} slots available for {tomorrow}')
    """
    from .models import TimeSlot, Appointment
    from .constants import AppointmentStatus

    # Get all active time slots for this date
    time_slots = TimeSlot.objects.filter(
        groomer=groomer,
        date=booking_date,
        is_active=True
    )

    # Get existing appointment times (completed appointments also block time slots)
    # Exclude current customer's appointments to allow multi-dog bookings in same slot
    booked_times_query = Appointment.objects.filter(
        groomer=groomer,
        date=booking_date,
        status__in=AppointmentStatus.BLOCKING_STATUSES
    )

    if customer:
        booked_times_query = booked_times_query.exclude(customer=customer)

    booked_times = booked_times_query.values_list('time', flat=True)

    # Filter out booked slots and count remaining
    available_count = time_slots.exclude(start_time__in=booked_times).count()

    return available_count


def get_available_time_slots(groomer: 'Groomer', booking_date: date, customer: Optional['Customer'] = None) -> list[Dict[str, Any]]:
    """Get list of available time slots for a groomer and date.

    Returns an ordered list of time slots that are:
    1. For the specified groomer and date
    2. Currently active (is_active=True)
    3. Not booked with pending, confirmed, or completed appointments
    4. If customer provided, their ACTIVE (pending, confirmed) appointments remain available
       for multi-dog booking in same slot. Completed appointments still block.

    Args:
        groomer: Groomer instance.
        booking_date: Date object to check availability for.
        customer: Optional customer instance to exclude from unavailable check.

    Returns:
        List of dictionaries containing time slot information:
        - time (str): Time in 'HH:MM' 24-hour format
        - display (str): Formatted time string (e.g., '02:30 PM')
        - duration (int): Always 0 (placeholder for future enhancement)
        - has_same_customer_booking (bool): True if slot is available because customer already has an active booking

    Example:
        groomer = Groomer.objects.first()
        tomorrow = date.today() + timedelta(days=1)
        slots = get_available_time_slots(groomer, tomorrow)
        for slot in slots:
            print(f"{slot['display']}")
    """
    from .models import TimeSlot, Appointment
    from .constants import AppointmentStatus

    # Get all active time slots for this date
    time_slots = TimeSlot.objects.filter(
        groomer=groomer,
        date=booking_date,
        is_active=True
    ).order_by('start_time')

    # Get existing appointment times (completed appointments also block time slots)
    # Exclude current customer's ACTIVE appointments (pending, confirmed) only
    # to allow multi-dog bookings in same slot. Completed appointments still block.
    booked_times_query = Appointment.objects.filter(
        groomer=groomer,
        date=booking_date,
        status__in=AppointmentStatus.BLOCKING_STATUSES
    )

    if customer:
        # Only exclude active appointments, not completed ones
        booked_times_query = booked_times_query.exclude(
            customer=customer,
            status__in=AppointmentStatus.ACTIVE_STATUSES
        )

    booked_times = booked_times_query.values_list('time', flat=True)

    # Get customer's active booked times for indicator (not completed)
    customer_booked_times = set()
    if customer:
        customer_booked_times = set(
            Appointment.objects.filter(
                groomer=groomer,
                date=booking_date,
                customer=customer,
                status__in=AppointmentStatus.ACTIVE_STATUSES
            ).values_list('time', flat=True)
        )

    # Filter out booked slots
    available_slots = [
        {
            'time': slot.start_time.strftime('%H:%M'),
            'display': slot.start_time.strftime('%I:%M %p'),
            'duration': 0,  # Can be calculated if needed
            'has_same_customer_booking': slot.start_time in customer_booked_times
        }
        for slot in time_slots
        if slot.start_time not in booked_times
    ]

    return available_slots


def has_appointment_at_time(groomer: 'Groomer', booking_date: date, booking_time: time) -> bool:
    """Check if there is an appointment for a groomer at a specific date and time.

    Checks for existing appointments that are pending, confirmed, or completed.
    Completed appointments block the time slot to prevent same-day rebooking.

    Args:
        groomer: Groomer instance to check.
        booking_date: Date object to check for appointments.
        booking_time: Time object to check for appointments.

    Returns:
        True if there is a pending, confirmed, or completed appointment at that date and time,
        False otherwise.

    Example:
        groomer = Groomer.objects.first()
        appointment_date = date(2026, 5, 15)
        appointment_time = time(14, 30)
        if has_appointment_at_time(groomer, appointment_date, appointment_time):
            print("This time slot is already booked")
    """
    from .models import Appointment
    from .constants import AppointmentStatus

    return Appointment.objects.filter(
        groomer=groomer,
        date=booking_date,
        time=booking_time,
        status__in=AppointmentStatus.BLOCKING_STATUSES
    ).exists()


def parse_groomer_and_date_from_query(
    request_data: Dict[str, Any]
) -> Tuple[Optional['Groomer'], Optional[date], Optional[JsonResponse]]:
    """Parse and validate groomer and date from request data.

    Extracts and validates groomer_id and date strings from request data,
    converting them to proper Python objects with error handling.

    Args:
        request_data: Dictionary containing:
            - groomer_id (str): The groomer's ID as a string
            - date (str): The date in 'YYYY-MM-DD' format

    Returns:
        Tuple of (Groomer or None, date or None, JsonResponse or None).
        If successful, returns (groomer_instance, datetime.date, None).
        If validation fails, returns (None, None, error_response).

    Example:
        groomer, booking_date, error = parse_groomer_and_date_from_query({
            'groomer_id': '1',
            'date': '2026-05-15'
        })
        if error:
            return error
        # Use groomer and booking_date objects
    """
    from datetime import datetime
    from .models import Groomer

    groomer_id = request_data.get('groomer_id')
    date_str = request_data.get('date')

    if not groomer_id or not date_str:
        return None, None, validation_error_response(missing_fields=['groomer_id', 'date'])

    try:
        groomer = get_object_or_404(Groomer, id=groomer_id)
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return groomer, booking_date, None
    except ValueError:
        return None, None, error_response('Invalid date format. Use YYYY-MM-DD', status=400)
    except Exception as e:
        return None, None, error_response(str(e), status=500)


def clone_breed_pricing_config(
    source_breed: 'Breed',
    target_breed: 'Breed',
    clone_note: str = ''
) -> int:
    """Clone pricing configuration from source to target breed.

    Copies all breed-specific pricing setup including:
    - All BreedServiceMapping entries (custom service prices and availability)
    - Weight-based pricing configuration (start_weight, weight_range_amount, weight_price_amount)
    - Updates target breed's clone_note and pricing_cloned_from references

    This is useful when adding new breeds with similar pricing structures
    to an existing breed.

    Args:
        source_breed: Breed object to clone pricing configuration from.
        target_breed: Breed object to clone pricing configuration to.
        clone_note: Optional note documenting the cloning operation.

    Returns:
        Number of pricing items cloned (service mappings).

    Raises:
        None - operates within transaction for atomicity.

    Example:
        source = Breed.objects.get(name='Golden Retriever')
        target = Breed.objects.create(name='Labrador Retriever')
        count = clone_breed_pricing_config(
            source,
            target,
            clone_note='Similar size and coat type'
        )
        print(f'Cloned {count} pricing items')
    """
    from .models import BreedServiceMapping

    BreedServiceMapping.objects.filter(breed=target_breed).delete()

    source_prices = BreedServiceMapping.objects.filter(breed=source_breed)
    cloned_count = 0
    for price in source_prices:
        BreedServiceMapping.objects.create(
            service=price.service,
            breed=target_breed,
            base_price=price.base_price,
            is_available=price.is_available
        )
        cloned_count += 1

    # Clone weight-based pricing fields
    target_breed.start_weight = source_breed.start_weight
    target_breed.weight_range_amount = source_breed.weight_range_amount
    target_breed.weight_price_amount = source_breed.weight_price_amount
    target_breed.typical_weight_min = source_breed.typical_weight_min
    target_breed.typical_weight_max = source_breed.typical_weight_max

    target_breed.pricing_cloned_from = source_breed
    target_breed.clone_note = clone_note
    target_breed.save()

    return cloned_count


def get_breeds_from_bulk_request(
    data: Dict[str, Any]
) -> Tuple[Optional[QuerySet['Breed']], Optional[JsonResponse]]:
    """Get breeds from bulk operation request data.

    Handles two types of bulk requests:
    1. Apply-to-all: Returns all active breeds when apply_to_all=True
    2. Apply-to-specific: Returns breeds matching the provided breed_ids list

    Args:
        data: Request data dictionary containing:
            - apply_to_all (bool): If True, returns all active breeds
            - breed_ids (list of int): List of breed IDs to filter

    Returns:
        Tuple of (QuerySet[Breed] or None, JsonResponse or None).
        If successful, returns (breeds_queryset, None).
        If no breeds selected and apply_to_all is False, returns (None, error_response).

    Example:
        # Apply to all
        data = {'apply_to_all': True}
        breeds, error = get_breeds_from_bulk_request(data)

        # Apply to specific breeds
        data = {'breed_ids': [1, 2, 3]}
        breeds, error = get_breeds_from_bulk_request(data)

        # No breeds selected
        data = {'breed_ids': [], 'apply_to_all': False}
        breeds, error = get_breeds_from_bulk_request(data)
        # error will contain validation error response
    """
    from .models import Breed

    apply_to_all = data.get('apply_to_all', False)
    breed_ids = data.get('breed_ids', [])

    if apply_to_all:
        return Breed.objects.filter(is_active=True), None
    else:
        if not breed_ids:
            return None, validation_error_response(error_message='No breeds selected')
        return Breed.objects.filter(id__in=breed_ids), None



