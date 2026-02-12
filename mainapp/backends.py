"""
Custom authentication backend for Shampooches.

This backend uses the custom User model (users.User) which includes
user_type and phone fields directly, eliminating the need for a
separate UserProfile model.
"""

# Standard library imports (none in this file)

# Third-party imports (none in this file)

# Django imports
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class UserProfileBackend(ModelBackend):
    """
    Custom authentication backend for the custom User model.

    The custom User model (users.User) already includes all necessary
    fields (user_type, phone) that were previously in UserProfile,
    so this backend provides standard Django authentication without
    needing profile management.
    """

    def get_user(self, user_id):
        """
        Retrieve user by ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with username and password.

        The custom User model includes all profile fields directly,
        so no separate profile creation is needed.
        """
        return super().authenticate(request, username=username, password=password, **kwargs)
