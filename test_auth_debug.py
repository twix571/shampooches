#!/usr/bin/env python
"""
Test script to debug admin authentication issues.
Run this in the Railway console or locally.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')

import django
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

print('=== Admin Authentication Test ===\n')

# 1. Check environment variables
print('1. Environment Variables:')
print(f'   SUPERUSER_USERNAME: {os.getenv("SUPERUSER_USERNAME")}')
print(f'   SUPERUSER_PASSWORD set: {"YES" if os.getenv("SUPERUSER_PASSWORD") else "NO"}')

# 2. List all users
print('\n2. All Users:')
all_users = User.objects.all()
print(f'   Total: {all_users.count()}')
for u in all_users:
    print(f'   - {u.username}: super={u.is_superuser}, staff={u.is_staff}, active={u.is_active}')

# 3. Try to create/update superuser
print('\n3. Attempting to create/update superuser:')
username = os.getenv('SUPERUSER_USERNAME')
password = os.getenv('SUPERUSER_PASSWORD')
email = os.getenv('SUPERUSER_EMAIL', '')

if username and password:
    try:
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            print(f'   Updated existing user: {username}')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print(f'   Created new user: {username}')

        print(f'   User details: super={user.is_superuser}, staff={user.is_staff}, active={user.is_active}')
    except Exception as e:
        print(f'   ERROR: {e}')
else:
    print('   SKIPPED: Missing SUPERUSER_USERNAME or SUPERUSER_PASSWORD')

# 4. Test authentication
print('\n4. Testing Authentication:')
if User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)

    # Test with standard authentication
    auth_user = authenticate(username=username, password=password)
    print(f'   Standard authenticate: {"SUCCESS" if auth_user else "FAILED"}')

    # Test with ModelBackend directly
    backend = ModelBackend()
    backend_user = backend.authenticate(request=None, username=username, password=password)
    print(f'   ModelBackend authenticate: {"SUCCESS" if backend_user else "FAILED"}')

    # Test with check_password
    print(f'   check_password: {"SUCCESS" if user.check_password(password) else "FAILED"}')

    # Test can login
    from django.test import Client
    client = Client()
    login_success = client.login(username=username, password=password)
    print(f'   Client.login: {"SUCCESS" if login_success else "FAILED"}')

print('\n=== Test Complete ===')
