"""
Models module for the users application.

This module contains the custom User model that extends Django's AbstractUser.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    """Custom user model inheriting from AbstractUser with additional profile fields.

    This model extends Django's built-in User model with:
    - user_type: To distinguish between admin, groomer, and customer roles
    - phone: Contact information for the user
    """

    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('groomer', 'Groomer'),
        ('customer', 'Customer'),
    ]

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='customer',
        help_text="Type of user account"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in the format: +1234567890 or 1234567890. Up to 15 digits allowed.'
            )
        ],
        help_text="User's phone number"
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
