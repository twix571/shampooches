"""Schedule and time slot management views including HTMX partials."""

from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from mainapp.models import Groomer, TimeSlot
from mainapp.utils import admin_required


@admin_required
def time_slot_editor_modal(request):
    """
    Render the time slot editor modal.

    Expects optional query parameters:
    - date: The date to edit (format: YYYY-MM-DD)
    - day_name: The day of the week for display purposes

    If date is provided but day_name is not, the day_name is calculated automatically.
    """
    date_str = request.GET.get('date')
    day_name = request.GET.get('day_name')
    if date_str and not day_name:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = dt.strftime('%A')
        except ValueError:
            day_name = ''
    return render(request, 'mainapp/schedule_modal.html', {'date': date_str, 'day_name': day_name})


@csrf_exempt
@admin_required
def render_groomer_options(request: HttpRequest) -> HttpResponse:
    """
    Render groomer options HTML for HTMX.

    Returns partial HTML for groomer select dropdown.

    This is an AJAX endpoint used to dynamically populate groomer selection
    in the admin interface without reloading the page.
    """
    groomers = Groomer.objects.filter(is_active=True).order_by('name')
    context = {'groomers': groomers}
    return render(request, 'mainapp/partials/groomer_options.html', context)


@csrf_exempt
@admin_required
def render_time_slots(request: HttpRequest) -> HttpResponse:
    """
    Render time slots HTML for HTMX.

    Returns partial HTML for existing time slots list.
    If groomer_id is empty or 'all', shows time slots for all groomers.

    Query parameters:
    - groomer_id: The groomer ID to filter by (or 'all' for all groomers)
    - date: The date to display time slots for (format: YYYY-MM-DD)

    This is an AJAX endpoint used to dynamically display time slots
    in the admin interface using HTMX partial HTML updates.
    """
    groomer_id = request.GET.get('groomer_id', '').strip()
    date_str = request.GET.get('date')

    if not date_str:
        return HttpResponse('Missing date parameter', status=400)

    booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Handle "All Groomers" case (empty groomer_id or 'all')
    if not groomer_id or groomer_id == 'all':
        time_slots = TimeSlot.objects.filter(
            date=booking_date
        ).select_related('groomer').order_by('groomer__name', 'start_time')
    else:
        groomer = get_object_or_404(Groomer, id=int(groomer_id))
        time_slots = TimeSlot.objects.filter(
            groomer=groomer,
            date=booking_date
        ).order_by('start_time')

    def format_time_display(time_obj):
        """
        Format time in 12-hour format without leading zero.

        More portable than strftime with locale-dependent modifiers.

        Args:
            time_obj: A datetime.time object

        Returns:
            str: Formatted time string (e.g., "9:30 AM")
        """
        hour = time_obj.hour
        period = 'AM' if hour < 12 else 'PM'
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f'{hour_12}:{time_obj.strftime("%M")} {period}'

    slots = []
    for slot in time_slots:
        slot_data = {
            'id': slot.id,
            'start': slot.start_time.strftime('%H:%M'),
            'end': slot.end_time.strftime('%H:%M'),
            'start_display': format_time_display(slot.start_time),
            'end_display': format_time_display(slot.end_time)
        }
        # Include groomer name for "All Groomers" view
        if not groomer_id or groomer_id == 'all':
            slot_data['groomer_name'] = slot.groomer.name
        slots.append(slot_data)

    context = {'slots': slots, 'show_groomer': not groomer_id or groomer_id == 'all'}
    return render(request, 'mainapp/partials/time_slots_list.html', context)
