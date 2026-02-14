import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import (
    Appointment, Breed, BreedServiceMapping, Customer,
    Groomer, Service, TimeSlot, LegalAgreement, SiteConfig
)
from .serializers import (
    CalculatePriceRequestSerializer, CalculateFinalPriceRequestSerializer,
    BookAppointmentSubmitSerializer, TimeSlotCreateSerializer,
    TimeSlotSetSerializer, TimeSlotDeleteSerializer, TimeSlotDeleteDateSerializer,
    BreedCloneSerializer, CreateBreedWithCloneSerializer,
    BatchSavePricingManagementSerializer,
    AppointmentStatusUpdateSerializer
)
from .services import create_booking
from .utils import (
    success_response, error_response, validation_error_response,
    calculate_price_breakdown, get_available_time_slots_count,
    get_available_time_slots, has_appointment_at_time,
    parse_groomer_and_date_from_query, admin_required_for_viewsets,
    clone_breed_pricing_config, get_breeds_from_bulk_request
)
from .api_helpers import StandardResponse, StandardPagination, StandardAPIView, handle_api_errors

logger = logging.getLogger(__name__)

class BookingCalculatePriceView(StandardAPIView):
    @handle_api_errors('BookingCalculatePriceView')
    def post(self, request):
        data = self.validate_request(
            request,
            CalculatePriceRequestSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        breed_id = data['breed_id']
        dog_weight = data['dog_weight']

        breed = get_object_or_404(Breed, id=breed_id)
        services = Service.objects.filter(is_active=True)

        service_prices = [
            {
                'id': service.id,
                'name': service.name,
                'price': float(breed.get_final_price(service, dog_weight)),
                'pricing_type': service.pricing_type
            }
            for service in services
        ]

        return self.success_response(data={'services': service_prices})


class BookingCalculateFinalPriceView(StandardAPIView):
    @handle_api_errors('BookingCalculateFinalPriceView')
    def post(self, request):
        data = self.validate_request(
            request,
            CalculateFinalPriceRequestSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        breed_id = data['breed_id']
        service_id = data['service_id']
        dog_weight = data['dog_weight']

        breed = get_object_or_404(Breed, id=breed_id)
        service = get_object_or_404(Service, id=service_id)

        pricing_info = calculate_price_breakdown(breed, service, dog_weight)

        return self.success_response(data=pricing_info)


class BookingAvailableDaysView(StandardAPIView):
    @handle_api_errors('BookingAvailableDaysView')
    def get(self, request):
        groomer_id = request.query_params.get('groomer_id')

        # Get the preferred groomer if provided, otherwise check all active groomers
        if groomer_id:
            try:
                preferred_groomer = Groomer.objects.get(id=int(groomer_id), is_active=True)
            except Groomer.DoesNotExist:
                return self.error_response(
                    message='Groomer not found',
                    status_code=status.HTTP_404_NOT_FOUND
                )
        else:
            preferred_groomer = None

        # Get all active groomers for availability check
        all_groomers = Groomer.objects.filter(is_active=True)

        today = date.today()
        days = []

        # Get current customer if authenticated to enable multi-dog booking visibility
        customer = None
        if request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile

        # Use Django's built-in localized formatting (respects locale settings in settings.py)
        for i in range(14):
            current_date = today + timedelta(days=i)

            # Check availability across ALL active groomers
            total_slots = 0
            preferred_slots = 0

            for groomer in all_groomers:
                slots_count = get_available_time_slots_count(groomer, current_date, customer=customer)
                total_slots += slots_count
                if preferred_groomer and groomer.id == preferred_groomer.id:
                    preferred_slots = slots_count

            if total_slots > 0:
                # Use strftime for localized date formatting
                weekday_name = current_date.strftime('%A')
                display_date = current_date.strftime('%B %d')

                day_data = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': weekday_name,
                    'day': current_date.day,
                    'slots': total_slots,
                    'display': display_date
                }

                # Add preferred groomer slot count if checking a specific groomer
                if preferred_groomer:
                    day_data['preferred_slots'] = preferred_slots

                days.append(day_data)

        return self.success_response(data={'days': days})


class BookingTimeSlotsView(StandardAPIView):
    @handle_api_errors('BookingTimeSlotsView')
    def get(self, request):
        groomer_id = request.query_params.get('groomer_id')
        date_str = request.query_params.get('date')
        show_override = request.query_params.get('show_override', 'false').lower() == 'true'

        if not date_str:
            return self.error_response(
                message='Missing required parameter',
                errors={'date': 'Date is required'}
            )

        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return self.error_response(
                message='Invalid date format',
                errors={'date': 'Date must be in YYYY-MM-DD format'}
            )

        # Get preferred groomer if provided
        preferred_groomer = None
        if groomer_id:
            try:
                preferred_groomer = Groomer.objects.get(id=int(groomer_id), is_active=True)
            except Groomer.DoesNotExist:
                return self.error_response(
                    message='Groomer not found',
                    status_code=status.HTTP_404_NOT_FOUND
                )

        # Get primary slots from preferred groomer
        primary_slots = []

        # Get current customer if authenticated to enable multi-dog booking visibility
        customer = None
        if request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile

        if preferred_groomer:
            preferred_slots = get_available_time_slots(preferred_groomer, booking_date, customer=customer)
            primary_slots = [
                {**slot, 'is_override': False, 'is_primary': True}
                for slot in preferred_slots
            ]

        # Get override slots from other groomers if requested
        override_slots = []
        if show_override:
            # Get all active groomers except the preferred groomer
            other_groomers = Groomer.objects.filter(is_active=True)
            if preferred_groomer:
                other_groomers = other_groomers.exclude(id=preferred_groomer.id)

            # Collect time slots from other groomers
            other_slots_by_time = {}
            for groomer in other_groomers:
                groomer_slots = get_available_time_slots(groomer, booking_date, customer=customer)
                for slot in groomer_slots:
                    # Group by time
                    time_key = slot['time']
                    if time_key not in other_slots_by_time:
                        other_slots_by_time[time_key] = []
                    other_slots_by_time[time_key].append({
                        **slot,
                        'groomer_id': groomer.id,
                        'groomer_name': groomer.name,
                        'is_override': True,
                        'is_primary': False
                    })

            # For each time slot, group all groomers who have that time available
            for time_slots in other_slots_by_time.values():
                # Create a single override slot entry with multiple groomers
                override_slots.append({
                    'time': time_slots[0]['time'],
                    'display': time_slots[0]['display'],
                    'duration': time_slots[0].get('duration'),
                    'is_override': True,
                    'is_primary': False,
                    'groomers': [
                        {
                            'groomer_id': slot['groomer_id'],
                            'groomer_name': slot['groomer_name']
                        }
                        for slot in time_slots
                    ],
                    'groomer_count': len(time_slots)
                })

        # Combine primary and override slots, sort by time
        all_slots = primary_slots + override_slots
        all_slots.sort(key=lambda x: x['time'])

        return self.success_response(data={
            'slots': all_slots,
            'primary_slots_count': len(primary_slots),
            'override_slots_count': len(override_slots)
        })


class BookingSubmitView(StandardAPIView):
    @handle_api_errors('BookingSubmitView')
    def post(self, request):
        data = self.validate_request(
            request,
            BookAppointmentSubmitSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        booking_date = data['selected_date']
        booking_time = data['selected_time']

        appointment = create_booking(
            customer_email=data['customer_email'],
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            service_id=data['service_id'],
            breed_id=data['breed_id'],
            groomer_id=data['groomer_id'],
            dog_name=data['dog_name'],
            dog_weight=Decimal(str(data['dog_weight'])),
            dog_age=data['dog_age'],
            booking_date=booking_date,
            booking_time=booking_time,
            notes=data.get('notes', ''),
            preferred_groomer_id=data.get('preferred_groomer_id'),
            user=request.user if request.user.is_authenticated else None
        )

        return self.success_response(
            data={
                'appointment': {
                    'id': appointment.id,
                    'price_at_booking': float(appointment.price_at_booking),
                    'date': booking_date.strftime('%Y-%m-%d'),
                    'time': booking_time.strftime('%H:%M')
                }
            },
            message='Appointment booked successfully!'
        )

class DashboardStatsView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('DashboardStatsView')
    def get(self, request):
        stats = Appointment.objects.get_dashboard_stats(include_schedule=True)
        return self.success_response(data=stats)


class UpdateAppointmentStatusView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('UpdateAppointmentStatusView')
    def post(self, request):
        data = self.validate_request(
            request,
            AppointmentStatusUpdateSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        appointment_id = data['appointment_id']
        new_status = data['status']

        appointment = get_object_or_404(Appointment, id=appointment_id)
        appointment.status = new_status
        appointment.save()

        return self.success_response(
            data={'status': new_status},
            message=f'Appointment status updated to {new_status}'
        )


class TimeSlotManageView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('TimeSlotManageView')
    def get(self, request):
        from .serializers import TimeSlotSerializer

        groomer_id = request.query_params.get('groomer_id')
        base_query = TimeSlot.objects.all().select_related('groomer')

        if groomer_id:
            base_query = base_query.filter(groomer_id=int(groomer_id))

        slots = base_query.order_by('date', 'start_time')
        time_slots = TimeSlotSerializer(slots, many=True).data

        return self.success_response(data={'time_slots': time_slots})


class TimeSlotDeleteView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('TimeSlotDeleteView')
    def post(self, request):
        data = self.validate_request(
            request,
            TimeSlotDeleteSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        slot_id = data['slot_id']
        slot = get_object_or_404(TimeSlot, id=slot_id)

        if has_appointment_at_time(slot.groomer, slot.date, slot.start_time):
            return self.error_response(
                message='Cannot delete time slot with existing appointment',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        slot.delete()
        return self.success_response(message='Time slot deleted successfully')


class SetDayTimeSlotsView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('SetDayTimeSlotsView')
    def post(self, request):
        data = self.validate_request(
            request,
            TimeSlotSetSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        groomer_id = data['groomer_id']
        booking_date = data['date']
        time_slots = data['time_slots']

        if groomer_id == 'all':
            return self._process_all_groomers(booking_date, time_slots)
        else:
            return self._process_single_groomer(groomer_id, booking_date, time_slots)

    def _get_existing_and_new_times(self, groomer, booking_date, time_slots):
        existing_slots = TimeSlot.objects.filter(groomer=groomer, date=booking_date)
        existing_times = set(slot.start_time for slot in existing_slots)
        new_times = set(datetime.strptime(slot['start'], '%H:%M').time() for slot in time_slots)
        return existing_times, new_times

    def _validate_removed_times(self, groomer, booking_date, removed_times, groomer_name=None):
        for removed_time in removed_times:
            if has_appointment_at_time(groomer, booking_date, removed_time):
                groomer_display = f'{groomer_name} at ' if groomer_name else 'at '
                return self.error_response(
                    message=f'Cannot remove time slot with existing appointment {groomer_display}{removed_time.strftime("%I:%M %p")}',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        return None

    def _delete_existing_slots(self, groomer, booking_date):
        TimeSlot.objects.filter(groomer=groomer, date=booking_date).delete()

    def _create_time_slots(self, groomer, booking_date, time_slots):
        created_count = 0
        for slot_data in time_slots:
            start_time = datetime.strptime(slot_data['start'], '%H:%M').time()
            end_time = datetime.strptime(slot_data['end'], '%H:%M').time()

            if end_time <= start_time:
                continue

            slot, created = TimeSlot.objects.get_or_create(
                groomer=groomer,
                date=booking_date,
                start_time=start_time,
                defaults={
                    'end_time': end_time,
                    'is_active': True
                }
            )
            if created:
                created_count += 1
            else:
                # Update the end_time if it exists but might be different
                slot.end_time = end_time
                slot.is_active = True
                slot.save()
        return created_count

    def _process_groomer_slots(self, groomer, booking_date, time_slots, groomer_name=None):
        existing_times, new_times = self._get_existing_and_new_times(groomer, booking_date, time_slots)
        removed_times = existing_times - new_times

        validation_error = self._validate_removed_times(groomer, booking_date, removed_times, groomer_name)
        if validation_error:
            return validation_error, 0

        self._delete_existing_slots(groomer, booking_date)
        created_count = self._create_time_slots(groomer, booking_date, time_slots)

        return None, created_count

    def _process_all_groomers(self, booking_date, time_slots):
        groomers = Groomer.objects.filter(is_active=True)
        created_count = 0

        for groomer in groomers:
            validation_error, slots_created = self._process_groomer_slots(
                groomer, booking_date, time_slots, groomer_name=groomer.name
            )
            if validation_error:
                return validation_error
            created_count += slots_created

        groomer_display = f'{groomers.count()} groomers'
        return self.success_response(
            data={'created': created_count},
            message=f'Set {created_count} time slots for {booking_date} across {groomer_display}'
        )

    def _process_single_groomer(self, groomer_id, booking_date, time_slots):
        groomer = get_object_or_404(Groomer, id=int(groomer_id))

        validation_error, created_count = self._process_groomer_slots(groomer, booking_date, time_slots)
        if validation_error:
            return validation_error

        return self.success_response(
            data={'created': created_count},
            message=f'Set {created_count} time slots for {booking_date}'
        )


class CloneBreedPricingView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('CloneBreedPricingView')
    def post(self, request):
        data = self.validate_request(
            request,
            BreedCloneSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        source_breed_id = data['source_breed_id']
        target_breed_id = data['target_breed_id']
        clone_note = data.get('clone_note', '')

        source_breed = get_object_or_404(Breed, id=source_breed_id)
        target_breed = get_object_or_404(Breed, id=target_breed_id)

        cloned_count = clone_breed_pricing_config(source_breed, target_breed, clone_note)

        return self.success_response(
            message=f'Pricing cloned from {source_breed.name} to {target_breed.name} successfully ({cloned_count} items)'
        )


class CreateBreedWithCloneView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('CreateBreedWithCloneView')
    def post(self, request):
        data = self.validate_request(
            request,
            CreateBreedWithCloneSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        name = data['name']
        clone_from_breed_id = data.get('clone_from_breed_id')
        clone_note = data.get('clone_note', '')
        typical_weight_min = data.get('typical_weight_min')
        typical_weight_max = data.get('typical_weight_max')

        if Breed.objects.filter(name__iexact=name).exists():
            return self.error_response(
                message='Breed already exists',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        breed_data = {
            'name': name,
            'clone_note': clone_note,
        }
        if typical_weight_min:
            breed_data['typical_weight_min'] = typical_weight_min
        if typical_weight_max:
            breed_data['typical_weight_max'] = typical_weight_max

        breed = Breed.objects.create(**breed_data)

        if clone_from_breed_id:
            source_breed = get_object_or_404(Breed, id=clone_from_breed_id)
            clone_breed_pricing_config(source_breed, breed, clone_note)

        return self.success_response(
            data={'breed_id': breed.id, 'name': breed.name},
            message=f'Breed {name} created successfully' + (' with cloned pricing' if clone_from_breed_id else '')
        )


class TimeSlotCreateView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('TimeSlotCreateView')
    def post(self, request):
        data = self.validate_request(
            request,
            TimeSlotCreateSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        groomer = get_object_or_404(Groomer, id=data['groomer_id'])
        start_date = data['start_date']
        end_date = data['end_date']
        selected_days = data['selected_days']
        time_slots = data['time_slots']

        created_count = 0

        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in selected_days:
                for slot_pair in time_slots:
                    start_time = datetime.strptime(slot_pair['start'], '%H:%M').time()
                    end_time = datetime.strptime(slot_pair['end'], '%H:%M').time()

                    existing_slot = TimeSlot.objects.filter(
                        groomer=groomer,
                        date=current_date,
                        start_time=start_time,
                        end_time=end_time
                    ).first()

                    if not existing_slot:
                        TimeSlot.objects.create(
                            groomer=groomer,
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            is_active=True
                        )
                        created_count += 1

            current_date += timedelta(days=1)

        return self.success_response(
            data={'created': created_count},
            message=f'Created {created_count} time slots'
        )


class DayTimeSlotsView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('DayTimeSlotsView')
    def get(self, request):
        groomer_id = request.query_params.get('groomer_id')
        date_str = request.query_params.get('date')

        if not groomer_id or not date_str:
            return self.error_response(
                message='Missing required parameters',
                errors={'groomer_id': 'Groomer ID is required', 'date': 'Date is required'}
            )

        groomer = get_object_or_404(Groomer, id=int(groomer_id))
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        time_slots = TimeSlot.objects.filter(
            groomer=groomer,
            date=booking_date
        ).order_by('start_time')

        slots = [
            {
                'start': slot.start_time.strftime('%H:%M'),
                'end': slot.end_time.strftime('%H:%M'),
                'id': slot.id
            }
            for slot in time_slots
        ]

        return self.success_response(data={'slots': slots})


class TimeSlotDeleteDateView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('TimeSlotDeleteDateView')
    def post(self, request):
        data = self.validate_request(
            request,
            TimeSlotDeleteDateSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        groomer_id = data['groomer_id']
        booking_date = data['date']

        groomer = get_object_or_404(Groomer, id=groomer_id)

        appointment_count = Appointment.objects.filter(
            groomer=groomer,
            date=booking_date,
            status__in=['pending', 'confirmed']
        ).count()

        if appointment_count > 0:
            return self.error_response(
                message=f'Cannot delete time slots with {appointment_count} existing appointment(s)',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        deleted_count = TimeSlot.objects.filter(
            groomer=groomer,
            date=booking_date
        ).delete()[0]

        return self.success_response(
            message=f'Deleted {deleted_count} time slot(s)'
        )


class BatchSavePricingManagementView(StandardAPIView):
    @admin_required_for_viewsets
    @handle_api_errors('BatchSavePricingManagementView')
    def post(self, request):
        data = self.validate_request(
            request,
            BatchSavePricingManagementSerializer,
            error_message='Validation failed'
        )
        if isinstance(data, Response):
            return data

        changes = data.get('changes', [])

        from django.db import transaction

        with transaction.atomic():
            for change_key, change_data in changes:
                if change_key.startswith('breed_name_'):
                    breed_id = change_key.replace('breed_name_', '')
                    breed = get_object_or_404(Breed, id=int(breed_id))
                    breed.name = change_data['value']
                    breed.save()

                elif change_key.startswith('base_price_'):
                    breed_id = change_key.replace('base_price_', '')
                    first_service = Service.objects.first()
                    if first_service:
                        BreedServiceMapping.objects.update_or_create(
                            breed_id=int(breed_id),
                            service=first_service,
                            defaults={'base_price': Decimal(str(change_data['value']))}
                        )

        return self.success_response(
            message=f'{len(changes)} changes saved successfully'
        )


class BatchDayTimeSlotsView(StandardAPIView):
    """
    Batch endpoint to fetch all time slots for multiple groomers across multiple dates.
    Reduces API calls from N*M calls to a single request.
    """
    @admin_required_for_viewsets
    @handle_api_errors('BatchDayTimeSlotsView')
    def get(self, request):
        groomer_ids = request.query_params.get('groomer_ids')
        dates = request.query_params.get('dates')

        if not groomer_ids or not dates:
            return self.error_response(
                message='Missing required parameters',
                errors={
                    'groomer_ids': 'Groomer IDs are required (comma-separated)',
                    'dates': 'Dates are required (comma-separated)'
                }
            )

        try:
            groomer_id_list = [int(gid.strip()) for gid in groomer_ids.split(',')]
            date_list = []
            for d in dates.split(','):
                date_string = d.strip()
                date_list.append(datetime.strptime(date_string, '%Y-%m-%d').date())
        except (ValueError, AttributeError) as e:
            return self.error_response(
                message='Invalid parameter format',
                errors={'detail': f'Failed to parse groomer_ids or dates: {str(e)}'}
            )

        # Fetch all time slots in a single database query
        all_slots = TimeSlot.objects.filter(
            groomer_id__in=groomer_id_list,
            date__in=date_list
        ).select_related('groomer').order_by('groomer_id', 'date', 'start_time')

        # Build response grouped by groomer and date
        result = {}

        for slot in all_slots:
            groomer_id = slot.groomer_id
            date_str = slot.date.strftime('%Y-%m-%d')

            if groomer_id not in result:
                result[groomer_id] = {}

            if date_str not in result[groomer_id]:
                result[groomer_id][date_str] = {
                    'groomer_id': groomer_id,
                    'groomer_name': slot.groomer.name,
                    'date': date_str,
                    'slots': []
                }

            result[groomer_id][date_str]['slots'].append({
                'start': slot.start_time.strftime('%H:%M'),
                'end': slot.end_time.strftime('%H:%M'),
                'id': slot.id
            })

        # Flatten result to match frontend expectations
        # Response format: [{ groomer_id, groomer_name, date: 'YYYY-MM-DD', slots: [] }, ...]
        flat_result = []
        for groomer_id, dates_dict in result.items():
            for date_str, date_data in dates_dict.items():
                flat_result.append(date_data)

        return self.success_response(data={'time_slots': flat_result})


class ActiveAgreementView(StandardAPIView):
    """API endpoint for getting the currently active legal agreement."""

    @handle_api_errors('ActiveAgreementView')
    def get(self, request):
        """Get the currently active legal agreement.

        Returns:
            - id: The ID of the agreement
            - title: Title of the agreement
            - content: Full text of the agreement
            - effective_date: When this agreement becomes effective
            - is_required: Whether customers must sign (True if active, False if no active agreement)

        If no active agreement exists, returns empty values with is_required=False.
        """
        agreement = LegalAgreement.get_active_agreement()

        if agreement:
            return self.success_response(data={
                'id': agreement.id,
                'title': agreement.title,
                'content': agreement.content,
                'effective_date': agreement.effective_date.strftime('%Y-%m-%d') if agreement.effective_date else None,
                'is_required': True
            })
        else:
            return self.success_response(data={
                'id': None,
                'title': None,
                'content': None,
                'effective_date': None,
                'is_required': False
            })


class CustomerDogsView(StandardAPIView):
    """API endpoint for getting the authenticated customer's dogs with appointment status."""

    @handle_api_errors('CustomerDogsView')
    def get(self, request):
        """Get the authenticated customer's dogs.

        Returns a list of the customer's dogs with information about whether
        they have a pending or confirmed appointment. Dogs with active appointments
        are marked as unavailable for booking.

        Returns:
            - dogs: List of dog profiles with:
                - id: Dog ID
                - name: Dog's name
                - breed_id: Breed ID
                - breed_name: Breed name
                - weight: Dog's weight
                - age: Dog's age
                - has_active_appointment: True if dog has pending/confirmed appointment
        """
        # Check if user is authenticated and is a customer
        if not request.user.is_authenticated or request.user.user_type != 'customer':
            return self.error_response(
                message='Authentication required',
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Get customer for the user
        try:
            from users.models import User
            customer = request.user.customer_profile
        except AttributeError:
            return self.error_response(
                message='Customer profile not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Get all dogs for this customer
        from mainapp.models import Dog, Appointment
        dogs = Dog.objects.filter(owner=request.user)

        # Get all pending/confirmed appointments for this customer
        active_appointments = Appointment.objects.filter(
            customer=customer,
            status__in=['pending', 'confirmed']
        ).values_list('dog_name', flat=True)

        # Build response with appointment status
        dogs_data = []
        for dog in dogs:
            has_active_appointment = dog.name in active_appointments

            dogs_data.append({
                'id': dog.id,
                'name': dog.name,
                'breed_id': dog.breed.id if dog.breed else None,
                'breed_name': dog.breed.name if dog.breed else None,
                'weight': float(dog.weight) if dog.weight else None,
                'age': dog.age or '',
                'notes': dog.notes or '',
                'has_active_appointment': has_active_appointment
            })

        return self.success_response(data={'dogs': dogs_data})


class SiteConfigUpdateView(StandardAPIView):
    """API endpoint for updating site configuration settings like max_dogs_per_day."""

    @handle_api_errors('SiteConfigUpdateView')
    def post(self, request):
        """Update site configuration settings.

        Accepts:
            - max_dogs_per_day: Maximum number of dogs a customer can book in a single day (1-20)

        Returns:
            - success: True if update was successful
            - message: Success message
        """
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            return self.error_response(
                message='Admin access required',
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Get the active site configuration
        site_config = SiteConfig.get_active_config()

        if not site_config:
            return self.error_response(
                message='No active site configuration found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Validate and update max_dogs_per_day
        max_dogs_per_day = request.data.get('max_dogs_per_day')

        if not max_dogs_per_day or not isinstance(max_dogs_per_day, int) or max_dogs_per_day < 1 or max_dogs_per_day > 20:
            return self.error_response(
                message='max_dogs_per_day must be an integer between 1 and 20',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Update the setting
        site_config.max_dogs_per_day = max_dogs_per_day
        site_config.save()

        logger.info(f"SiteConfig updated: max_dogs_per_day = {max_dogs_per_day} by user {request.user.username}")

        return self.success_response(
            data={
                'success': True,
                'message': f'Settings updated successfully. Maximum dogs per day is now {max_dogs_per_day}.'
            }
        )
