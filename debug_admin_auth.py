from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()

print('=== Django Admin Authentication Debug ===\n')

# Check environment variables
import os
print('Environment Variables:')
print(f'SUPERUSER_USERNAME: {os.getenv("SUPERUSER_USERNAME")}')
print(f'SUPERUSER_PASSWORD set: {"Y" if os.getenv("SUPERUSER_PASSWORD") else "N"}')
print()

# List all users
print('All Users in Database:')
users = User.objects.all()
print(f'Total users: {users.count()}')
for u in users:
    print(f'  - {u.username}: super={u.is_superuser}, staff={u.is_staff}, active={u.is_active}')
print()

# Check for superusers specifically
print('Superusers:')
superusers = User.objects.filter(is_superuser=True)
print(f'Count: {superusers.count()}')
for u in superusers:
    print(f'  - {u.username}')
print()

# Test authentication for superuser
if superusers.exists():
    for user in superusers:
        username = user.username
        print(f'Testing authentication for "{username}":')

        # Try with environment variable password
        env_password = os.getenv('SUPERUSER_PASSWORD')
        if env_password:
            env_user = authenticate(username=username, password=env_password)
            print(f'  - With SUPERUSER_PASSWORD: {"SUCCESS" if env_user else "FAILED"}')
        else:
            print(f'  - SUPERUSER_PASSWORD not set')

        # Test with check_password
        print(f'  - Password hash: {user.password[:20]}...')
        print()
