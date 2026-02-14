"""
Django signals for users app.

This module contains signal handlers for User model to automatically
set staff status based on user_type.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender='users.User')
def set_staff_status_by_user_type(sender, instance, **kwargs):
    """Automatically set staff status based on user_type.

    - admin users: is_staff=True, is_superuser=True
    - groomer_manager users: is_staff=True, is_superuser=False
    - groomer users: is_staff=True, is_superuser=False
    - customer users: is_staff=False, is_superuser=False

    This ensures groomers and groomer managers can access the admin dashboard
    without having full superuser privileges.
    """
    if instance.user_type == 'admin':
        instance.is_staff = True
        instance.is_superuser = True
    elif instance.user_type == 'groomer_manager':
        instance.is_staff = True
        instance.is_superuser = False
    elif instance.user_type == 'groomer':
        instance.is_staff = True
        instance.is_superuser = False
    elif instance.user_type == 'customer':
        instance.is_staff = False
        instance.is_superuser = False
