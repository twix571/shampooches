"""Analyze database state for orphaned users."""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from mainapp.models import Customer

User = get_user_model()

print('=== DATABASE STATE ANALYSIS ===')
print(f'Total Users: {User.objects.count()}')

users_with_customer = User.objects.filter(customer_profile__isnull=False).count()
print(f'Users WITH Customer profile: {users_with_customer}')

users_without_customer = User.objects.exclude(customer_profile__isnull=False).count()
print(f'Users WITHOUT Customer profile: {users_without_customer}')

print('\n=== BREAKDOWN BY USER TYPE ===')
for user_type in ['admin', 'customer', 'groomer']:
    count = User.objects.filter(user_type=user_type).count()
    print(f'{user_type.upper()}: {count} users')

print('\n=== ORPHANED USERS (customer type without profile) ===')
orphaned = User.objects.filter(user_type='customer').exclude(customer_profile__isnull=False)
print(f'Count: {orphaned.count()}')
for user in orphaned:
    print(f'  - ID: {user.id}, Username: {user.username}, Email: {user.email}, Created: {user.date_journal}')

print('\n=== CUSTOMER RECORDS ===')
print(f'Total Customers: {Customer.objects.count()}')
for customer in Customer.objects.all():
    print(f'  - ID: {customer.id}, Name: {customer.name}, Email: {customer.email}, User: {customer.user_id}')
