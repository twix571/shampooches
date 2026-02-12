"""Booking and service-related views for customers."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from mainapp.models import Dog, Service
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
    view_logger = get_view_logger(request)
    view_logger.log_action('Booking modal accessed', {'method': request.method})

    return render(request, 'mainapp/booking_modal.html')


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
    view_logger = get_view_logger(request)
    view_logger.log_action('Booking modal with preloaded dog accessed', {
        'dog_id': dog_id,
        'user': request.user.username if request.user.is_authenticated else 'anonymous'
    })

    context = {}

    if request.user.is_authenticated and request.user.user_type == 'customer':
        try:
            dog = Dog.objects.get(id=dog_id, owner=request.user)
            context['preloaded_dog'] = {
                'id': dog.id,
                'name': dog.name,
                'breed_id': dog.breed.id if dog.breed else None,
                'breed_name': dog.breed.name if dog.breed else None,
                'weight': float(dog.weight) if dog.weight else None,
                'age': dog.age or '',
                'notes': dog.notes or ''
            }
            context['preloaded_customer'] = {
                'name': f'{request.user.first_name} {request.user.last_name}'.strip(),
                'email': request.user.email,
                'phone': request.user.phone or ''
            }
        except Dog.DoesNotExist:
            pass

    return render(request, 'mainapp/booking_modal.html', context)
