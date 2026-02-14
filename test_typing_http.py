"""
Test the typing indicator endpoint using Python requests.
This will help identify if the issue is with how the request is being sent.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from mainapp.models import MessageThread
import json

User = get_user_model()

# Get a customer user
customer = User.objects.filter(user_type='customer').first()
print(f"Customer: {customer.username}, id={customer.id}")

# Get an existing thread
thread = MessageThread.objects.filter(customer=customer).first()
print(f"Thread: id={thread.id}, subject='{thread.subject}'")

# Create test client and login
client = Client()
client.force_login(customer)
print("\nLogged in customer")

# Try to simulate the exact request format the JavaScript sends
print("\nTesting typing indicator endpoint...")

# Get the CSRF token from the client's cookies
csrf_token = client.cookies.get('csrftoken', '')

print(f"CSRF Token: {csrf_token[:20] if csrf_token else 'None'}...")

# Make the POST request with the exact headers and body that JavaScript sends
response = client.post(
    f'/api/contact/threads/{thread.id}/typing/',
    data=b'is_typing=true',
    content_type='application/x-www-form-urlencoded',
    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    HTTP_X_CSRFTOKEN=csrf_token
)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"Content: {response.content.decode()[:500]}")

if response.status_code == 200:
    print("\n✓ SUCCESS: Typing indicator endpoint works!")
else:
    print(f"\n✗ FAILURE: Status {response.status_code}")
