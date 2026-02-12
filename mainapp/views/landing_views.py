"""Landing page views for admin, customer, and groomer."""

from collections import defaultdict

from datetime import date, timedelta

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from mainapp.models import Appointment, Service, SiteConfig
from mainapp.logging_utils import get_view_logger
from mainapp.utils import admin_required, groomer_required


@admin_required
def admin_landing(request: HttpRequest) -> HttpResponse:
    """
    Admin dashboard landing page.

    Displays:
    - Dashboard statistics (today's appointments, pending appointments, revenue)
    - Today's appointment schedule
    - Quick action cards for common admin tasks
    """
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
            'page_url': 'pricing_management',
            'bg_color': 'bg-teal-100',
            'hover_color': 'group-hover:bg-teal-200',
            'text_color': 'text-teal-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>',
            'title': 'Pricing Management',
            'description': 'Manage breeds, base prices, and weight-based pricing'
        },
        {
            'modal_url': 'appointments_modal',
            'bg_color': 'bg-cyan-100',
            'hover_color': 'group-hover:bg-cyan-200',
            'text_color': 'text-cyan-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>',
            'title': 'View Appointments',
            'description': 'See upcoming, current, and past appointments'
        },
        {
            'modal_url': 'customers_modal',
            'bg_color': 'bg-emerald-100',
            'hover_color': 'group-hover:bg-emerald-200',
            'text_color': 'text-emerald-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>',
            'title': 'Customer Database',
            'description': 'Access and manage customer information'
        },
        {
            'modal_url': 'groomers_management_modal',
            'bg_color': 'bg-sky-100',
            'hover_color': 'group-hover:bg-sky-200',
            'text_color': 'text-sky-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>',
            'title': 'Manage Groomers',
            'description': 'Add, edit, or deactivate team members'
        },
        {
            'modal_url': 'site_config_modal',
            'bg_color': 'bg-indigo-100',
            'hover_color': 'group-hover:bg-indigo-200',
            'text_color': 'text-indigo-600',
            'svg_icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>',
            'title': 'Site Configuration',
            'description': 'Edit business hours, contact info, and business details'
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
    """
    Customer landing page with dynamic pricing and business hours.

    Displays:
    - Preview of available services (limited to 4)
    - Site configuration including business hours and contact info
    """
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
    """
    Groomer dashboard landing page.

    Displays:
    - All upcoming appointments for the groomer
    - Ordered by date and time
    """
    today = date.today()
    groomer_appointments = Appointment.objects.filter(
        date__gte=today
    ).order_by('date', 'time')

    context = {
        'groomer_appointments': groomer_appointments,
    }
    return render(request, 'mainapp/groomer_landing.html', context)


@admin_required
def appointments_modal(request: HttpRequest) -> HttpResponse:
    """
    Admin modal for viewing appointments.

    Displays:
    - Weekly calendar view of appointments
    - Ability to navigate between weeks
    - Grouped by date
    """
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
