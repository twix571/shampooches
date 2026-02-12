"""
Test script to verify that all Factory Boy factories work correctly.

This script creates instances of all factories to ensure they're properly configured.
Run with: python manage.py shell < test_factories.py
Or execute this file directly after setting up Django.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from mainapp.tests.factories import (
    BreedFactory,
    WeightRangeFactory,
    WeightRangeTemplateFactory,
    BreedServiceMappingFactory,
    BreedWeightSurchargeFactory,
    ServiceFactory,
    CustomerFactory,
    AppointmentFactory,
    GroomerFactory,
    TimeSlotFactory,
    DogFactory,
)
from users.tests.factories import UserFactory, CustomerUserFactory
from django.core.management import call_command

print("Testing Factory Boy factories...\n")

# Test User factory
print("1. Creating User...")
user = CustomerUserFactory()
print(f"   ✓ User created: {user.username} ({user.email})")

# Test Breed factory
print("\n2. Creating Breed...")
breed = BreedFactory()
print(f"   ✓ Breed created: {breed.name} (base price: ${breed.base_price})")

# Test WeightRange factory
print("\n3. Creating WeightRange...")
weight_range = WeightRangeFactory()
print(f"   ✓ WeightRange created: {weight_range.name} ({weight_range.min_weight}-{weight_range.max_weight} lbs)")

# Test WeightRangeTemplate factory
print("\n4. Creating WeightRangeTemplate...")
template = WeightRangeTemplateFactory()
print(f"   ✓ WeightRangeTemplate created: {template.name}")

# Test Service factory
print("\n5. Creating Service...")
service = ServiceFactory()
print(f"   ✓ Service created: {service.name} (${service.price})")

# Test BreedServiceMapping factory
print("\n6. Creating BreedServiceMapping...")
mapping = BreedServiceMappingFactory(breed=breed, service=service)
print(f"   ✓ BreedServiceMapping created: {mapping}")

# Test BreedWeightSurcharge factory
print("\n7. Creating BreedWeightSurcharge...")
surcharge = BreedWeightSurchargeFactory(breed=breed, weight_range=weight_range)
print(f"   ✓ BreedWeightSurcharge created: +${surcharge.surcharge_amount}")

# Test Customer factory
print("\n8. Creating Customer...")
customer = CustomerFactory()
print(f"   ✓ Customer created: {customer.name} ({customer.email})")

# Test Groomer factory
print("\n9. Creating Groomer...")
groomer = GroomerFactory()
print(f"   ✓ Groomer created: {groomer.name}")

# Test TimeSlot factory
print("\n10. Creating TimeSlot...")
time_slot = TimeSlotFactory(groomer=groomer)
print(f"   ✓ TimeSlot created: {time_slot}")

# Test Appointment factory
print("\n11. Creating Appointment...")
appointment = AppointmentFactory(customer=customer, groomer=groomer, service=service, dog_breed=breed)
print(f"   ✓ Appointment created: {appointment}")

# Test Dog factory
print("\n12. Creating Dog...")
dog = DogFactory(owner=user, breed=breed)
print(f"   ✓ Dog created: {dog.name} (owned by {user.username})")

print("\n" + "="*60)
print("All factories working correctly! ✓")
print("="*60)
print("\nYou can now use these factories in your tests:")
print("  from mainapp.tests.factories import BreedFactory, CustomerFactory, ...")
print("  from users.tests.factories import UserFactory, CustomerUserFactory, ...")
print("\nExample usage:")
print("  breed = BreedFactory()")
print("  customer = CustomerFactory(name='John Doe')")
print("  appointment = AppointmentFactory(customer=customer)")
