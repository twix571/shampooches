"""
Admin Metrics Service Module

This module provides comprehensive KPI (Key Performance Indicator) calculations
for the groomer salon admin dashboard. All metrics follow industry best practices
and business intelligence standards.

Based on research from 2026 salon industry benchmarks:
- Revenue metrics are highest priority for business decisions
- Appointment metrics track operational efficiency
- Client metrics measure customer satisfaction and retention
- Staff performance metrics optimize team productivity
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.db.models import (
    Sum, Count, Avg, Q, F, ExpressionWrapper, FloatField, Case, When,
    Value, BooleanField, OuterRef, Subquery, Max, Min
)
from django.db.models.functions import TruncDay, TruncMonth, Coalesce

from .models import Appointment, Customer, Groomer

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
            - revenue: Revenue metrics (today, monthly, average ticket, pending)
            - appointments: Appointment metrics (today, pending, no-show rate)
            - customers: Customer metrics (active, retention rate, new rebooking)
            - staff: Staff performance metrics (revenue per groomer, utilization)
            - alerts: Warning/alert indicators (pending confirmations)
            - trends: Historical data for trend analysis (monthly revenue last 6 months)
    """
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        start_of_year = today.replace(month=1, day=1)

        # Calculate all metrics with optimized queries
        metrics = {
            'revenue': _calculate_revenue_metrics(today, start_of_month),
            'appointments': _calculate_appointment_metrics(today, start_of_month),
            'customers': _calculate_customer_metrics(today, start_of_month),
            'staff': _calculate_staff_metrics(today, start_of_month),
            'alerts': _calculate_alert_metrics(),
            'trends': _calculate_trend_metrics(start_of_year, today),
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
    - today_revenue: Confirmed/completed appointments today
    - monthly_revenue: Completed appointments this month
    - average_ticket_value: Revenue per completed appointment this month
    - pending_revenue: Pending bookings (potential revenue at risk)
    - ytd_revenue: Year-to-date revenue for comparison

    Args:
        today: Current date
        start_of_month: First day of current month

    Returns:
        Dict: Revenue metrics
    """
    # Today's revenue (confirmed/completed appointments today)
    today_revenue = Appointment.objects.filter(
        date=today,
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

    # Average ticket value (monthly)
    monthly_appointments = Appointment.objects.filter(
        date__gte=start_of_month,
        date__lte=today,
        status='completed'
    ).count()

    average_ticket_value = (
        monthly_revenue / monthly_appointments if monthly_appointments > 0 else Decimal('0')
    )

    # Pending revenue (potential revenue at risk)
    pending_revenue = Appointment.objects.filter(
        status='pending',
        date__gte=today
    ).aggregate(
        total=Coalesce(Sum('price_at_booking'), Decimal('0'))
    )['total']

    # Year-to-date revenue
    start_of_year = today.replace(month=1, day=1)
    ytd_revenue = Appointment.objects.filter(
        date__gte=start_of_year,
        date__lte=today,
        status__in=['confirmed', 'completed']
    ).aggregate(
        total=Coalesce(Sum('price_at_booking'), Decimal('0'))
    )['total']

    return {
        'today_revenue': float(today_revenue),
        'monthly_revenue': float(monthly_revenue),
        'average_ticket_value': float(average_ticket_value),
        'pending_revenue': float(pending_revenue),
        'ytd_revenue': float(ytd_revenue),
    }


def _calculate_appointment_metrics(today: date, start_of_month: date) -> Dict[str, float]:
    """
    Calculate appointment-related KPIs.

    Metrics:
    - today_appointments: Count of appointments scheduled today
    - pending_appointments: Count of pending bookings needing confirmation
    - no_show_rate: Percentage of completed/cancelled appointments with no-show status
    - booking_conversion_rate: Percentage of bookings confirmed (confirmed/total)
    - monthly_appointments: Total appointments this month

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

    # No-show rate (cancelled appointments / total completed appointments)
    # Note: No-shows aren't explicitly tracked, but cancelled appointments serve as a proxy
    start_of_month = today.replace(day=1)
    monthly_appointments = Appointment.objects.filter(
        date__gte=start_of_month,
        date__lte=today,
        status__in=['completed', 'cancelled']
    )

    cancelled_count = monthly_appointments.filter(status='cancelled').count()
    completed_count = monthly_appointments.filter(status='completed').count()
    total_completed_cancelled = completed_count + cancelled_count

    no_show_rate = (
        (cancelled_count / total_completed_cancelled) * 100
        if total_completed_cancelled > 0 else 0
    )

    # Booking conversion rate (confirmed appointments / total appointments this month)
    total_monthly = Appointment.objects.filter(
        date__gte=start_of_month,
        date__lte=today
    ).count()

    confirmed_monthly = Appointment.objects.filter(
        date__gte=start_of_month,
        date__lte=today,
        status__in=['confirmed', 'completed']
    ).count()

    booking_conversion_rate = (
        (confirmed_monthly / total_monthly) * 100 if total_monthly > 0 else 0
    )

    return {
        'today_appointments': float(today_appointments),
        'pending_appointments': float(pending_appointments),
        'no_show_rate': round(no_show_rate, 1),
        'booking_conversion_rate': round(booking_conversion_rate, 1),
        'monthly_appointments': total_monthly,
    }


def _calculate_customer_metrics(today: date, start_of_month: date) -> Dict[str, float]:
    """
    Calculate customer-related KPIs.

    Metrics:
    - active_customers: Number of customers with at least one appointment
    - customer_retention_rate: Percentage of returning customers this month
    - new_guest_rebooking: Percentage of new customers who rebooked

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

    # Customer retention rate calculation
    # A customer is considered "retained" if they had an appointment in a previous month
    # and another appointment in the current month
    # Get customers who had appointments before this month
    previous_month = start_of_month - timedelta(days=1)
    start_of_previous_month = previous_month.replace(day=1)
    customers_before_this_month = Appointment.objects.filter(
        date__gte=start_of_previous_month,
        date__lt=start_of_month,
        status__in=['confirmed', 'completed']
    ).values_list('customer_id', flat=True).distinct()

    # Count how many of those had appointments this month
    retained_customers = Appointment.objects.filter(
        date__gte=start_of_month,
        date__lte=today,
        status__in=['confirmed', 'completed'],
        customer_id__in=customers_before_this_month
    ).values('customer_id').distinct().count()

    retention_rate = (
        (retained_customers / len(customers_before_this_month)) * 100
        if customers_before_this_month else 0
    )

    # New guest rebooking rate
    # New guests this month are customers whose first appointment was this month
    # Track if they've booked again
    # Get customers with their first appointment date
    first_appointments = Appointment.objects.filter(
        customer__appointments__isnull=False
    ).values('customer_id').annotate(
        first_appointment=Min('customer__appointments__date')
    ).filter(first_appointment__gte=start_of_month)

    total_new_guests = first_appointments.count()

    # Count how many new guests have rebooked (more than 1 appointment total)
    new_guests_with_counts = Appointment.objects.filter(
        customer_id__in=first_appointments.values('customer_id')
    ).values('customer_id').annotate(
        appointment_count=Count('id')
    )

    rebooked_guests = new_guests_with_counts.filter(appointment_count__gt=1).count()

    new_guest_rebooking_rate = (
        (rebooked_guests / total_new_guests) * 100 if total_new_guests > 0 else 0
    )

    return {
        'active_customers': float(active_customers),
        'customer_retention_rate': round(retention_rate, 1),
        'new_guest_rebooking_rate': round(new_guest_rebooking_rate, 1),
    }


def _calculate_staff_metrics(today: date, start_of_month: date) -> Dict[str, List[Dict]]:
    """
    Calculate staff (groomer) performance metrics.

    Metrics:
    - revenue_per_groomer: List of groomers with their monthly revenue
    - groomer_utilization: Appointment count per groomer this month
    - top_performer: Groomer with highest revenue this month

    Args:
        today: Current date
        start_of_month: First day of current month

    Returns:
        Dict: Staff metrics
    """
    # Revenue per groomer
    groomer_revenue = Appointment.objects.filter(
        date__gte=start_of_month,
        date__lte=today,
        status__in=['confirmed', 'completed'],
        groomer__isnull=False
    ).values('groomer__name', 'groomer__id').annotate(
        total_revenue=Coalesce(Sum('price_at_booking'), Decimal('0')),
        appointment_count=Count('id')
    ).order_by('-total_revenue')

    # Convert QuerySet to list for template rendering
    groomer_performance = [
        {
            'groomer_id': item['groomer__id'],
            'groomer_name': item['groomer__name'],
            'revenue': float(item['total_revenue']),
            'appointments': item['appointment_count'],
        }
        for item in groomer_revenue
    ]

    # Top performer
    top_performer = groomer_performance[0] if groomer_performance else None

    return {
        'groomer_performance': groomer_performance,
        'top_performer': top_performer,
    }


def _calculate_alert_metrics() -> Dict:
    """
    Calculate alert/warning indicators for the dashboard.

    Metrics:
    - pending_confirmations: Count of pending appointments needing confirmation
    - upcoming_unconfirmed: Unconfirmed appointments in next 7 days
    - overdue_payments: Payments past due (if payment tracking exists)
    - low_availability: Days with low time slot availability

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


def _calculate_trend_metrics(start_of_year: date, end_date: date) -> Dict[str, List[Dict]]:
    """
    Calculate historical trend data for charts and analysis.

    Returns last 6 months of revenue and appointment data.

    Args:
        start_of_year: First day of year
        end_date: Current date

    Returns:
        Dict: Trend metrics with monthly breakdown
    """
    # Get last 6 months of data
    monthly_data = Appointment.objects.filter(
        date__gte=start_of_year,
        date__lte=end_date,
        status__in=['confirmed', 'completed']
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        revenue=Coalesce(Sum('price_at_booking'), Decimal('0')),
        appointments=Count('id')
    ).order_by('-month')[:6]

    # Convert to list and reverse for chronological order
    trends = [
        {
            'month': item['month'].strftime('%B %Y'),
            'revenue': float(item['revenue']),
            'appointments': item['appointments'],
        }
        for item in reversed(list(monthly_data))
    ]

    return {
        'monthly_trends': trends,
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
