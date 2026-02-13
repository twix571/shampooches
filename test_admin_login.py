from django.test import Client
from django.contrib.auth import get_user_model

# Get the user
User = get_user_model()
u = User.objects.get(username='BeckTheBoss')
print(f'User exists: {u.username}')
print(f'is_staff: {u.is_staff}')
print(f'is_superuser: {u.is_superuser}')
print(f'is_active: {u.is_active}')

# Test admin login
client = Client()
response = client.post('/admin/', {'username': 'BeckTheBoss', 'password': 'Jhue0606!8'}, follow=False)
print(f'\n')
print(f'Login test:')
print(f'Status code: {response.status_code}')
print(f'Redirect location: {response.get("location", "No redirect")}')
print(f'Successful (302 redirect): {response.status_code == 302}')

# Check if logged in
client.login(username='BeckTheBoss', password='Jhue0606!8')
response2 = client.get('/admin/')
print(f'\n')
print(f'After manual login:')
print(f'Can access admin: {response2.status_code in [200, 302]}')
print(f'Status code: {response2.status_code}')
