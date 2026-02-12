import json
import logging
import platform
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

User = get_user_model()

from .models import (
    Appointment, Breed, BreedServiceMapping, Customer,
    Groomer, Service, TimeSlot, Dog, DogDeletionRequest, SiteConfig
)
from .services import create_booking
from .utils import (
    success_response, error_response, validation_error_response,
    parse_json_request, validate_required_fields,
    calculate_price_breakdown, get_available_time_slots_count,
    get_available_time_slots, has_appointment_at_time,
    parse_groomer_and_date_from_query, admin_required, groomer_required,
    clone_breed_pricing_config, get_breeds_from_bulk_request
)
from .logging_utils import get_view_logger

# Get module-level logger for backward compatibility
module_logger = logging.getLogger(__name__)


@csrf_exempt
def health_check(request: HttpRequest) -> JsonResponse:
    """
    Health check endpoint for load balancers and monitoring systems.

    Checks:
    - Database connectivity
    - Cache connectivity (if configured)
    - Application status

    Returns:
        JsonResponse: JSON response with health status and component status details
    """
    status = 'ok'
    components = {}
    http_status = 200

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            components['database'] = {'status': 'ok', 'message': 'Database connection successful'}
    except Exception as e:
        status = 'error'
        components['database'] = {'status': 'error', 'message': f'Database connection failed: {str(e)}'}
        http_status = 503

    # Check cache connectivity (only if cache is configured)
    try:
        cache_key = '__health_check__'
        cache.set(cache_key, 'test', timeout=10)
        cache.get(cache_key)
        cache.delete(cache_key)
        components['cache'] = {'status': 'ok', 'message': 'Cache connection successful'}
    except Exception as e:
        # Cache failures should not result in health check failure
        components['cache'] = {'status': 'warning', 'message': f'Cache connection failed: {str(e)}'}

    return JsonResponse({
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'components': components
    }, status=http_status)


@admin_required
def admin_landing(request: HttpRequest) -> HttpResponse:
    view_logger = get_view_logger(request)
    view_logger.log_action('Admin landing page accessed', {'user': request.user.username})
    
    today = date.today()
    view_logger.log_database_operation('query_dashboard_stats', {'date': str(today)})
    stats = Appointment.objects.get_dashboard_stats()

    view_logger.log_database_operation('query_today_appointments', {'date': str(today)})
    today_schedule = Appointment.objects.filter(
        date=today
    ).order_by('time')

    action_cards = [
        {
            'page_url': reverse('pricing_management'),
            'bg_color': 'bg-teal-100',
            'hover_color': 'group-hover:bg-teal-200',
            'text_color': 'text-teal-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>',
            'title': 'Pricing Management',
            'description': 'Manage breeds, base prices, and weight-based pricing'
        },
        {
            'modal_url': reverse('appointments_modal'),
            'bg_color': 'bg-cyan-100',
            'hover_color': 'group-hover:bg-cyan-200',
            'text_color': 'text-cyan-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>',
            'title': 'View Appointments',
            'description': 'See upcoming, current, and past appointments'
        },
        {
            'modal_url': reverse('customers_modal'),
            'bg_color': 'bg-emerald-100',
            'hover_color': 'group-hover:bg-emerald-200',
            'text_color': 'text-emerald-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>',
            'title': 'Customer Database',
            'description': 'Access and manage customer information'
        },
        {
            'modal_url': reverse('groomers_management_modal'),
            'bg_color': 'bg-sky-100',
            'hover_color': 'group-hover:bg-sky-200',
            'text_color': 'text-sky-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>',
            'title': 'Manage Groomers',
            'description': 'Add, edit, or deactivate team members'
        }
    ]

    context = {
        'today_appointments': stats['today_appointments'],
        'pending_appointments': stats['pending_appointments'],
        'total_customers': stats['total_customers'],
        'monthly_revenue': stats['monthly_revenue'],
        'today_schedule': today_schedule,
        'action_cards': action_cards,
    }
    return render(request, 'mainapp/admin_landing.html', context)


