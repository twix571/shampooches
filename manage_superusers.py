from users.models import User
import sys

action = sys.argv[1] if len(sys.argv) > 1 else 'list'

if action == 'list':
    superusers = User.objects.filter(is_superuser=True)
    print(f'Superusers count: {superusers.count()}')
    for u in superusers:
        print(f'  - Username: {u.username}')
        print(f'    Email: {u.email}')
        print(f'    is_staff: {u.is_staff}')
        print(f'    is_active: {u.is_active}')
        print()
        
elif action == 'delete':
    username = sys.argv[2] if len(sys.argv) > 2 else None
    if username:
        deleted = User.objects.filter(username=username).delete()
        print(f'Deleted {deleted[0]} users with username {username}')
    else:
        print('Usage: python manage.py shell < manage_superusers.py delete <username>')
        
elif action == 'create':
    username = sys.argv[2]
    password = sys.argv[3]
    email = sys.argv[4] if len(sys.argv) > 4 else 'admin@example.com'
    
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f'Created superuser: {username}')
    except Exception as e:
        print(f'Error: {e}')
        
elif action == 'reset_password':
    username = sys.argv[2]
    new_password = sys.argv[3]
    
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        print(f'Password reset for {username}')
    except Exception as e:
        print(f'Error: {e}')
