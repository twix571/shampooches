"""Customer profile and dog management views."""

from decimal import Decimal

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.messages import add_message, constants
from django.core.exceptions import ValidationError
from django.db.models import Case, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from mainapp.models import Appointment, Breed, Dog, DogDeletionRequest, Customer
from mainapp.forms import DogForm


@login_required
def customer_profile(request: HttpRequest) -> HttpResponse:
    """
    Customer profile page for viewing and editing account details.

    Displays customer information including:
    - Username, email, phone
    - Booking history
    - Account settings

    Allows updating profile information.
    """
    try:
        user = request.user

        if not hasattr(user, 'user_type'):
            add_message(request, constants.ERROR, 'User account configuration error. Please contact support.')
            return redirect('customer_landing')

        if user.user_type != 'customer':
            add_message(request, constants.WARNING, 'This page is only accessible to customers.')
            return redirect('customer_landing')
    except Exception as e:
        add_message(request, constants.ERROR, f'Error accessing user profile: {str(e)}')
        return redirect('customer_landing')

    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        errors = []

        has_changes = False

        if email and email != user.email:
            User = get_user_model()
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                errors.append('Email already registered')
            else:
                user.email = email
                has_changes = True

        if phone is not None:
            user.phone = phone
            has_changes = True

        if full_name:
            name_parts = full_name.split()
            user.first_name = name_parts[0] if name_parts else ''
            user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            has_changes = True

        if password:
            if password != password_confirm:
                errors.append('Passwords do not match')
            else:
                try:
                    validate_password(password, user)
                    user.set_password(password)
                    has_changes = True
                except ValidationError as e:
                    errors.extend(e.messages)

        if errors:
            for error in errors:
                add_message(request, constants.ERROR, error)
            dogs_with_bookings = set(
                Appointment.objects.filter(
                    customer__user=user,
                    status__in=['pending', 'confirmed']
                ).values_list('dog_name', flat=True)
            )
            return render(request, 'mainapp/customer_profile.html', {
                'user': user,
                'customer_appointments': Appointment.objects.filter(
                    customer__user=user
                ).select_related('service').annotate(
                    status_order=Case(
                        When(status='pending', then=0),
                        When(status='confirmed', then=1),
                        When(status='completed', then=2),
                        When(status='cancelled', then=3),
                        default=4,
                    )
                ).order_by('status_order', '-date', '-time'),
                'dogs_with_bookings': dogs_with_bookings,
            })
        elif has_changes:
            user.save()
            add_message(request, constants.SUCCESS, 'Profile updated successfully!')
            if password:
                update_session_auth_hash(request, user)

        return redirect('customer_profile')

    try:
        customer_appointments = Appointment.objects.filter(
            customer__user=user
        ).select_related('service').annotate(
            status_order=Case(
                When(status='pending', then=0),
                When(status='confirmed', then=1),
                When(status='completed', then=2),
                When(status='cancelled', then=3),
                default=4,
            )
        ).order_by('status_order', '-date', '-time')

        # Get dog names with pending or confirmed bookings
        dogs_with_bookings = set(
            Appointment.objects.filter(
                customer__user=user,
                status__in=['pending', 'confirmed']
            ).values_list('dog_name', flat=True)
        )

        breeds = Breed.objects.filter(is_active=True).order_by('name')

        context = {
            'user': user,
            'customer_appointments': customer_appointments,
            'breeds': breeds,
            'dogs_with_bookings': dogs_with_bookings,
        }
        return render(request, 'mainapp/customer_profile.html', context)
    except Exception as e:
        add_message(request, constants.ERROR, f'Error loading profile data: {str(e)}')
        return redirect('customer_landing')