def customer_landing(request: HttpRequest) -> HttpResponse:
    """Customer landing page with dynamic pricing and business hours."""
    # Get active services for the services preview section (limit to 4 for landing page)
    services = Service.objects.filter(is_active=True).order_by('name')[:4]

    # Get active site configuration for business hours and contact info
    site_config = SiteConfig.get_active_config()

    context = {
        'landing_services': services,
        'site_config': site_config,
    }
    return render(request, 'mainapp/customer_landing.html', context)


@groomer_required
def groomer_landing(request: HttpRequest) -> HttpResponse:
    today = date.today()
    groomer_appointments = Appointment.objects.filter(
        date__gte=today
    ).order_by('date', 'time')

    context = {
        'groomer_appointments': groomer_appointments,
    }
    return render(request, 'mainapp/groomer_landing.html', context)


@require_http_methods(["GET", "POST"])
def book_appointment(request: HttpRequest) -> HttpResponse:
    """Render the multi-step booking modal.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered booking modal.
    """
    view_logger = get_view_logger(request)
    view_logger.log_action('Booking modal accessed', {'method': request.method})
    
    return render(request, 'mainapp/booking_modal.html')


def services_list(request: HttpRequest) -> HttpResponse:
    """Render the services list modal.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered services list modal.
    """
    services = Service.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/services_list_modal.html', {'services': services})


@admin_required
def appointments_modal(request: HttpRequest) -> HttpResponse:
    from django.utils import timezone

    appointments = Appointment.objects.all().order_by('-date', '-time')

    try:
        week_offset = int(request.GET.get('week', '0'))
    except (ValueError, TypeError):
        week_offset = 0
    today = timezone.now().date()

    monday = today - timedelta(days=today.weekday())
    monday += timedelta(weeks=week_offset)

    week_dates = []
    for i in range(5):
        day_date = monday + timedelta(days=i)
        week_dates.append({
            'date': day_date,
            'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][i],
            'is_today': day_date == today
        })

    appointments_by_date = defaultdict(list)
    for appointment in appointments:
        appointments_by_date[appointment.date].append(appointment)

    calendar_data = []
    for day_info in week_dates:
        calendar_data.append({
            'date': day_info['date'],
            'day_name': day_info['day_name'],
            'is_today': day_info['is_today'],
            'appointments': appointments_by_date.get(day_info['date'], [])
        })

    return render(request, 'mainapp/admin/appointments_modal.html', {
        'calendar_data': calendar_data,
        'week_offset': week_offset,
        'all_appointments': appointments,
    })


@admin_required
def customers_modal(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'mainapp/admin/customers_modal.html', {'customers': customers})


def groomers_modal(request):
    groomers = Groomer.objects.filter(is_active=True).order_by('order', 'name')
    return render(request, 'mainapp/admin/groomers_list_modal.html', {'groomers': groomers})


@admin_required
def groomers_management_modal(request):
    groomers = Groomer.objects.all().order_by('order', 'name')
    return render(request, 'mainapp/admin/groomers_management_modal.html', {'groomers': groomers})


