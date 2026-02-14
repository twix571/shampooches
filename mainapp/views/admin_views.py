"""Admin views for managing customers, groomers, and site configuration."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count, Avg, Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from mainapp.models import Customer, Groomer, SiteConfig, LegalAgreement, Appointment, Dog, Breed
from mainapp.utils import admin_required


@admin_required
def customers_modal(request):
    """
    Render the customers list modal.

    Displays all customers in the database ordered by name.
    Supports search functionality with exact and fuzzy matching for name, email, and phone.
    """
    search_query = request.GET.get('search', '').strip()
    customers = Customer.objects.all()

    # Apply search filter if query is provided
    if search_query:
        # Exact match for phone (digits only)
        clean_phone = ''.join(filter(str.isdigit, search_query))
        # Fuzzy match for name and email (case-insensitive partial match)
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=clean_phone)
        )

    customers = customers.order_by('name')
    return render(request, 'mainapp/admin/customers_modal.html', {'customers': customers, 'search_query': search_query})


def groomers_modal(request):
    """
    Render the groomers list modal.

    Displays only active groomers ordered by display order and name.
    """
    groomers = Groomer.objects.filter(is_active=True).order_by('order', 'name')
    return render(request, 'mainapp/admin/groomers_list_modal.html', {'groomers': groomers})


@admin_required
def groomers_management_modal(request):
    """
    Render the groomers management modal.

    Displays all including inactive groomers for administrative purposes.
    """
    groomers = Groomer.objects.all().order_by('order', 'name')
    return render(request, 'mainapp/admin/groomers_management_modal.html', {'groomers': groomers})


@admin_required
def site_config_modal(request):
    """
    Render the site configuration modal.

    Displays business information, contact details, and business hours.
    Changes affect the customer landing page, booking flow, and contact displays.
    """
    site_config = SiteConfig.get_active_config()
    return render(request, 'mainapp/admin/site_config_modal.html', {'site_config': site_config})


@admin_required
def legal_agreements_modal(request):
    """
    Render the legal agreements modal.

    Displays all legal agreement versions with the active one highlighted.
    Staff can create, edit, and manage agreement versions.
    """
    active_agreement = LegalAgreement.get_active_agreement()
    agreements = LegalAgreement.objects.all().order_by('-effective_date')
    return render(request, 'mainapp/admin/legal_agreements_modal.html', {
        'active_agreement': active_agreement,
        'agreements': agreements,
        'agreement_count': agreements.count()
    })


@admin_required
def booking_settings_modal(request):
    """
    Render the booking settings modal.

    Allows staff to configure booking-related settings like the maximum
    number of dogs per day a customer can book.
    """
    site_config = SiteConfig.get_active_config()
    return render(request, 'mainapp/admin/booking_settings_modal.html', {'site_config': site_config})


@admin_required
def customer_detail_modal(request, customer_id):
    """
    Render the customer detail modal with comprehensive information.

    Displays:
    - Contact information, account status, address
    - Dog profiles with photos and health notes
    - Appointment history with visual timeline
    - Booking preferences and preferred groomer
    - Revenue summary per customer
    - Notes/Tags system for customer classification
    """
    customer = get_object_or_404(
        Customer.objects.select_related('preferred_groomer', 'user'),
        pk=customer_id
    )

    # Get all appointments for this customer, ordered by date descending
    appointments = customer.appointments.prefetch_related(
        'service', 'groomer'
    ).order_by('-date', '-time')

    # Calculate statistics
    completed_appointments = appointments.filter(status='completed').count()
    total_appointments = appointments.count()
    total_revenue = appointments.filter(
        status__in=['confirmed', 'completed']
    ).aggregate(total=Sum('price_at_booking'))['total'] or '0.00'
    average_price = appointments.filter(
        status__in=['confirmed', 'completed']
    ).aggregate(avg=Avg('price_at_booking'))['avg'] or '0.00'

    # Get all dogs for this customer (through the User relationship)
    dogs = []
    if customer.user:
        dogs = Dog.objects.filter(owner=customer.user).select_related('breed')

    context = {
        'customer': customer,
        'appointments': appointments,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'total_revenue': total_revenue,
        'average_price': average_price,
        'dogs': dogs,
    }

    return render(request, 'mainapp/admin/customer_detail_modal.html', context)


@login_required
def update_customer_notes(request, customer_id):
    """
    Update customer notes via HTMX request.

    Expects POST request with 'notes' field containing the updated notes text.
    Returns HTML fragment with updated notes display.
    """
    if request.method == 'POST' and request.user.is_staff:
        customer = get_object_or_404(Customer, pk=customer_id)
        notes = request.POST.get('notes', '')

        customer.notes = notes
        customer.save()

        # Return the updated notes fragment
        if notes:
            html = f'<div class="text-sm text-gray-700 whitespace-pre-line">{notes}</div>'
        else:
            html = '<p class="text-sm text-gray-500 italic">No notes added for this customer.</p>'

        return HttpResponse(html)

    return HttpResponse(status=403)


@admin_required
def edit_customer_dog_modal(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Render the edit dog modal for staff.
    Allows staff to edit any customer's dog profile.

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to edit.
    """
    dog = get_object_or_404(Dog, pk=dog_id)

    # Verify the dog belongs to a customer
    if not dog.owner or dog.owner.user_type != 'customer':
        return HttpResponse(status=403)

    # Get the customer associated with this dog
    customer = get_object_or_404(Customer, user=dog.owner)

    breeds = Breed.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/edit_dog_modal.html', {'dog': dog, 'breeds': breeds, 'customer_id': customer.pk})


@admin_required
def edit_customer_dog(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Edit an existing customer's dog profile (staff-only).
    Updates a Dog record associated with a customer and redirects back to customer detail view.

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to edit.
    """
    dog = get_object_or_404(Dog, pk=dog_id)

    # Verify the dog belongs to a customer
    if not dog.owner or dog.owner.user_type != 'customer':
        return HttpResponse(status=403)

    # Get the customer associated with this dog
    customer = Customer.objects.filter(user=dog.owner).first()
    if not customer:
        return HttpResponse(status=403)

    if request.method == 'POST':
        from mainapp.forms import DogForm
        from django.http import JsonResponse

        form = DogForm(request.POST, instance=dog)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Dog profile updated successfully!'}, status=200)
        else:
            errors = {field: [str(error) for error in errors] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    return HttpResponse(status=405)
