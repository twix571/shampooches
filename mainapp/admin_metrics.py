"""
Admin Metrics Service Module

This module provides KPI (Key Performance Indicator) calculations
for the groomer salon admin dashboard. Metrics are optimized for the
admin landing page display and minimize unnecessary database queries.

Calculated Metrics:
- Revenue: Weekly revenue, monthly revenue
- Appointments: Today's appointments, pending appointments
- Customers: Active customer count
- Alerts: Pending confirmations, upcoming unconfirmed appointments
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict

from django.db.models import Sum, Count
from django.db.models.functions import Coalesce

from .models import Appointment, Customer

logger = logging.getLogger(__name__)


class MetricsError(Exception):
    """Custom exception for metrics calculation errors."""
    pass


def calculate_all_dashboard_metrics() -> Dict:
    """
    Calculate all dashboard metrics in a single optimized query batch.

    This function aggregates all KPI calculations needed for the admin dashboard,
    minimizing database queries for optimal performance.

    Returns:
        Dict: Complete dashboard metrics with the following structure:
            - revenue: Revenue metrics (weekly, monthly)
            - appointments: Appointment metrics (today, pending)
            - customers: Customer metrics (active)
            - alerts: Warning/alert indicators (pending confirmations)
    """
    try:
        today = date.today()
        start_of_month = today.replace(day=1)

        # Calculate all metrics with optimized queries
        metrics = {
            'revenue': _calculate_revenue_metrics(today, start_of_month),
            'appointments': _calculate_appointment_metrics(today, start_of_month),
            'customers': _calculate_customer_metrics(today, start_of_month),
            'alerts': _calculate_alert_metrics(),
        }

        logger.info(f'Calculated all dashboard metrics for {today}')
        return metrics

    except Exception as e:
        logger.error(f'Error calculating dashboard metrics: {str(e)}', exc_info=True)
        raise MetricsError(f'Failed to calculate dashboard metrics: {str(e)}')


def _calculate_revenue_metrics(today: date, start_of_month: date) -> Dict[str, float]:
    """
    Calculate revenue-related KPIs.

    Metrics:
    - weekly_revenue: Confirmed/completed appointments this week (Monday to today)
    - monthly_revenue: Completed appointments this month

    Args:
        today: Current date
        start_of_month: First day of current month

    Returns:
        Dict: Revenue metrics
    """
    # Weekly revenue (confirmed/completed appointments Monday to today)
    start_of_week = today - timedelta(days=today.weekday())
    weekly_revenue = Appointment.objects.filter(
        date__gte=start_of_week,
        date__lte=today,
        status__in=['confirmed', 'completed']
    ).aggregate(
        total=Coalesce(Sum('price_at_booking'), Decimal('0'))
    )['total']

    # Monthly revenue (completed appointments this month)
    monthly_revenue = Appointment.objects.filter(
        date__gte=start_of_month,
        date__lte=today,
        status='completed'
    ).aggregate(
        total=Coalesce(Sum('price_at_booking'), Decimal('0'))
    )['total']

    return {
        'weekly_revenue': float(weekly_revenue),
        'monthly_revenue': float(monthly_revenue),
    }


def _calculate_appointment_metrics(today: date, start_of_month: date) -> Dict[str, float]:
    """
    Calculate appointment-related KPIs.

    Metrics:
    - today_appointments: Count of appointments scheduled today
    - pending_appointments: Count of pending bookings needing confirmation

    Args:
        today: Current date
        start_of_month: First day of current month

    Returns:
        Dict: Appointment metrics
    """
    # Today's appointments
    today_appointments = Appointment.objects.filter(date=today).count()

    # Pending appointments
    pending_appointments = Appointment.objects.filter(status='pending').count()

    return {
        'today_appointments': float(today_appointments),
        'pending_appointments': float(pending_appointments),
    }


def _calculate_customer_metrics(today: date, start_of_month: date) -> Dict[str, float]:
    """
    Calculate customer-related KPIs.

    Metrics:
    - active_customers: Number of customers with at least one appointment

    Args:
        today: Current date
        start_of_month: First day of current month

    Returns:
        Dict: Customer metrics
    """
    # Active customers (customers with at least one appointment)
    active_customers = Customer.objects.filter(
        appointments__isnull=False
    ).distinct().count()

    return {
        'active_customers': float(active_customers),
    }





def _calculate_alert_metrics() -> Dict:
    """
    Calculate alert/warning indicators for the dashboard.

    Metrics:
    - pending_confirmations: Count of pending appointments needing confirmation
    - upcoming_unconfirmed: Unconfirmed appointments in next 7 days
    - has_alerts: Boolean indicating if any alerts exist

    Returns:
        Dict: Alert metrics
    """
    # Pending confirmations
    pending_confirmations = Appointment.objects.filter(status='pending').count()

    # Upcoming unconfirmed (next 7 days)
    today = date.today()
    week_ahead = today + timedelta(days=7)

    upcoming_unconfirmed = Appointment.objects.filter(
        date__gte=today,
        date__lte=week_ahead,
        status='pending'
    ).count()

    return {
        'pending_confirmations': pending_confirmations,
        'upcoming_unconfirmed': upcoming_unconfirmed,
        'has_alerts': pending_confirmations > 0 or upcoming_unconfirmed > 0,
    }


def get_quick_stats() -> Dict[str, float]:
    """
    Get quick, lightweight stats for dashboard header or notifications.

    This function is optimized for speed and should be called frequently
    for real-time updates without heavy database load.

    Returns:
        Dict: Quick stats (today's revenue, appointments, pending actions)
    """
    today = date.today()

    today_rev = Appointment.objects.filter(
        date=today,
        status__in=['confirmed', 'completed']
    ).aggregate(
        total=Coalesce(Sum('price_at_booking'), Decimal('0'))
    )['total']

    today_appts = Appointment.objects.filter(date=today).count()
    pending = Appointment.objects.filter(status='pending').count()

    return {
        'today_revenue': float(today_rev),
        'today_appointments': float(today_appts),
        'pending_actions': float(pending),
    }
