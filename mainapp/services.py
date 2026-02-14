"""
Services module for the grooming salon application.

This module contains business logic services for booking appointments,
creating customers, and handling related operations.
"""

import logging
from datetime import date, time
from decimal import Decimal
from typing import Optional
from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404

from .models import Appointment, Breed, Customer, Groomer, Service, LegalAgreement, MessageThread, Message
from .constants import ErrorMessages, AppointmentStatus

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class BookingDateInPastError(ValidationError):
    """Raised when attempting to book an appointment in the past."""
    pass


class BookingConflictError(ValidationError):
    """Raised when attempting to book a conflicting appointment."""
    pass


class InactiveServiceError(ValidationError):
    """Raised when attempting to book an inactive service."""
    pass


class InactiveGroomerError(ValidationError):
    """Raised when attempting to book an inactive groomer."""
    pass


class InvalidInputError(ValidationError):
    """Raised when input validation fails."""
    pass


# ============================================================================
# Booking Services
# ============================================================================

def create_booking(
    customer_email: str,
    customer_name: str,
    customer_phone: str,
    service_id: int,
    breed_id: int,
    groomer_id: int,
    dog_name: str,
    dog_weight: Decimal,
    dog_age: str,
    booking_date: date,
    booking_time: time,
    notes: str = '',
    preferred_groomer_id: Optional[int] = None,
    user=None,
    agreement_version_id: Optional[int] = None,
) -> Appointment:
    """Centralized booking creation service.

    This service handles the core business logic for creating appointments:
    - Getting or creating customers
    - Retrieving related objects (service, breed, groomer)
    - Calculating final price based on breed and weight
    - Creating and saving the appointment

    Args:
        customer_email: Customer's email address (used for uniqueness)
        customer_name: Customer's full name
        customer_phone: Customer's phone number
        service_id: ID of the service being booked
        breed_id: ID of the dog's breed
        groomer_id: ID of the groomer performing the service (actual groomer)
        dog_name: Name of the dog
        dog_weight: Weight of the dog in lbs (for pricing calculation)
        dog_age: Age of the dog (for records)
        booking_date: Date of the appointment
        booking_time: Time of the appointment
        notes: Optional notes about the booking
        preferred_groomer_id: Optional ID of the customer's preferred groomer (may differ from actual groomer)
        user: Optional User object for registered customers (None for guest bookings)
        agreement_version_id: Optional ID of the legal agreement version that was accepted

    Returns:
        Appointment: The created appointment object

    Raises:
        InvalidInputError: If input validation fails
        BookingDateInPastError: If booking date is in the past
        InactiveServiceError: If service is inactive
        InactiveGroomerError: If groomer is inactive
        BookingConflictError: If time slot already booked
        DatabaseError: If database operation fails
        ValidationError: For other validation errors

    Example:
        appointment = create_booking(
            customer_email='john@example.com',
            customer_name='John Doe',
            customer_phone='5551234567',
            service_id=1,
            breed_id=2,
            groomer_id=3,
            dog_name='Buddy',
            dog_weight=Decimal('45.0'),
            dog_age='3 years',
            booking_date=date(2026, 2, 5),
            booking_time=time(14, 30),
            notes='Please trim nails',
            preferred_groomer_id=3
        )
    """
    try:
        with transaction.atomic():
            # Validate input fields
            _validate_booking_input(
                customer_name, customer_phone, dog_name, dog_age, dog_weight
            )

            # Get or create/update customer
            customer = _get_or_create_customer(
                customer_email, customer_name, customer_phone, user
            )

            # Get preferred groomer if provided
            preferred_groomer = None
            if preferred_groomer_id:
                preferred_groomer = _get_or_raise(Groomer, preferred_groomer_id, 'Preferred Groomer')

                # Validate preferred groomer is active
                if not preferred_groomer.is_active:
                    logger.warning(f'Attempted to book with inactive preferred groomer: {preferred_groomer.name}')
                    raise InactiveGroomerError(
                        ErrorMessages.INACTIVE_GROOMER.format(groomer=preferred_groomer.name)
                    )

            # Get related objects
            groomer = _get_or_raise(Groomer, groomer_id, 'Groomer')
            breed = _get_or_raise(Breed, breed_id, 'Breed')
            service = _get_or_raise(Service, service_id, 'Service')

            # Validate booking constraints (pass customer for same-customer multi-dog support)
            _validate_booking_constraints(
                booking_date, groomer, service, booking_time, customer
            )

            # Calculate final price
            final_price = _calculate_final_price(breed, service, dog_weight)

            # Get legal agreement version if provided
            agreement_version = None
            if agreement_version_id:
                try:
                    agreement_version = LegalAgreement.objects.get(id=agreement_version_id, is_active=True)
                except LegalAgreement.DoesNotExist:
                    logger.warning(f'Agreement version with ID {agreement_version_id} not found or not active')

            # Create and return the appointment
            appointment = _create_appointment(
                customer, service, groomer, breed,
                dog_name, dog_weight, dog_age,
                booking_date, booking_time,
                notes, final_price, user, preferred_groomer, agreement_version
            )

            logger.info(
                f'Created appointment #{appointment.id} for {customer.name} '
                f'with {groomer.name} on {booking_date} at {booking_time} '
                f'- Service: {service.name}, Dog: {dog_name}, Price: ${final_price} '
                f'{"(Preferred: " + preferred_groomer.name + ")" if preferred_groomer else ""}'
            )

            return appointment

    except (InvalidInputError, BookingDateInPastError, InactiveServiceError,
            InactiveGroomerError, BookingConflictError):
        raise
    except ValidationError:
        raise
    except DatabaseError as e:
        logger.error(f'Database error in create_booking: {str(e)}')
        raise ValidationError('A database error occurred while creating the booking. Please try again.')
    except Exception as e:
        logger.error(f'Unexpected error in create_booking: {str(e)}', exc_info=True)
        raise ValidationError('An unexpected error occurred while creating the booking. Please try again.')


