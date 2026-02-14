"""
Test the typing indicator using Django's test client.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from mainapp.models import MessageThread

User = get_user_model()

# Get a customer user
customer = User.objects.filter(user_type='customer').first()
print(f"Customer: {customer.username}, id={customer.id}")

# Get an existing thread
thread = MessageThread.objects.filter(customer=customer).first()
print(f"Thread: id={thread.id}, subject='{thread.subject}'")

# Create test client
client = Client()

# Login the customer
client.force_login(customer)
print("\nLogged in customer")

# Try to set typing indicator
print("\nPOST request to typing endpoint...")
response = client.post(
    f'/api/contact/threads/{thread.id}/typing/',
    {'is_typing': 'true'},
    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"Content: {response.content.decode()[:500]}")

# Try to get thread status
print("\nGET request to status endpoint...")
response = client.get(f'/api/contact/threads/{thread.id}/status/')
print(f"Status: {response.status_code}")
print(f"Content: {response.content.decode()[:500]}")
