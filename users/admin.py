"""
Admin configuration for the User model.

This module provides a custom admin interface for managing user accounts.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model with enhanced organization."""

    list_display = ('username', 'email', 'user_type', 'phone', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ['-date_joined', 'username']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal Information'), {
            'fields': (('first_name', 'last_name'), 'email', 'phone', 'user_type')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important Dates'), {
            'fields': (('last_login', 'date_joined'),),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'user_type', 'phone', 'first_name', 'last_name'
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make username readonly for existing users."""
        if obj:
            return self.readonly_fields + ['username']
        return self.readonly_fields