# ============================================================================
# Helper Functions
# ============================================================================

def _validate_booking_input(
    customer_name: str,
    customer_phone: str,
    dog_name: str,
    dog_age: str,
    dog_weight: Decimal
) -> None:
    """Validate booking input fields.

    Args:
        customer_name: Customer's full name
        customer_phone: Customer's phone number
        dog_name: Dog's name
        dog_age: Dog's age
        dog_weight: Dog's weight

    Raises:
        InvalidInputError: If any validation fails
    """
    if not customer_name or not customer_name.strip():
        raise InvalidInputError('Customer name cannot be empty.')
    if not customer_phone or not customer_phone.strip():
        raise InvalidInputError('Customer phone number cannot be empty.')
    if not dog_name or not dog_name.strip():
        raise InvalidInputError('Dog name cannot be empty.')
    if not dog_age or not dog_age.strip():
        raise InvalidInputError('Dog age cannot be empty.')
    if dog_weight is None or dog_weight <= 0:
        raise InvalidInputError(f'Dog weight must be a positive number. Got: {dog_weight}')


def _get_or_create_customer(
    email: str,
    name: str,
    phone: str,
    user=None
) -> Customer:
    """Get or create a customer.

    Args:
        email: Customer's email
        name: Customer's name
        phone: Customer's phone
        user: Optional User object (for registered customers)

    Returns:
        Customer: The customer object

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # If a User is provided and has a Customer profile, use it
        if user and hasattr(user, 'customer_profile') and user.customer_profile:
            customer = user.customer_profile
            # Update existing customer profile with latest info
            if customer.name != name or customer.phone != phone:
                customer.name = name
                customer.phone = phone
                customer.save()
                logger.info(f'Updated existing customer profile for user {user.username}')
            return customer

        # Otherwise, get or create by email (for guest bookings or legacy customers)
        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'phone': phone
            }
        )

        if created:
            logger.info(f'Created new customer: {email}')
        else:
            if customer.name != name or customer.phone != phone:
                customer.name = name
                customer.phone = phone
                customer.save()
                logger.info(f'Updated customer info for {email}')
            else:
                logger.info(f'Using existing customer: {email}')

        return customer
    except DatabaseError as e:
        logger.error(f'Database error creating/updating customer: {str(e)}')
        raise


def _get_or_raise(model_class, object_id, model_name: str):
    """Get an object or raise DoesNotExist.

    Args:
        model_class: The model class
        object_id: The object's ID
        model_name: Name of the model for error message

    Returns:
        The object

    Raises:
        DatabaseError: If object doesn't exist
    """
    try:
        return model_class.objects.get(id=object_id)
    except model_class.DoesNotExist:
        error_msg = f'{model_name} with ID {object_id} not found'
        logger.warning(error_msg)
        raise DatabaseError(error_msg)


def _validate_booking_constraints(
    booking_date: date,
    groomer: Groomer,
    service: Service,
    booking_time: time,
    customer: Customer
) -> None:
    """Validate booking date, service, groomer, and time slot availability.

    Allows customers to book multiple dogs in the same time slot, up to max_dogs_per_day limit.

    Args:
        booking_date: Date of the booking
        groomer: Groomer object
        service: Service object
        booking_time: Time of the booking
        customer: Customer object making the booking

    Raises:
        BookingDateInPastError: If booking date is in the past
        InactiveServiceError: If service is inactive
        InactiveGroomerError: If groomer is inactive
        BookingConflictError: If time slot already booked by another customer
    """
    from .models import SiteConfig

    # Validate booking_date is in the future
    if booking_date < date.today():
        logger.warning(f'Attempted to book in the past: {booking_date}')
        raise BookingDateInPastError(
            ErrorMessages.PAST_BOOKING.format(date=booking_date)
        )

    # Validate service is active
    if not service.is_active:
        logger.warning(f'Attempted to book inactive service: {service.name}')
        raise InactiveServiceError(
            ErrorMessages.INACTIVE_SERVICE.format(service=service.name)
        )

    # Validate groomer is active
    if not groomer.is_active:
        logger.warning(f'Attempted to book inactive groomer: {groomer.name}')
        raise InactiveGroomerError(
            ErrorMessages.INACTIVE_GROOMER.format(groomer=groomer.name)
        )

    # Check for conflicts with other customers
    other_customer_conflicts = Appointment.objects.filter(
        groomer=groomer,
        date=booking_date,
        time=booking_time,
        status__in=AppointmentStatus.BLOCKING_STATUSES
    ).exclude(customer=customer)

    if other_customer_conflicts.exists():
        logger.warning(
            f'Booking conflict detected: {groomer.name} on {booking_date} at {booking_time}'
        )
        raise BookingConflictError(
            ErrorMessages.BOOKING_CONFLICT.format(
                groomer=groomer.name,
                date=booking_date,
                time=booking_time
            )
        )

    # Check daily limit for this customer
    site_config = SiteConfig.get_active_config()
    max_dogs = site_config.max_dogs_per_day if site_config else 3

    # Count existing appointments for this customer on this date
    existing_appointments = Appointment.objects.filter(
        customer=customer,
        date=booking_date,
        status__in=AppointmentStatus.BLOCKING_STATUSES
    ).count()

    if existing_appointments >= max_dogs:
        logger.warning(
            f'Customer {customer.name} exceeded max_dogs_per_day ({max_dogs}) on {booking_date}'
        )
        raise BookingConflictError(
            f'You have reached the maximum number of bookings ({max_dogs}) for this day. '
            f'Please book on a different day or contact us for special arrangements.'
        )

    # Check if this customer already has this time slot booked
    # If so, we still allow it because same-customer bookings are permitted
    # as long as daily limit is not exceeded


def _calculate_final_price(
    breed: Breed,
    service: Service,
    dog_weight: Decimal
) -> Decimal:
    """Calculate final price for a service and dog weight.

    Args:
        breed: Breed object
        service: Service object
        dog_weight: Dog's weight

    Returns:
        Decimal: Final price

    Raises:
        ValidationError: If price calculation fails
    """
    try:
        return breed.get_final_price(service, dog_weight)
    except Exception as e:
        logger.error(f'Error calculating price: {str(e)}')
        raise ValidationError(f'Error calculating final price: {str(e)}')


def ensure_customer_thread(user):
    """Ensure customer has a message thread, create one if missing.

    Args:
        user: User object

    Returns:
        MessageThread: The existing or newly created thread
    """
    from mainapp.models import MessageThread, Message

    # Check if user already has any threads
    existing_thread = MessageThread.objects.filter(
        customer=user,
        is_active=True
    ).first()

    if existing_thread:
        return existing_thread

    # Create a new thread with a default subject
    thread = MessageThread.objects.create(
        customer=user,
        subject='Appointment Inquiry'
    )

    # Create a welcome message from staff (admin)
    from users.models import User
    admin_user = User.objects.filter(
        user_type='admin',
        is_active=True
    ).first()

    if admin_user:
        Message.objects.create(
            thread=thread,
            sender=admin_user,
            content='Welcome! Feel free to ask questions about your upcoming appointment or any other grooming services.'
        )

    return thread


def _create_appointment(
    customer: Customer,
    service: Service,
    groomer: Groomer,
    breed: Breed,
    dog_name: str,
    dog_weight: Decimal,
    dog_age: str,
    booking_date: date,
    booking_time: time,
    notes: str,
    final_price: Decimal,
    user=None,
    preferred_groomer: Optional[Groomer] = None,
    agreement_version: Optional[LegalAgreement] = None,
) -> Appointment:
    """Create and save an appointment.

    Args:
        customer: Customer object
        service: Service object
        groomer: Groomer object (actual groomer)
        breed: Breed object
        dog_name: Dog's name
        dog_weight: Dog's weight
        dog_age: Dog's age
        booking_date: Date of appointment
        booking_time: Time of appointment
        notes: Optional notes
        final_price: Calculated final price
        user: Optional User object for registered customers (None for guest bookings)
        preferred_groomer: Optional Preferred Groomer object (may differ from actual groomer)
        agreement_version: Optional LegalAgreement object for tracking customer agreement acceptance

    Returns:
        Appointment: The created appointment

    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Prepare appointment data
        appointment_data = {
            'customer': customer,
            'user': user,
            'service': service,
            'groomer': groomer,
            'preferred_groomer': preferred_groomer,
            'dog_breed': breed,
            'dog_name': dog_name,
            'dog_weight': dog_weight,
            'dog_age': dog_age,
            'date': booking_date,
            'time': booking_time,
            'notes': notes,
            'price_at_booking': final_price,
            'status': 'pending'
        }

        # Add agreement version and accepted timestamp if agreement was signed
        if agreement_version:
            appointment_data['agreement_version'] = agreement_version
            appointment_data['agreement_accepted_at'] = timezone.now()

        appointment = Appointment.objects.create(**appointment_data)

        # Create a message thread for registered customers if they don't have one
        if user and user.user_type == 'customer':
            ensure_customer_thread(user)

        return appointment
    except DatabaseError as e:
        logger.error(f'Database error creating appointment: {str(e)}')
        raise
