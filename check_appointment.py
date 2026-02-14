import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')
django.setup()

from mainapp.models import Appointment, Groomer, Service, Customer
from django.contrib.auth import get_user_model

User = get_user_model()

a = Appointment.objects.get(id=3)

print('=== APPOINTMENT #3 DETAILS ===')
print(f'ID: {a.id}')
print(f'Status: {a.status}')
print(f'Date: {a.date}')
print(f'Time: {a.time}')
print(f'\n--- Relationships ---')

if a.customer:
    print(f'[OK] Customer: {a.customer.name} (ID: {a.customer.id})')
    if a.customer.user:
        print(f'  |-- User: customer1 (ID: {a.customer.user.id}) - PROPERLY LINKED')
    else:
        print(f'  |-- NO USER - CUSTOMER IS ORPHANED')
else:
    print('[X] No Customer linked')

if a.service:
    print(f'[OK] Service: {a.service.name} (ID: {a.service.id})')
else:
    print('[X] No Service linked')

if a.groomer:
    print(f'[OK] Groomer: {a.groomer.name} (ID: {a.groomer.id})')
else:
    print('[X] No Groomer linked')

print('\n=== VERDICT ===')
if a.customer and hasattr(a.customer, 'user') and a.customer.user:
    print('[NOT ORPHANED] All relationships are valid')
    print('   This is customer1\'s appointment with Brittany H')
elif a.customer and not (hasattr(a.customer, 'user') and a.customer.user):
    print('[ORPHANED] Customer exists but has no User')
else:
    print('[ORPHANED] Missing relationships')
