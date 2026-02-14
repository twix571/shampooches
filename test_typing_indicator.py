"""
Diagnostic script to test the typing indicator endpoint.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from mainapp.models import MessageThread, TypingIndicator
from mainapp.views.messaging_views import set_typing_indicator

User = get_user_model()

# Get a customer user
try:
    customer = User.objects.filter(user_type='customer').first()
    print(f"Customer: {customer.username}, id={customer.id}")

    # Get or create a test thread
    thread = MessageThread.objects.filter(customer=customer).first()
    if not thread:
        thread = MessageThread.objects.create(
            customer=customer,
            subject="Test Thread"
        )
        print(f"Created new thread: id={thread.id}")
    else:
        print(f"Found existing thread: id={thread.id}, subject='{thread.subject}'")

    # Create mock request
    from unittest.mock import Mock
    factory = RequestFactory()
    request = factory.post(
        f'/api/contact/threads/{thread.id}/typing/',
        {'is_typing': 'true'},
        content_type='application/x-www-form-urlencoded'
    )
    request.user = customer

    # Try to call the view
    print("\nAttempting to set typing indicator...")
    response = set_typing_indicator(request, thread.id)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode() if hasattr(response, 'content') else response}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
