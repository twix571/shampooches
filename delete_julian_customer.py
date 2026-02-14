import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')
django.setup()

from mainapp.models import Appointment, Customer
from django.db import transaction

with transaction.atomic():
    # Delete appointments for Customer julian
    deleted = Appointment.objects.filter(customer_id=1).delete()
    print(f'Deleted {deleted[0]} appointments for Customer julian')

    # Delete the Customer julian
    c = Customer.objects.get(id=1)
    c.delete()
    print(f'Deleted Customer julian')

print("\nCleanup complete! Database is now clean.")
