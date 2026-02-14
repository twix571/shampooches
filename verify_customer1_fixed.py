import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from mainapp.models import Customer

User = get_user_model()

# Check all users and their Customer profiles
print('=== USERS AND CUSTOMER PROFILES ===')
for u in User.objects.all():
    print(f'\nUser: {u.username}, Type: {u.user_type}')
    has_profile = hasattr(u, 'customer_profile')
    print(f'  Has Customer Profile: {has_profile}')
    if has_profile:
        print(f'  Customer Profile: {u.customer_profile.name}')
    else:
        print('  No customer profile (ORPHANED)')

# Check all Customers and their User relationships
print('\n\n=== CUSTOMERS AND USERS ===')
for c in Customer.objects.all():
    print(f'\nCustomer ID: {c.id}, Name: {c.name}')
    print(f'  User: {c.user_id}')
    if c.user_id:
        print(f'  User username: {c.user.username}')
    else:
        print(f'  NO USER (ORPHANED)')
