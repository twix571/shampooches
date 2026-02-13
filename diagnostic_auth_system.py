#!/usr/bin/env python
"""
Diagnostic script for the Authentication System

This script checks for:
1. User-Customer relationship integrity
2. Potential orphaned Users without Customer profiles
3. Admin users that may or may not have Customer profiles
4. Authentication backend configuration
5. Signal handlers for User->Customer synchronization

Run with: python diagnostic_auth_system.py
"""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model
from mainapp.models import Customer, Dog

User = get_user_model()

print("=" * 80)
print("AUTHENTICATION SYSTEM DIAGNOSTIC REPORT")
print("=" * 80)
print()

# 1. Check User-Customer relationship integrity
print("1. USER-CUSTOMER RELATIONSHIP INTEGRITY")
print("-" * 80)

total_users = User.objects.count()
users_with_customer = User.objects.filter(customer_profile__isnull=False).count()
users_without_customer = total_users - users_with_customer

print(f"Total Users: {total_users}")
print(f"Users WITH Customer profile: {users_with_customer}")
print(f"Users WITHOUT Customer profile: {users_without_customer}")
print()

if users_without_customer > 0:
    print("Users WITHOUT Customer profiles:")
    users_no_customer = User.objects.filter(customer_profile__isnull=False)
    for user in users_no_customer[:10]:  # Show first 10
        profile_type = "Admin/Staff" if (user.is_staff or user.is_superuser) else "Customer"
        print(f"  - {user.username} ({profile_type}) - User Type: {user.user_type}")
    if users_no_customer.count() > 10:
        print(f"  ... and {users_no_customer.count() - 10} more")
    print()

# 2. Check Customer-User relationship integrity
print("2. CUSTOMER-USER RELATIONSHIP INTEGRITY")
print("-" * 80)

total_customers = Customer.objects.count()
customers_with_user = Customer.objects.filter(user__isnull=False).count()
customers_without_user = total_customers - customers_with_user

print(f"Total Customers: {total_customers}")
print(f"Customers WITH User account: {customers_with_user}")
print(f"Customers WITHOUT User account (guest bookings): {customers_without_user}")
print()

# 3. Check for orphaned records
print("3. ORPHANED RECORDS CHECK")
print("-" * 80)

# Check if any Customer references a non-existent User
print("Checking for Customers referencing deleted Users...")
customers_with_deleted_user = 0
for customer in Customer.objects.iterator():
    if customer.user_id and not User.objects.filter(id=customer.user_id).exists():
        customers_with_deleted_user += 1
        print(f"  - Customer ID {customer.id} ({customer.email}) references deleted User ID {customer.user_id}")

if customers_with_deleted_user == 0:
    print("  No orphaned Customer records found.")
print()

# 4. Check User types and their Customer profile status
print("4. USER TYPE DISTRIBUTION")
print("-" * 80)

for user_type, display_name in User.USER_TYPE_CHOICES:
    users_of_type = User.objects.filter(user_type=user_type)
    count = users_of_type.count()
    without_customer = sum(1 for u in users_of_type if not hasattr(u, 'customer_profile') or not u.customer_profile)
    print(f"{display_name}:")
    print(f"  Total: {count}")
    print(f"  WITHOUT Customer profile: {without_customer}")

# Check admin users specifically
admin_users = User.objects.filter(is_superuser=True)
print(f"\nAdmin Users (is_superuser=True):")
print(f"  Total: {admin_users.count()}")
for admin in admin_users:
    has_customer = hasattr(admin, 'customer_profile') and admin.customer_profile
    print(f"  - {admin.username}: has_customer={has_customer}")
print()

# 5. Check Dogs and their ownership
print("5. DOG OWNERSHIP INTEGRITY")
print("-" * 80)

total_dogs = Dog.objects.count()
dogs_with_user_owner = Dog.objects.filter(owner__isnull=False).count()
dogs_without_owner = total_dogs - dogs_with_user_owner

print(f"Total Dogs: {total_dogs}")
print(f"Dogs WITH User owner: {dogs_with_user_owner}")
print(f"Dogs WITHOUT User owner: {dogs_without_owner}")
print()

if dogs_without_owner > 0:
    print("WARNING: Dogs without User owners:")
    dogs_no_owner = Dog.objects.filter(owner__isnull=True)
    for dog in dogs_no_owner[:5]:
        print(f"  - {dog.name} (ID: {dog.id})")
    print()

# 6. Test authentication backend
print("6. AUTHENTICATION BACKEND TEST")
print("-" * 80)

from django.conf import settings
auth_backends = settings.AUTHENTICATION_BACKENDS
print(f"Configured authentication backends:")
for backend in auth_backends:
    print(f"  - {backend}")
print()

# Check if custom backend is configured
if 'mainapp.backends.UserProfileBackend' in auth_backends:
    print("Custom UserProfileBackend is configured.")
else:
    print("WARNING: Custom UserProfileBackend is NOT configured!")
print()

# 7. Check for signal handlers
print("7. SIGNAL HANDLERS CHECK")
print("-" * 80)

print("Checking for post_save signals on User model...")

# Try to find signals in the codebase
signal_files = [
    'mainapp/signals.py',
    'users/signals.py',
]

has_customer_signal = False
for signal_file in signal_files:
    import os
    full_path = os.path.join(os.path.dirname(__file__), signal_file)
    if os.path.exists(full_path):
        with open(full_path, 'r') as f:
            content = f.read()
            if 'post_save' in content and 'User' in content:
                print(f"  Found post_save signal in {signal_file}")
                has_customer_signal = True

if not has_customer_signal:
    print("  WARNING: No post_save signal found for User->Customer synchronization!")
    print("  This means Customer profiles are NOT automatically created when Users are created.")
    print("  Customer profiles are only created in the customer_sign_up view.")
print()

# 8. Summary and Recommendations
print("=" * 80)
print("SUMMARY AND RECOMMENDATIONS")
print("=" * 80)

issues = []

if users_without_customer > 0:
    non_admin_without_customer = User.objects.filter(
        customer_profile__isnull=True,
        is_staff=False,
        is_superuser=False,
        user_type='customer'
    ).count()
    if non_admin_without_customer > 0:
        issues.append(f"CRITICAL: {non_admin_without_customer} customer Users exist without Customer profiles!")

if customers_with_deleted_user > 0:
    issues.append(f"HIGH: {customers_with_deleted_user} Customer records reference deleted Users!")

if dogs_without_owner > 0:
    issues.append(f"MEDIUM: {dogs_without_owner} Dogs exist without a User owner!")

if not has_customer_signal:
    issues.append("INFO: No automatic User->Customer signal. Customer profiles are manually created in views.")

if 'mainapp.backends.UserProfileBackend' not in auth_backends:
    issues.append("HIGH: Custom authentication backend is not configured in settings!")

if issues:
    print("ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
else:
    print("No critical issues found!")

print()
print("RECOMMENDATIONS:")
print()
print("1. If customer Users exist without Customer profiles, either:")
print("   - Create missing Customer profiles, or")
print("   - Delete orphaned User accounts")
print()
print("2. Consider using database transactions in customer_sign_up to ensure")
print("   User and Customer are created atomically (all or nothing)")
print()
print("3. Add post_save signal handler for User model to automatically create")
print("   Customer profiles for customer-type Users (optional)")
print()
print("4. Ensure authentication backend is properly configured in settings.py")
print()
print("=" * 80)