@admin_required
def pricing_management(request):
    """Admin page for managing services, breeds, weight ranges, and prices (server-side rendered)."""
    # Create a default service if none exists (required for base prices)
    if not Service.objects.exists():
        Service.objects.create(
            name='Default Service',
            description='Default service for base pricing',
            price=Decimal('0.00'),
            pricing_type='base_required',
            duration_minutes=60
        )
    services = Service.objects.all().order_by('name')
    breeds = Breed.objects.filter(is_active=True).order_by('name')
    service_breed_prices = BreedServiceMapping.objects.all().select_related('service', 'breed')
    
    # Create mapping of breed_id to base_price for the first service
    # Fall back to Breed.base_price if ServiceMapping doesn't have a price
    breed_data = []
    if services.exists():
        first_service = services.first()
        prices_for_service = service_breed_prices.filter(service=first_service)
        service_mapping_prices = {str(price.breed_id): str(price.base_price) for price in prices_for_service if price.base_price}
        
        for breed in breeds:
            breed_id = str(breed.id)
            # Use ServiceMapping price if it exists, otherwise fall back to Breed.base_price
            base_price = None
            if breed_id in service_mapping_prices:
                base_price = service_mapping_prices[breed_id]
            elif breed.base_price:
                base_price = str(breed.base_price)
            
            breed_data.append({
                'id': breed.id,
                'name': breed.name,
                'base_price': base_price,
                'weight_range_amount': breed.weight_range_amount,
                'weight_price_amount': breed.weight_price_amount,
                'start_weight': breed.start_weight,
            })
    
    context = {
        'services': services,
        'breeds': breed_data,
        'service_breed_prices': service_breed_prices,
        'default_service': services.first(),
    }
    return render(request, 'mainapp/pricing/pricing_management.html', context)





@admin_required
def weight_ranges_editor_modal(request, breed_id):
    breed = get_object_or_404(Breed, id=breed_id)
    return render(request, 'mainapp/pricing/weight_pricing_modal.html', {'breed': breed})


