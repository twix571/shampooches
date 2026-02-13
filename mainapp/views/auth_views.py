"""Authentication and health check views for the grooming salon application."""

import logging
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.messages import add_message, constants
from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from mainapp.logging_utils import get_view_logger
from mainapp.utils import admin_required, groomer_required

# Get module-level logger
logger = logging.getLogger(__name__)


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


def custom_login(request):
    """Custom login view with role-based redirect after successful authentication."""
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
    """Custom logout view with success message."""
    logout(request)
    add_message(request, constants.SUCCESS, 'You have been logged out successfully.')
    return redirect('custom_login')


def customer_sign_up(request: HttpRequest) -> HttpResponse:
    """
    Customer registration page.

    Allows new customers to create an account by providing:
    - Username
    - Email
    - Password
    - Phone number
    - Full name
    """
    User = __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model()

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

            # Create Customer profile linked to the User
            from mainapp.models import Customer
            Customer.objects.create(
                user=user,
                name=full_name,
                email=email,
                phone=phone
            )

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
def auth_test(request):
    """
    Test endpoint to verify authentication status and user roles.

    Returns:
        JsonResponse: Contains authentication status and user details
    """
    return JsonResponse({
        'authenticated': True,
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff,
        'is_authenticated': request.user.is_authenticated,
    })
