import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

u = User.objects.get(username='customer1')
print(f'User: {u.username}')
print(f'Type: {u.user_type}')
print(f'Has Customer Profile: {hasattr(u, "customer_profile")}')

if hasattr(u, 'customer_profile'):
    print(f'Customer Profile ID: {u.customer_profile.id}')
    print('SUCCESS: Customer profile created via signals!')
else:
    print('WARNING: No customer_profile found - signals may not have worked')
