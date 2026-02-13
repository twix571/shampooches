"""
Django management command to create a superuser automatically if one doesn't exist.
This is useful for deployments (e.g., Railway) where you need to ensure a superuser exists.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Create a superuser if one does not already exist'

    def handle(self, *args, **options):
        User = get_user_model()

        # Check for superuser via environment variables
        superuser_username = os.getenv('SUPERUSER_USERNAME')
        superuser_email = os.getenv('SUPERUSER_EMAIL', '')
        superuser_password = os.getenv('SUPERUSER_PASSWORD')

        if not superuser_username or not superuser_password:
            self.stdout.write(
                self.style.ERROR(
                    f'MISSING: username={bool(superuser_username)}, password={bool(superuser_password)}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'SUPERUSER_USERNAME and SUPERUSER_PASSWORD environment variables not set. '
                    'Skipping superuser creation.'
                )
            )
            return

        # Check if superuser already exists
        if User.objects.filter(username=superuser_username).exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f'Superuser "{superuser_username}" already exists. Skipping creation.'
                )
            )
            # Update password if provided (useful for password resets)
            user = User.objects.get(username=superuser_username)
            user.set_password(superuser_password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Password updated for superuser "{superuser_username}"')
            )
            return

        # Create superuser
        try:
            user = User.objects.create_superuser(
                username=superuser_username,
                email=superuser_email,
                password=superuser_password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser "{superuser_username}" with is_superuser={user.is_superuser}, is_staff={user.is_staff}, is_active={user.is_active}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create superuser: {e}')
            )
