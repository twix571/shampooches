#!/usr/bin/env python
"""
Delete orphaned customer Users without Customer profiles.
This script deletes Users that have user_type='customer' but no Customer profile.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("DELETING ORPHANED CUSTOMER USERS")
print("=" * 80)
print()

orphaned = User.objects.filter(user_type='customer').exclude(
    customer_profile__isnull=False
)

print(f"Found {orphaned.count()} orphaned customer users:")
for user in orphaned:
    print(f"  - {user.username} ({user.email})")

print()
print("Deleting...")

deleted = orphaned.delete()[0]

print()
print(f"Deleted {deleted} users.")
print()
print("Verification:")
remaining = User.objects.filter(user_type='customer').exclude(
    customer_profile__isnull=False
).count()
print(f"Orphaned users remaining: {remaining}")

print()
print("=" * 80)