@require_http_methods(["POST"])
@admin_required
def update_breed_weight_pricing(request):
    success, data, error_response = parse_json_request(request)
    if not success:
        return error_response

    breed_id = data.get('breed_id')
    weight_range_amount = data.get('weight_range_amount')
    weight_price_amount = data.get('weight_price_amount')
    start_weight = data.get('start_weight')

    if not breed_id:
        return JsonResponse({'success': False, 'error': 'Breed ID is required'}, status=400)

    try:
        breed = get_object_or_404(Breed, id=breed_id)
        breed.weight_range_amount = weight_range_amount
        breed.weight_price_amount = weight_price_amount
        breed.start_weight = start_weight
        breed.save()
        return JsonResponse({'success': True, 'message': 'Weight pricing saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@admin_required
def breed_pricing_table_modal(request, breed_id):
    breed = get_object_or_404(Breed, id=breed_id)
    services = Service.objects.all().order_by('name')
    service_breed_prices = BreedServiceMapping.objects.filter(breed=breed).select_related('service')

    sample_weights = []

    if breed.start_weight and breed.weight_range_amount and breed.weight_price_amount:
        sample_weights.append({
            'key': 'start',
            'weight': breed.start_weight,
            'label': f"{breed.start_weight} lbs",
            'description': 'Start weight'
        })

        sample_weights.append({
            'key': 'increment_1',
            'weight': breed.start_weight + breed.weight_range_amount,
            'label': f"{breed.start_weight + breed.weight_range_amount} lbs",
            'description': f"Start + 1 × {breed.weight_range_amount} lbs"
        })

        # Add start + 3 increments
        sample_weights.append({
            'key': 'increment_3',
            'weight': breed.start_weight + (breed.weight_range_amount * 3),
            'label': f"{breed.start_weight + (breed.weight_range_amount * 3)} lbs",
            'description': f"Start + 3 × {breed.weight_range_amount} lbs"
        })

        if breed.typical_weight_max:
            sample_weights.append({
                'key': 'typical_max',
                'weight': breed.typical_weight_max,
                'label': f"{breed.typical_weight_max} lbs",
                'description': 'Typical maximum'
            })
        else:
            sample_weights.append({
                'key': 'increment_5',
                'weight': breed.start_weight + (breed.weight_range_amount * 5),
                'label': f"{breed.start_weight + (breed.weight_range_amount * 5)} lbs",
                'description': f"Start + 5 × {breed.weight_range_amount} lbs"
            })

    pricing_matrix = {}
    for service in services:
        pricing_matrix[service.id] = {}
        try:
            breed_price = service_breed_prices.get(service=service)
            base_price = float(breed_price.base_price)
        except BreedServiceMapping.DoesNotExist:
            base_price = float(service.price)

        for sample in sample_weights:
            weight_surcharge = 0.0
            if not service.exempt_from_surcharge:
                weight_surcharge = float(breed.calculate_weight_surcharge(sample['weight']))
            final_price = base_price + weight_surcharge
            pricing_matrix[service.id][sample['key']] = {
                'base_price': base_price,
                'weight_surcharge': weight_surcharge,
                'final_price': final_price
            }

    return render(request, 'mainapp/pricing/pricing_preview_modal.html', {
        'breed': breed,
        'services': services,
        'sample_weights': sample_weights,
        'pricing_matrix': pricing_matrix,
    })


@admin_required
def breed_cloning_wizard_modal(request):
    existing_breeds = Breed.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/pricing/breed_cloning_wizard_modal.html', {'existing_breeds': existing_breeds})


@admin_required
def export_pricing_config(request):
    import json
    from django.http import HttpResponse

    config = {
        'breeds': [],
        'services': [],
        'breed_prices': [],
    }

    for breed in Breed.objects.all():
        config['breeds'].append({
            'name': breed.name,
            'base_price': str(breed.base_price) if breed.base_price else None,
            'typical_weight_min': str(breed.typical_weight_min) if breed.typical_weight_min else None,
            'typical_weight_max': str(breed.typical_weight_max) if breed.typical_weight_max else None,
            'start_weight': str(breed.start_weight) if breed.start_weight else None,
            'weight_range_amount': str(breed.weight_range_amount) if breed.weight_range_amount else None,
            'weight_price_amount': str(breed.weight_price_amount) if breed.weight_price_amount else None,
            'breed_pricing_complex': breed.breed_pricing_complex,
            'clone_note': breed.clone_note,
            'is_active': breed.is_active,
        })

    for service in Service.objects.all():
        config['services'].append({
            'name': service.name,
            'description': service.description,
            'price': str(service.price),
            'pricing_type': service.pricing_type,
            'duration_minutes': service.duration_minutes,
            'is_active': service.is_active,
            'exempt_from_surcharge': service.exempt_from_surcharge,
        })

    for bp in BreedServiceMapping.objects.all():
        config['breed_prices'].append({
            'service': bp.service.name,
            'breed': bp.breed.name,
            'base_price': str(bp.base_price),
            'is_available': bp.is_available,
        })

    response = HttpResponse(
        json.dumps(config, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="pricing_config.json"'
    return response


@require_http_methods(["POST"])
@admin_required
def import_pricing_config(request):
    import json
    data = json.loads(request.FILES.get('config_file').read().decode('utf-8'))

    results = {
        'success': True,
        'message': '',
        'details': {
            'services_created': 0,
            'breeds_created': 0,
            'breed_prices_created': 0,
            'errors': []
        }
    }

    try:
        for service_data in data.get('services', []):
            try:
                service_name = service_data['name']
                Service.objects.update_or_create(
                    name=service_name,
                    defaults=service_data
                )
                results['details']['services_created'] += 1
            except Exception as e:
                results['details']['errors'].append(f"Failed to import service {service_data['name']}: {str(e)}")

        for breed_data in data.get('breeds', []):
            try:
                breed_name = breed_data['name']
                Breed.objects.update_or_create(
                    name=breed_name,
                    defaults=breed_data
                )
                results['details']['breeds_created'] += 1
            except Exception as e:
                results['details']['errors'].append(f"Failed to import breed {breed_data['name']}: {str(e)}")

        for price_data in data.get('breed_prices', []):
            try:
                service = Service.objects.get(name=price_data['service'])
                breed = Breed.objects.get(name=price_data['breed'])
                BreedServiceMapping.objects.update_or_create(
                    service=service,
                    breed=breed,
                    defaults={'base_price': price_data['base_price'], 'is_available': price_data.get('is_available', True)}
                )
                results['details']['breed_prices_created'] += 1
            except Exception as e:
                results['details']['errors'].append(f"Failed to import breed price: {str(e)}")

        results['message'] = 'Import completed successfully'
        return JsonResponse(results)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }, status=500)


@admin_required
def time_slot_editor_modal(request):
    date_str = request.GET.get('date')
    day_name = request.GET.get('day_name')
    if date_str and not day_name:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = dt.strftime('%A')
        except ValueError:
            day_name = ''
    return render(request, 'mainapp/schedule_modal.html', {'date': date_str, 'day_name': day_name})


@login_required
def auth_test(request):
    from django.http import JsonResponse
    return JsonResponse({
        'authenticated': True,
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff,
        'is_authenticated': request.user.is_authenticated,
    })


def custom_login(request):
    from django.contrib.auth import authenticate, login
    from django.contrib.auth.forms import AuthenticationForm
    from django.contrib.messages import add_message, constants

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                user_type = getattr(user, 'user_type', None)

                next_page = request.POST.get('next', request.GET.get('next', ''))

                if next_page:
                    return redirect(next_page)

                if user_type == 'admin':
                    return redirect('admin_landing')
                elif user_type == 'groomer':
                    return redirect('groomer_landing')
                else:
                    return redirect('customer_landing')
            else:
                pass
        else:
            pass
    else:
        form = AuthenticationForm()

    return render(request, 'mainapp/login.html', {'form': form})


def custom_logout(request):
    from django.contrib.auth import logout
    from django.contrib.messages import add_message, constants

    logout(request)
    add_message(request, constants.SUCCESS, 'You have been logged out successfully.')
    return redirect('custom_login')


def customer_sign_up(request: HttpRequest) -> HttpResponse:
    """Customer registration page.

    Allows new customers to create an account by providing:
    - Username
    - Email
    - Password
    - Phone number
    - Full name
    """
    from django.contrib.auth.forms import UserCreationForm
    from django.contrib.messages import add_message, constants

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        phone = request.POST.get('phone')
        full_name = request.POST.get('full_name')

        errors = []

        if not username:
            errors.append('Username is required')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already taken')

        if not email:
            errors.append('Email is required')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered')

        if not password:
            errors.append('Password is required')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters')

        if password != password_confirm:
            errors.append('Passwords do not match')

        if not full_name:
            errors.append('Full name is required')

        if errors:
            for error in errors:
                add_message(request, constants.ERROR, error)
            return render(request, 'mainapp/customer_sign_up.html', {
                'username': username,
                'email': email,
                'phone': phone,
                'full_name': full_name,
            })

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name.split()[0] if full_name else '',
                last_name=' '.join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else '',
                phone=phone,
                user_type='customer',
                is_active=True
            )
            from django.contrib.auth import login
            backend = 'mainapp.backends.UserProfileBackend'
            login(request, user, backend=backend)
            add_message(request, constants.SUCCESS, 'Account created successfully!')
            return redirect('customer_landing')
        except Exception as e:
            add_message(request, constants.ERROR, f'Error creating account: {str(e)}')
            return render(request, 'mainapp/customer_sign_up.html', {
                'username': username,
                'email': email,
                'phone': phone,
                'full_name': full_name,
            })

    return render(request, 'mainapp/customer_sign_up.html')


@login_required
def customer_profile(request: HttpRequest) -> HttpResponse:
    """Customer profile page for viewing and editing account details.

    Displays customer information including:
    - Username, email, phone
    - Booking history
    - Account settings

    Allows updating profile information.
    """
    from django.contrib.messages import add_message, constants

    user = request.user

    if user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        errors = []

        has_changes = False

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                errors.append('Email already registered')
            else:
                user.email = email
                has_changes = True

        if phone is not None:
            user.phone = phone
            has_changes = True

        if full_name:
            name_parts = full_name.split()
            user.first_name = name_parts[0] if name_parts else ''
            user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            has_changes = True

        if password:
            if len(password) < 8:
                errors.append('Password must be at least 8 characters')
            elif password != password_confirm:
                errors.append('Passwords do not match')
            else:
                user.set_password(password)
                has_changes = True

        if errors:
            for error in errors:
                add_message(request, constants.ERROR, error)
            return render(request, 'mainapp/customer_profile.html', {
                'user': user,
                'customer_appointments': Appointment.objects.filter(
                    customer__email=user.email
                ).order_by('-date', '-time'),
            })
        elif has_changes:
            user.save()
            add_message(request, constants.SUCCESS, 'Profile updated successfully!')
            if password:
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

        return redirect('customer_profile')

    customer_appointments = Appointment.objects.filter(
        customer__email=user.email
    ).order_by('-date', '-time')

    breeds = Breed.objects.filter(is_active=True).order_by('name')

    context = {
        'user': user,
        'customer_appointments': customer_appointments,
        'breeds': breeds,
    }
    return render(request, 'mainapp/customer_profile.html', context)


@login_required
def add_dog_modal(request: HttpRequest) -> HttpResponse:
    """Render the add dog modal."""
    from django.contrib.messages import add_message, constants

    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    breeds = Breed.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/add_dog_modal.html', {'breeds': breeds})


@login_required
def edit_dog_modal(request: HttpRequest, dog_id: int) -> HttpResponse:
    """Render the edit dog modal."""
    from django.contrib.messages import add_message, constants

    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    breeds = Breed.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/edit_dog_modal.html', {'dog': dog, 'breeds': breeds})


@login_required
def add_dog(request: HttpRequest) -> HttpResponse:
    """Add a new dog profile for the customer."""
    from django.contrib.messages import add_message, constants
    from django.core.validators import MinValueValidator

    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    if request.method == 'POST':
        name = request.POST.get('dog_name')
        breed_id = request.POST.get('breed_id')
        weight = request.POST.get('weight')
        age = request.POST.get('dog_age')
        notes = request.POST.get('notes')

        errors = []

        if not name:
            errors.append('Dog name is required')

        if breed_id and breed_id != '':
            try:
                breed = Breed.objects.get(id=int(breed_id))
            except Breed.DoesNotExist:
                errors.append('Invalid breed selected')
        else:
            breed = None

        if weight:
            try:
                weight = Decimal(weight)
                if weight <= 0:
                    errors.append('Weight must be greater than 0')
            except:
                errors.append('Invalid weight value')
        else:
            weight = None

        if errors:
            for error in errors:
                add_message(request, constants.ERROR, error)
        else:
            Dog.objects.create(
                name=name,
                owner=request.user,
                breed=breed,
                weight=weight,
                age=age,
                notes=notes
            )
            add_message(request, constants.SUCCESS, 'Dog profile added successfully!')

    return redirect('customer_profile')


@login_required
def edit_dog(request: HttpRequest, dog_id: int) -> HttpResponse:
    """Edit an exiting dog profile."""
    from django.contrib.messages import add_message, constants

    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    if request.method == 'POST':
        name = request.POST.get('dog_name')
        breed_id = request.POST.get('breed_id')
        weight = request.POST.get('weight')
        age = request.POST.get('dog_age')
        notes = request.POST.get('notes')

        errors = []

        if not name:
            errors.append('Dog name is required')

        if breed_id and breed_id != '':
            try:
                breed = Breed.objects.get(id=int(breed_id))
            except Breed.DoesNotExist:
                errors.append('Invalid breed selected')
        else:
            breed = None

        if weight:
            try:
                weight = Decimal(weight)
                if weight <= 0:
                    errors.append('Weight must be greater than 0')
            except:
                errors.append('Invalid weight value')
        else:
            weight = None

        if errors:
            for error in errors:
                add_message(request, constants.ERROR, error)
        else:
            dog.name = name
            dog.breed = breed
            dog.weight = weight
            dog.age = age
            dog.notes = notes
            dog.save()
            add_message(request, constants.SUCCESS, 'Dog profile updated successfully!')

    return redirect('customer_profile')


@login_required
def delete_dog(request: HttpRequest, dog_id: int) -> HttpResponse:
    """Delete a dog profile."""
    from django.contrib.messages import add_message, constants

    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
        dog.delete()
        add_message(request, constants.SUCCESS, 'Dog profile deleted successfully!')
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')

    return redirect('customer_profile')


@login_required
def request_dog_deletion_modal(request: HttpRequest, dog_id: int) -> HttpResponse:
    """Render the request dog deletion modal."""
    from django.contrib.messages import add_message, constants

    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    return render(request, 'mainapp/request_dog_deletion_modal.html', {'dog': dog})


@login_required
def request_dog_deletion(request: HttpRequest, dog_id: int) -> HttpResponse:
    """Submit a dog deletion request."""
    from django.contrib.messages import add_message, constants

    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    if request.method != 'POST':
        return redirect('customer_profile')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    reason = request.POST.get('reason', '').strip()
    if not reason:
        add_message(request, constants.ERROR, 'Please provide a reason for the deletion request.')
        return redirect('customer_profile')

    DogDeletionRequest.objects.create(
        dog=dog,
        requested_by=request.user,
        reason=reason,
        status='pending'
    )

    add_message(request, constants.SUCCESS,
                'Your deletion request has been submitted. Our team will review it and get back to you.')
    return redirect('customer_profile')


@require_http_methods(["GET"])
def book_with_dog(request: HttpRequest, dog_id: int) -> HttpResponse:
    """Render the booking modal with preloaded dog and customer data."""
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


@csrf_exempt
@admin_required
def render_groomer_options(request: HttpRequest) -> HttpResponse:
    """
    Render groomer options HTML for HTMX.
    Returns partial HTML for groomer select dropdown.
    """
    groomers = Groomer.objects.filter(is_active=True).order_by('name')
    context = {'groomers': groomers}
    return render(request, 'mainapp/partials/groomer_options.html', context)


@csrf_exempt
@admin_required
def render_time_slots(request: HttpRequest) -> HttpResponse:
    """
    Render time slots HTML for HTMX.
    Returns partial HTML for existing time slots list.
    If groomer_id is empty or 'all', shows time slots for all groomers.
    """
    groomer_id = request.GET.get('groomer_id', '').strip()
    date_str = request.GET.get('date')

    if not date_str:
        return HttpResponse('Missing date parameter', status=400)

    booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Handle "All Groomers" case (empty groomer_id or 'all')
    if not groomer_id or groomer_id == 'all':
        time_slots = TimeSlot.objects.filter(
            date=booking_date
        ).select_related('groomer').order_by('groomer__name', 'start_time')
    else:
        groomer = get_object_or_404(Groomer, id=int(groomer_id))
        time_slots = TimeSlot.objects.filter(
            groomer=groomer,
            date=booking_date
        ).order_by('start_time')

    def format_time_display(time_obj):
        """Format time in 12-hour format without leading zero. More portable than strftime with modifiers."""
        hour = time_obj.hour
        period = 'AM' if hour < 12 else 'PM'
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f'{hour_12}:{time_obj.strftime("%M")} {period}'

    slots = []
    for slot in time_slots:
        slot_data = {
            'id': slot.id,
            'start': slot.start_time.strftime('%H:%M'),
            'end': slot.end_time.strftime('%H:%M'),
            'start_display': format_time_display(slot.start_time),
            'end_display': format_time_display(slot.end_time)
        }
        # Include groomer name for "All Groomers" view
        if not groomer_id or groomer_id == 'all':
            slot_data['groomer_name'] = slot.groomer.name
        slots.append(slot_data)

    context = {'slots': slots, 'show_groomer': not groomer_id or groomer_id == 'all'}
    return render(request, 'mainapp/partials/time_slots_list.html', context)



