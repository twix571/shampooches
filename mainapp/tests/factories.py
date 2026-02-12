"""
Factory Boy factories for the mainapp application.

This module provides test data factories for all models in the mainapp,
making it easy to create test instances with Faker-generated data.
"""

import factory
from decimal import Decimal
from datetime import date, time, datetime
from django.utils import timezone

from mainapp.models import (
    Breed,
    BreedServiceMapping,
    Service,
    Customer,
    Appointment,
    Groomer,
    TimeSlot,
    Dog,
)


class BreedFactory(factory.django.DjangoModelFactory):
    """Factory for creating Breed instances."""

    class Meta:
        model = Breed

    name = factory.Sequence(lambda n: f"Breed {n}")
    base_price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    typical_weight_min = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    typical_weight_max = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    weight_range_amount = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    weight_price_amount = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    start_weight = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    breed_pricing_complex = False
    is_active = True





class ServiceFactory(factory.django.DjangoModelFactory):
    """Factory for creating Service instances."""

    class Meta:
        model = Service

    name = factory.Sequence(lambda n: f"Service {n}")
    description = factory.Faker('text', max_nb_chars=200)
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    pricing_type = factory.Iterator(['base_required', 'standalone'])
    duration_minutes = factory.Faker('random_int', min=30, max=180)
    is_active = True
    exempt_from_surcharge = False


class BreedServiceMappingFactory(factory.django.DjangoModelFactory):
    """Factory for creating BreedServiceMapping instances."""

    class Meta:
        model = BreedServiceMapping

    breed = factory.SubFactory(BreedFactory)
    service = factory.SubFactory(ServiceFactory)
    is_available = True
    base_price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)





class CustomerFactory(factory.django.DjangoModelFactory):
    """Factory for creating Customer instances."""

    class Meta:
        model = Customer

    name = factory.Faker('name')
    email = factory.Sequence(lambda n: f"customer{n}@example.com")
    phone = factory.Faker('phone_number')
    address = factory.Faker('address')


class GroomerFactory(factory.django.DjangoModelFactory):
    """Factory for creating Groomer instances."""

    class Meta:
        model = Groomer

    name = factory.Faker('name')
    bio = factory.Faker('text', max_nb_chars=300)
    specialties = factory.Faker('text', max_nb_chars=100)
    is_active = True
    order = factory.Sequence(lambda n: n)


class AppointmentFactory(factory.django.DjangoModelFactory):
    """Factory for creating Appointment instances."""

    class Meta:
        model = Appointment

    customer = factory.SubFactory(CustomerFactory)
    service = factory.SubFactory(ServiceFactory)
    groomer = factory.SubFactory(GroomerFactory)
    dog_name = factory.Faker('first_name')
    dog_breed = factory.SubFactory(BreedFactory)
    dog_size = factory.Iterator(['Small', 'Medium', 'Large'])
    dog_weight = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True, max_value=100)
    dog_age = factory.Faker('text', max_nb_chars=50)
    date = factory.LazyFunction(date.today)
    time = factory.LazyFunction(lambda: datetime.now().time().replace(minute=0, second=0, microsecond=0))
    status = factory.Iterator(['pending', 'confirmed', 'completed', 'cancelled'])
    notes = factory.Faker('text', max_nb_chars=200)
    price_at_booking = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)


class TimeSlotFactory(factory.django.DjangoModelFactory):
    """Factory for creating TimeSlot instances."""

    class Meta:
        model = TimeSlot

    groomer = factory.SubFactory(GroomerFactory)
    date = factory.LazyFunction(date.today)
    start_time = factory.LazyFunction(lambda: time(9, 0))
    end_time = factory.LazyFunction(lambda: time(10, 0))
    is_active = True


class DogFactory(factory.django.DjangoModelFactory):
    """Factory for creating Dog instances.

    Requires a User instance (from the users app) to be passed explicitly
    as the owner, since User is in a different app.
    """

    class Meta:
        model = Dog

    name = factory.Faker('first_name')
    breed = factory.SubFactory(BreedFactory)
    weight = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True, max_value=100)
    age = factory.Faker('text', max_nb_chars=50)
    notes = factory.Faker('text', max_nb_chars=200)


class ComplexBreedFactory(BreedFactory):
    """Factory for creating breeds with complex pricing rules."""

    breed_pricing_complex = True
    clone_note = factory.Faker('text', max_nb_chars=200)
    pricing_cloned_from = None


class StandaloneServiceFactory(ServiceFactory):
    """Factory for creating standalone services."""

    pricing_type = 'standalone'


class BaseRequiredServiceFactory(ServiceFactory):
    """Factory for creating base required services."""

    pricing_type = 'base_required'
