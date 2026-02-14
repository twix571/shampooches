"""
Factory Boy factories for the users application.

This module provides test data factories for the User model,
making it easy to create test instances with Faker-generated data.
"""

import factory
from factory import fuzzy

from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances.

    This factory creates custom User instances with realistic test data.
    The default user_type is 'customer', but this can be overridden.
    """

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda u: f"{u.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    user_type = fuzzy.FuzzyChoice(['admin', 'groomer_manager', 'groomer', 'customer'])
    phone = factory.Faker('phone_number')
    is_active = True


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""

    user_type = 'admin'
    is_staff = True
    is_superuser = True


class GroomerManagerUserFactory(UserFactory):
    """Factory for creating groomer manager users."""

    user_type = 'groomer_manager'
    is_staff = True


class GroomerUserFactory(UserFactory):
    """Factory for creating groomer users."""

    user_type = 'groomer'


class CustomerUserFactory(UserFactory):
    """Factory for creating customer users."""

    user_type = 'customer'
