from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line, call_command
import sys

def create_superuser():
    User = get_user_model()

    # Delete existing admin if exists
    User.objects.filter(username='admin').delete()

    # Create new admin
    User.objects.create_superuser(
        username='admin',
        email='admin@shampooches.com',
        password='admin123'
    )

    print("Created superuser with:")
    print("  Username: admin")
    print("  Password: admin123")

if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
    django.setup()
    create_superuser()
