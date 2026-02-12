from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Reset password for BrittTheBoss'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'BrittTheBoss'
        new_password = 'BritBrit'
        
        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            self.stdout.write(f'Successfully reset password for {username} to {new_password}')
            self.stdout.write(f'Verification: {user.check_password(new_password)}')
        except User.DoesNotExist:
            self.stdout.write(f'User {username} not found')
