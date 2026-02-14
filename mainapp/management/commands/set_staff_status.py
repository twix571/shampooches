from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Set staff status for existing users based on their user_type'

    def handle(self, *args, **options):
        self.stdout.write('=== Setting Staff Status Based on User Type ===\n')

        # Update admin users
        admins = User.objects.filter(user_type='admin')
        admins_updated = admins.update(is_staff=True, is_superuser=True)
        self.stdout.write(f'Admin users: {admins_updated} updated (is_staff=True, is_superuser=True)')

        for admin in admins:
            self.stdout.write(f'  - {admin.username} ({admin.email})')

        # Update groomer manager users
        groomer_managers = User.objects.filter(user_type='groomer_manager')
        groomer_managers_updated = groomer_managers.update(is_staff=True, is_superuser=False)
        self.stdout.write(f'\nGroomer Manager users: {groomer_managers_updated} updated (is_staff=True, is_superuser=False)')

        for gm in groomer_managers:
            self.stdout.write(f'  - {gm.username} ({gm.email})')

        # Update groomer users
        groomers = User.objects.filter(user_type='groomer')
        groomers_updated = groomers.update(is_staff=True, is_superuser=False)
        self.stdout.write(f'\nGroomer users: {groomers_updated} updated (is_staff=True, is_superuser=False)')

        for groomer in groomers:
            self.stdout.write(f'  - {groomer.username} ({groomer.email})')

        # Update customer users
        customers = User.objects.filter(user_type='customer')
        customers_updated = customers.update(is_staff=False, is_superuser=False)
        self.stdout.write(f'\nCustomer users: {customers_updated} updated (is_staff=False, is_superuser=False)')

        total_updated = admins_updated + groomer_managers_updated + groomers_updated + customers_updated
        self.stdout.write(f'\n✓ Successfully updated {total_updated} total users')
