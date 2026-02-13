"""
Django signals for mainapp.

This module contains signal handlers that respond to model changes,
particularly for sending email notifications when appointments are created
or their status changes.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from threading import local

from .models import Appointment, SiteConfig

logger = logging.getLogger(__name__)

# Thread-local storage for tracking old status in pre_save
_thread_local = local()


@receiver(pre_save, sender=Appointment)
def track_appointment_status_change(sender, instance, **kwargs):
    """Track the old status before an appointment is saved.

    This handler stores the old status in thread-local storage so that
    post_save can detect status transitions.

    Args:
        sender: The model class (Appointment)
        instance: The Appointment instance being saved
        **kwargs: Additional signal arguments
    """
    if instance.pk:
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            _thread_local.old_status = old_instance.status
        except Appointment.DoesNotExist:
            _thread_local.old_status = None
    else:
        _thread_local.old_status = None


@receiver(post_save, sender=Appointment)
def send_appointment_notification_email(sender, instance, created, **kwargs):
    """Send appropriate email notification based on appointment status changes.

    This signal handler triggers email notifications to the customer when:
    - A new appointment is created with pending status
    - An appointment status changes (confirmed, cancelled, etc.)

    Args:
        sender: The model class (Appointment)
        instance: The Appointment instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    # Get the old status from thread-local storage
    old_status = getattr(_thread_local, 'old_status', None)
    new_status = instance.status

    # Get customer email from the appointment
    customer_email = instance.customer.email
    if not customer_email:
        logger.warning(f"Cannot send email for appointment {instance.id}: no customer email")
        return

    # Get site configuration for business info
    site_config = SiteConfig.get_active_config()
    if not site_config:
        logger.warning("No active site configuration found for email template")
        site_config = None

    # Handle new pending appointments
    if created and new_status == 'pending':
        transaction.on_commit(lambda: _send_email(
            appointment=instance,
            site_config=site_config,
            email_type='confirmation'
        ))
        return

    # Handle status transitions
    if old_status and old_status != new_status:
        # Pending -> Confirmed
        if old_status == 'pending' and new_status == 'confirmed':
            transaction.on_commit(lambda: _send_email(
                appointment=instance,
                site_config=site_config,
                email_type='confirmed'
            ))
        # Any status -> Cancelled
        elif new_status == 'cancelled':
            transaction.on_commit(lambda: _send_email(
                appointment=instance,
                site_config=site_config,
                email_type='cancelled'
            ))


def _send_email(appointment, site_config, email_type):
    """Send email notification for an appointment.

    Args:
        appointment: Appointment instance
        site_config: SiteConfig instance (optional)
        email_type: Type of email ('confirmation', 'confirmed', or 'cancelled')
    """
    subject_map = {
        'confirmation': 'Appointment Confirmation',
        'confirmed': 'Appointment Confirmed',
        'cancelled': 'Appointment Cancelled'
    }

    email_builder_map = {
        'confirmation': _build_confirmation_email,
        'confirmed': _build_confirmed_email,
        'cancelled': _build_cancelled_email
    }

    subject = subject_map.get(email_type, 'Appointment Update')
    message = email_builder_map[email_type](appointment, site_config)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@shampooches.com'),
            recipient_list=[appointment.customer.email],
            fail_silently=False,
        )
        logger.info(f"Appointment {email_type} email sent for appointment {appointment.id}")
    except Exception as e:
        logger.error(f"Failed to send appointment {email_type} email: {e}")


def _build_confirmation_email(appointment, site_config):
    """Build plain text email content for appointment confirmation.

    Args:
        appointment: Appointment instance
        site_config: SiteConfig instance (optional)

    Returns:
        str: Plain text email content
    """
    business_name = site_config.business_name if site_config else 'Shampooches'
    business_phone = site_config.phone if site_config else ''

    lines = [
        f"Thank you for booking your appointment with {business_name}!",
        "",
        "Appointment Details:",
        f"  Pet: {appointment.dog_name}",
        f"  Service: {appointment.service.name}",
        f"  Date: {appointment.date.strftime('%A, %B %d, %Y')}",
        f"  Time: {appointment.time.strftime('%I:%M %p')}",
        f"  Price: ${appointment.price_at_booking or 'To be confirmed'}",
        "",
        "Your appointment is pending confirmation.",
        "We will contact you shortly to confirm and finalize the details.",
        "",
    ]

    if business_phone:
        lines.extend([
            f"If you need to reschedule or have questions, please call us at: {business_phone}",
            "",
        ])

    lines.extend([
        "We look forward to seeing you and your furry friend!",
        "",
        f"The {business_name} Team",
    ])

    return "\n".join(lines)


def _build_confirmed_email(appointment, site_config):
    """Build plain text email content for appointment confirmation.

    Args:
        appointment: Appointment instance
        site_config: SiteConfig instance (optional)

    Returns:
        str: Plain text email content
    """
    business_name = site_config.business_name if site_config else 'Shampooches'
    business_phone = site_config.phone if site_config else ''

    lines = [
        f"Great news! Your appointment with {business_name} has been confirmed.",
        "",
        "Appointment Details:",
        f"  Pet: {appointment.dog_name}",
        f"  Service: {appointment.service.name}",
        f"  Date: {appointment.date.strftime('%A, %B %d, %Y')}",
        f"  Time: {appointment.time.strftime('%I:%M %p')}",
        f"  Price: ${appointment.price_at_booking or 'To be confirmed'}",
        "",
    ]

    if business_phone:
        lines.extend([
            f"If you need to reschedule or have questions, please call us at: {business_phone}",
            "",
        ])

    lines.extend([
        "We look forward to seeing you and your furry friend!",
        "",
        f"The {business_name} Team",
    ])

    return "\n".join(lines)


def _build_cancelled_email(appointment, site_config):
    """Build plain text email content for appointment cancellation.

    Args:
        appointment: Appointment instance
        site_config: SiteConfig instance (optional)

    Returns:
        str: Plain text email content
    """
    business_name = site_config.business_name if site_config else 'Shampooches'
    business_phone = site_config.phone if site_config else ''

    lines = [
        f"Your appointment with {business_name} has been cancelled.",
        "",
        "Cancelled Appointment Details:",
        f"  Pet: {appointment.dog_name}",
        f"  Service: {appointment.service.name}",
        f"  Date: {appointment.date.strftime('%A, %B %d, %Y')}",
        f"  Time: {appointment.time.strftime('%I:%M %p')}",
        "",
    ]

    if business_phone:
        lines.extend([
            f"If you would like to reschedule or have any questions, please call us at: {business_phone}",
            "",
        ])

    lines.extend([
        "We hope to see you and your furry friend again soon!",
        "",
        f"The {business_name} Team",
    ])

    return "\n".join(lines)
