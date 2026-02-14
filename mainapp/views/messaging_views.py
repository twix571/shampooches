"""
Views for the contact messaging system.

This module contains views for the messaging/contact functionality,
including customer-facing contact pages and staff-facing message management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
import json

from mainapp.models import MessageThread, Message, ThreadView, TypingIndicator


@login_required
def contact_page(request):
    """
    Contact page that redirects based on authentication status.
    Authenticated customers go to the customer messaging page.
    Authenticated staff go to the staff messaging page.
    Non-authenticated users see a "Why Create Account" page.
    """
    if request.user.is_authenticated:
        if request.user.user_type == 'customer':
            return contact_page_authenticated(request)
        elif request.user.user_type in ['admin', 'groomer_manager', 'groomer']:
            return staff_contact_page(request)
    return why_create_account_page(request)


@login_required
def contact_page_authenticated(request):
    """
    Contact page for authenticated customers.
    Displays their message threads and allows messaging staff.
    """
    # Get all threads for this customer, ordered by most recent activity
    threads = MessageThread.objects.filter(
        customer=request.user,
        is_active=True
    ).prefetch_related('messages__sender')

    # Get staff members available for messaging (groomer_managers, admin, groomers)
    from users.models import User
    available_staff = User.objects.filter(
        user_type__in=['admin', 'groomer_manager', 'groomer'],
        is_active=True
    ).order_by('user_type', 'username')

    context = {
        'threads': threads,
        'available_staff': available_staff,
    }

    return render(request, 'mainapp/contact_page_authenticated.html', context)


def why_create_account_page(request):
    """
    Page explaining the benefits of creating an account to access messaging.
    """
    return render(request, 'mainapp/why_create_account.html')


@login_required
def staff_contact_page(request):
    """
    Staff contact page for admin/groomer_manager/groomer users.
    Displays all customer message threads for staff to view and respond.
    """
    # Verify user is staff
    if request.user.user_type not in ['admin', 'groomer_manager', 'groomer']:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access restricted to staff members")

    return render(request, 'mainapp/staff_contact_page.html')


@require_POST
@login_required
def create_message_thread(request):
    """
    Create a new message thread and send the first message.
    Returns JSON response with thread ID.
    """
    subject = request.POST.get('subject', '').strip()
    message_content = request.POST.get('message', '').strip()
    recipient_username = request.POST.get('recipient', '').strip()

    if not subject or not message_content:
        return JsonResponse({
            'success': False,
            'message': 'Subject and message are required.',
            'data': None,
            'errors': None
        }, status=400)

    if not recipient_username:
        return JsonResponse({
            'success': False,
            'message': 'Please select a recipient.',
            'data': None,
            'errors': None
        }, status=400)

    # Verify recipient exists and is staff
    from users.models import User
    try:
        recipient = User.objects.get(
            username=recipient_username,
            user_type__in=['admin', 'groomer_manager', 'groomer'],
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Invalid recipient.',
            'data': None,
            'errors': None
        }, status=400)

    # Check for existing thread with same subject to avoid duplicates
    existing_thread = MessageThread.objects.filter(
        customer=request.user,
        subject=subject
    ).first()

    if existing_thread:
        # Add message to existing thread
        thread = existing_thread
    else:
        # Create new thread
        thread = MessageThread.objects.create(
            customer=request.user,
            subject=subject
        )

    # Create initial message
    message = Message.objects.create(
        thread=thread,
        sender=request.user,
        content=message_content
    )

    return JsonResponse({
        'success': True,
        'message': 'Message sent successfully!',
        'data': {
            'thread_id': thread.id,
            'message_id': message.id,
        },
        'errors': None
    })


@require_GET
@login_required
def get_thread_messages(request, thread_id):
    """
    Get messages for a specific thread.
    Returns JSON response with messages.
    """
    thread = get_object_or_404(
        MessageThread,
        id=thread_id,
        customer=request.user  # Only get threads for the current user
    )

    messages = thread.messages.select_related('sender').order_by('created_at')

    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_type': msg.sender.user_type,
            'content': msg.content,
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'message': 'Messages retrieved successfully',
        'data': {
            'thread_id': thread.id,
            'subject': thread.subject,
            'messages': messages_data
        },
        'errors': None
    })


@require_POST
@login_required
def send_message(request, thread_id):
    """
    Send a new message in a thread.
    Returns JSON response with message details.
    """
    thread = get_object_or_404(
        MessageThread,
        id=thread_id
    )

    # Verify user has access to this thread
    if thread.customer != request.user:
        # Staff can also access threads
        from users.models import User
        if not User.objects.filter(
            id=request.user.id,
            user_type__in=['admin', 'groomer_manager']
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'Access denied.',
                'data': None,
                'errors': None
            }, status=403)

    message_content = request.POST.get('message', '').strip()
    if not message_content:
        return JsonResponse({
            'success': False,
            'message': 'Message content is required.',
            'data': None,
            'errors': None
        }, status=400)

    # Create message
    message = Message.objects.create(
        thread=thread,
        sender=request.user,
        content=message_content
    )

    # If sender is staff, mark thread as updated
    if request.user.user_type in ['admin', 'groomer_manager']:
        thread.updated_at = timezone.now()
        thread.save()

    return JsonResponse({
        'success': True,
        'message': 'Message sent successfully',
        'data': {
            'message_id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.isoformat()
        },
        'errors': None
    })


@require_GET
@login_required
def update_thread_view(request, thread_id):
    """
    Update the user's view status for this thread.
    Used for tracking which users are viewing a thread.
    Called periodically via polling.
    """
    thread = get_object_or_404(MessageThread, id=thread_id)

    # Verify user has access to this thread
    if thread.customer != request.user:
        from users.models import User
        if not User.objects.filter(
            id=request.user.id,
            user_type__in=['admin', 'groomer_manager', 'groomer']
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'Access denied.',
                'data': None,
                'errors': None
            }, status=403)

    # Update or create thread view
    ThreadView.objects.update_or_create(
        thread=thread,
        user=request.user,
        defaults={'last_seen_at': timezone.now()}
    )

    # Get all active viewers for this thread (staff only see this)
    viewers = []
    if request.user.user_type in ['admin', 'groomer_manager', 'groomer']:
        active_viewers = ThreadView.get_active_viewers(thread, timeout_seconds=30)
        viewers = [
            {
                'username': tv.user.username,
                'user_type': tv.user.user_type,
            }
            for tv in active_viewers if tv.user != request.user  # Don't include self
        ]

    return JsonResponse({
        'success': True,
        'message': 'View updated',
        'data': {
            'active_viewers': viewers
        },
        'errors': None
    })


@require_POST
@login_required
def set_typing_indicator(request, thread_id):
    """
    Set the typing indicator for the current user in this thread.
    """
    thread = get_object_or_404(MessageThread, id=thread_id)

    # Verify user has access to this thread
    if thread.customer != request.user:
        from users.models import User
        if not User.objects.filter(
            id=request.user.id,
            user_type__in=['admin', 'groomer_manager', 'groomer']
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'Access denied.',
                'data': None,
                'errors': None
            }, status=403)

    # Update or remove typing indicator
    is_typing = request.POST.get('is_typing', 'false').lower() == 'true'

    if is_typing:
        TypingIndicator.objects.update_or_create(
            thread=thread,
            user=request.user,
            defaults={'last_typed_at': timezone.now()}
        )
    else:
        TypingIndicator.objects.filter(
            thread=thread,
            user=request.user
        ).delete()

    # Get all active typers for this thread (excluding self)
    typers = []
    active_typers = TypingIndicator.get_active_typers(thread, timeout_seconds=5)
    typers = [
        {
            'username': typer.user.username,
            'user_type': typer.user.user_type,
        }
        for typer in active_typers if typer.user != request.user
    ]

    return JsonResponse({
        'success': True,
        'message': 'Typing indicator updated',
        'data': {
            'active_typers': typers
        },
        'errors': None
    })


@require_GET
@login_required
def get_thread_status(request, thread_id):
    """
    Get current status of a thread including active viewers and active typers.
    """
    thread = get_object_or_404(MessageThread, id=thread_id)

    # Verify user has access to this thread
    if thread.customer != request.user:
        from users.models import User
        if not User.objects.filter(
            id=request.user.id,
            user_type__in=['admin', 'groomer_manager', 'groomer']
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'Access denied.',
                'data': None,
                'errors': None
            }, status=403)

    # Get active viewers (staff only)
    viewers = []
    if request.user.user_type in ['admin', 'groomer_manager', 'groomer']:
        active_viewers = ThreadView.get_active_viewers(thread, timeout_seconds=30)
        viewers = [
            {
                'username': tv.user.username,
                'user_type': tv.user.user_type,
            }
            for tv in active_viewers if tv.user != request.user
        ]

    # Get active typers
    active_typers = TypingIndicator.get_active_typers(thread, timeout_seconds=5)
    typers = [
        {
            'username': typer.user.username,
            'user_type': typer.user.user_type,
        }
        for typer in active_typers if typer.user != request.user
    ]

    return JsonResponse({
        'success': True,
        'message': 'Status retrieved',
        'data': {
            'active_viewers': viewers,
            'active_typers': typers
        },
        'errors': None
    })


@require_GET
@login_required
def customer_threads_list(request):
    """
    Get all threads for the current customer.
    Only accessible by staff.
    """
    from users.models import User

    # Verify user is staff
    if request.user.user_type not in ['admin', 'groomer_manager', 'groomer']:
        return JsonResponse({
            'success': False,
            'message': 'Access denied.',
            'data': None,
            'errors': None
        }, status=403)

    customer_username = request.GET.get('customer', '')

    if customer_username:
        try:
            customer = User.objects.get(username=customer_username, user_type='customer')
            threads = MessageThread.objects.filter(customer=customer, is_active=True)
        except User.DoesNotExist:
            threads = MessageThread.objects.none()
    else:
        threads = MessageThread.objects.filter(is_active=True)

    threads = threads.select_related('customer').prefetch_related('messages').order_by('-updated_at')

    threads_data = []
    for thread in threads:
        last_msg = thread.get_last_message()
        threads_data.append({
            'id': thread.id,
            'customer': thread.customer.username,
            'subject': thread.subject,
            'last_message': last_msg.content[:100] if last_msg else 'No messages yet',
            'last_message_at': last_msg.created_at.isoformat() if last_msg else thread.created_at.isoformat(),
            'unread_count': thread.messages.filter(is_read=False).count(),
        })

    return JsonResponse({
        'success': True,
        'message': 'Threads retrieved',
        'data': {
            'threads': threads_data
        },
        'errors': None
    })


@require_GET
@login_required
def staff_thread_messages(request, thread_id):
    """
    Staff endpoint to get messages for any thread.
    """
    from users.models import User

    # Verify user is staff
    if request.user.user_type not in ['admin', 'groomer_manager', 'groomer']:
        return JsonResponse({
            'success': False,
            'message': 'Access denied.',
            'data': None,
            'errors': None
        }, status=403)

    thread = get_object_or_404(MessageThread, id=thread_id)

    # Mark all unread messages from customer as read
    thread.messages.filter(
        is_read=False,
        sender=thread.customer
    ).update(is_read=True)

    messages = thread.messages.select_related('sender').order_by('created_at')

    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_type': msg.sender.user_type,
            'content': msg.content,
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'message': 'Messages retrieved',
        'data': {
            'thread_id': thread.id,
            'customer': thread.customer.username,
            'subject': thread.subject,
            'messages': messages_data
        },
        'errors': None
    })