@login_required
def add_dog_modal(request: HttpRequest) -> HttpResponse:
    """
    Render the add dog modal.

    Requires customer authentication.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    breeds = Breed.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/add_dog_modal.html', {'breeds': breeds})


@login_required
def edit_dog_modal(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Render the edit dog modal.

    Requires customer authentication and ownership of the dog.

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to edit.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    breeds = Breed.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/edit_dog_modal.html', {'dog': dog, 'breeds': breeds})


@login_required
def add_dog(request: HttpRequest) -> HttpResponse:
    """
    Add a new dog profile for the customer.

    Validates and creates a new Dog record associated with the authenticated customer.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    if request.method == 'POST':
        form = DogForm(request.POST)
        if form.is_valid():
            dog = form.save(commit=False)
            dog.owner = request.user
            dog.save()
            add_message(request, constants.SUCCESS, 'Dog profile added successfully!')
            return redirect('customer_profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    add_message(request, constants.ERROR, error)

    return redirect('customer_profile')


@login_required
def edit_dog(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Edit an existing dog profile.

    Updates an existing Dog record associated with the authenticated customer.

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to edit.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    if request.method == 'POST':
        from django.http import JsonResponse

        form = DogForm(request.POST, instance=dog)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Dog profile updated successfully!'}, status=200)
        else:
            errors = {field: [str(error) for error in errors] for field, errors in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    return HttpResponse(status=405)


@login_required
def delete_dog(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Delete a dog profile immediately.

    Requires customer authentication and ownership of the dog.

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to delete.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
        dog.delete()
        add_message(request, constants.SUCCESS, 'Dog profile deleted successfully!')
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')

    return redirect('customer_profile')


@login_required
def request_dog_deletion_modal(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Render the request dog deletion modal.

    Allows customers to submit a deletion request that requires admin approval.

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to request deletion for.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    return render(request, 'mainapp/request_dog_deletion_modal.html', {'dog': dog})


@login_required
def request_dog_deletion(request: HttpRequest, dog_id: int) -> HttpResponse:
    """
    Submit a dog deletion request for admin approval.

    Creates a DogDeletionRequest record with the provided reason.

    Args:
        request: The HTTP request object.
        dog_id: The ID of the dog to request deletion for.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    if request.method != 'POST':
        return redirect('customer_profile')

    try:
        dog = Dog.objects.get(id=dog_id, owner=request.user)
    except Dog.DoesNotExist:
        add_message(request, constants.ERROR, 'Dog profile not found.')
        return redirect('customer_profile')

    reason = request.POST.get('reason', '').strip()
    if not reason:
        add_message(request, constants.ERROR, 'Please provide a reason for the deletion request.')
        return redirect('customer_profile')

    DogDeletionRequest.objects.create(
        dog=dog,
        requested_by=request.user,
        reason=reason,
        status='pending'
    )

    add_message(request, constants.SUCCESS,
                'Your deletion request has been submitted. Our team will review it and get back to you.')
    return redirect('customer_profile')


@login_required
def cancel_appointment_confirm_modal(request: HttpRequest, appointment_id: int) -> HttpResponse:
    """
    Render the appointment cancellation confirmation modal.

    Requires customer authentication and ownership of the appointment.

    Args:
        request: The HTTP request object.
        appointment_id: The ID of the appointment to confirm cancellation for.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        add_message(request, constants.ERROR, 'Appointment not found.')
        return redirect('customer_profile')

    # Check if it's the user's appointment
    if appointment.user and appointment.user.id != request.user.id:
        add_message(request, constants.ERROR, 'You can only cancel your own appointments.')
        return redirect('customer_profile')

    if not appointment.user and appointment.customer.email != request.user.email:
        add_message(request, constants.ERROR, 'You can only cancel your own appointments.')
        return redirect('customer_profile')

    return render(request, 'mainapp/cancel_appointment_confirm_modal.html', {'appointment': appointment})


@login_required
def cancel_appointment(request: HttpRequest, appointment_id: int) -> HttpResponse:
    """
    Cancel a pending appointment.

    Only allows cancellation of pending appointments that belong to the authenticated customer.
    Confirmed appointments cannot be cancelled.

    Args:
        request: The HTTP request object.
        appointment_id: The ID of the appointment to cancel.
    """
    if request.user.user_type != 'customer':
        add_message(request, constants.WARNING, 'This page is only accessible to customers.')
        return redirect('customer_landing')

    if request.method != 'POST':
        return redirect('customer_profile')

    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        add_message(request, constants.ERROR, 'Appointment not found.')
        return redirect('customer_profile')

    if appointment.status != 'pending':
        add_message(request, constants.ERROR,
                    'Only pending appointments can be cancelled. Please contact us for assistance.')
        return redirect('customer_profile')

    if appointment.user and appointment.user.id != request.user.id:
        add_message(request, constants.ERROR, 'You can only cancel your own appointments.')
        return redirect('customer_profile')

    if not appointment.user and appointment.customer.email != request.user.email:
        add_message(request, constants.ERROR, 'You can only cancel your own appointments.')
        return redirect('customer_profile')

    appointment.status = 'cancelled'
    appointment.save()

    add_message(request, constants.SUCCESS, 'Appointment cancelled successfully.')
    return redirect('customer_profile')
