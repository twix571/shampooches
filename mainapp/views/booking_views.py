"""Booking and service-related views for customers."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from mainapp.models import Appointment, Dog, Service
from mainapp.logging_utils import get_view_logger


@require_http_methods(["GET", "POST"])
def book_appointment(request: HttpRequest) -> HttpResponse:
    """
    Render the multi-step booking modal.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered booking modal.
    """
    import json

    view_logger = get_view_logger(request)
    view_logger.log_action('Booking modal accessed', {'method': request.method})

    preloaded_data = {}

    # Preload customer contact information if user is a customer
    if request.user.is_authenticated and request.user.user_type == 'customer':
        preloaded_customer = {
            'name': f'{request.user.first_name} {request.user.last_name}'.strip(),
            'email': request.user.email,
            'phone': request.user.phone or ''
        }
        preloaded_data['preloadedCustomer'] = preloaded_customer

    context = {
        'preloaded_data_json': json.dumps(preloaded_data)
    }

    return render(request, 'mainapp/booking_modal.html', context)


def services_list(request: HttpRequest) -> HttpResponse:
    """
    Render the services list modal.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered services list modal.
    """
    services = Service.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/services_list_modal.html', {'services': services})


@require_http_methods(["GET"])
@login_required
def book_with_dog(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Render the booking modal with preloaded dog and customer data.

    Preloads:
    - Dog profile information (name, breed, weight, age, notes)
    - Customer contact information

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to preload.

    Returns:
        HttpResponse: Rendered booking modal with preloaded context.
    """
    import json

    view_logger = get_view_logger(request)
    view_logger.log_action('Booking modal with preloaded dog accessed', {
        'dog_id': dog_id,
        'user': request.user.username if request.user.is_authenticated else 'anonymous'
    })

    preloaded_data = {}

    if request.user.is_authenticated and request.user.user_type == 'customer':
        try:
            dog = Dog.objects.get(id=dog_id, owner=request.user)
            preloaded_data['preloadedDog'] = {
                'id': dog.id,
                'name': dog.name,
                'breed_id': dog.breed.id if dog.breed else None,
                'breed_name': dog.breed.name if dog.breed else None,
                'weight': float(dog.weight) if dog.weight else None,
                'age': dog.age or '',
                'notes': dog.notes or ''
            }
            preloaded_data['preloadedCustomer'] = {
                'name': f'{request.user.first_name} {request.user.last_name}'.strip(),
                'email': request.user.email,
                'phone': request.user.phone or ''
            }
        except Dog.DoesNotExist:
            pass

    context = {
        'preloaded_data_json': json.dumps(preloaded_data)
    }

    return render(request, 'mainapp/booking_modal.html', context)


@require_http_methods(["GET"])
@login_required
def rebook_appointment(request: HttpRequest, appointment_id: int) -> HttpResponse:
    """
    Render the booking modal preloaded with data from a previous completed appointment.

    Preloads:
    - Dog profile from the previous appointment
    - Service from the previous appointment
    - Groomer from the previous appointment (prefers preferred_groomer, falls back to groomer)
    - Customer contact information

    The modal will start at step 4 (Day selection) only if groomer data is available.
    If no groomer is associated with the appointment, the modal starts at step 1.

    Args:
        request: The HTTP request object.
        appointment_id: The ID of the completed appointment to rebook.

    Returns:
        HttpResponse: Rendered booking modal with preloaded context.
    """
    import json

    view_logger = get_view_logger(request)
    view_logger.log_action('Rebooking modal accessed', {
        'appointment_id': appointment_id,
        'user': request.user.username if request.user.is_authenticated else 'anonymous'
    })

    preloaded_data = {
        'startAtStep': 1  # Default to step 1, will advance to step 4 only if groomer is available
    }

    if request.user.is_authenticated and request.user.user_type == 'customer':
        try:
            # appointments are linked to Customer model, check via customer_profile
            try:
                customer = request.user.customer_profile
            except Customer.DoesNotExist:
                raise Appointment.DoesNotExist()

            appointment = Appointment.objects.filter(id=appointment_id, customer=customer).first()
            if not appointment:
                raise Appointment.DoesNotExist()

            # Debug logging

            # Preload dog data
            if appointment.dog_breed:
                preloaded_data['preloadedDog'] = {
                    'name': appointment.dog_name,
                    'breed_id': appointment.dog_breed.id,
                    'breed_name': appointment.dog_breed.name,
                    'weight': float(appointment.dog_weight) if appointment.dog_weight else None,
                    'age': appointment.dog_age or '',
                    'notes': ''
                }

            # Preload customer data
            preloaded_data['preloadedCustomer'] = {
                'name': f'{request.user.first_name} {request.user.last_name}'.strip(),
                'email': request.user.email,
                'phone': request.user.phone or ''
            }

            # Preload groomer as preferred groomer
            # Check both actual groomer and preferred groomer, preferring preferred_groomer for rebooking
            groomer_to_preload = appointment.preferred_groomer or appointment.groomer
            if groomer_to_preload:
                preloaded_data['preloadedGroomer'] = {
                    'id': groomer_to_preload.id,
                    'name': groomer_to_preload.name
                }
                preloaded_data['startAtStep'] = 4  # Advance to step 4 only if groomer is available
            else:
                # No groomer data available, start from step 1
                preloaded_data['startAtStep'] = 1

            # Preload service data
            if appointment.service:
                preloaded_data['preloadedService'] = {
                    'id': appointment.service.id,
                    'name': appointment.service.name
                }
        except Appointment.DoesNotExist:
            pass

    context = {
        'preloaded_data_json': json.dumps(preloaded_data)
    }

    return render(request, 'mainapp/booking_modal.html', context)
