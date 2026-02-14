"""
Serializers for the grooming salon application.

This module provides serializer classes for all models, ensuring proper
field types (DecimalField for monetary/weight values) and validation.
"""

from decimal import Decimal
from rest_framework import serializers
from .models import (
    Service, Breed, BreedServiceMapping, Groomer, Customer, Appointment, TimeSlot
)


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model with proper decimal handling."""
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        min_value=Decimal('0.00')
    )

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'price', 'pricing_type',
            'duration_minutes', 'is_active', 'exempt_from_surcharge',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BreedSerializer(serializers.ModelSerializer):
    """Serializer for Breed model with proper decimal handling for pricing and weight fields."""
    base_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        min_value=Decimal('0.00')
    )
    typical_weight_min = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
        allow_null=True,
        min_value=Decimal('0.00')
    )
    typical_weight_max = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
        allow_null=True,
        min_value=Decimal('0.00')
    )
    weight_range_amount = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        allow_null=True,
        min_value=Decimal('0.01')
    )
    weight_price_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        min_value=Decimal('0.00')
    )
    start_weight = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        allow_null=True,
        min_value=Decimal('0.00')
    )

    class Meta:
        model = Breed
        fields = [
            'id', 'name', 'base_price', 'typical_weight_min',
            'typical_weight_max', 'weight_range_amount', 'weight_price_amount',
            'start_weight', 'breed_pricing_complex', 'pricing_cloned_from',
            'clone_note', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'pricing_cloned_from']


class BreedServiceMappingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    breed_name = serializers.CharField(source='breed.name', read_only=True)
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, allow_null=False, min_value=Decimal('0.00'))

    class Meta:
        model = BreedServiceMapping
        fields = [
            'id', 'breed', 'service', 'breed_name', 'service_name',
            'base_price', 'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GroomerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Groomer
        fields = [
            'id', 'name', 'bio', 'specialties', 'image',
            'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image(self, obj):
        """Get groomer image URL."""
        return obj.image.url if obj.image else None


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'email', 'phone', 'address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot model with computed fields."""
    groomer_id = serializers.IntegerField(source='groomer.id', read_only=True)
    groomer_name = serializers.CharField(source='groomer.name', read_only=True)
    date = serializers.SerializerMethodField()
    date_display = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    time_display = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(source='is_active', read_only=True)
    has_appointment = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = [
            'id', 'groomer_id', 'groomer_name', 'date', 'date_display',
            'time', 'time_display', 'is_available', 'has_appointment'
        ]

    def get_date(self, obj):
        """Format date as YYYY-MM-DD."""
        return obj.date.strftime('%Y-%m-%d')

    def get_date_display(self, obj):
        """Format date as Month DD, YYYY."""
        return obj.date.strftime('%B %d, %Y')

    def get_time(self, obj):
        """Format time as HH:MM."""
        return obj.start_time.strftime('%H:%M')

    def get_time_display(self, obj):
        """Format time as HH:MM AM/PM."""
        return obj.start_time.strftime('%I:%M %p')

    def get_has_appointment(self, obj):
        """Check if time slot has an appointment that blocks availability."""
        from .models import Appointment
        from .constants import AppointmentStatus
        return Appointment.objects.filter(
            groomer=obj.groomer,
            date=obj.date,
            time=obj.start_time,
            status__in=AppointmentStatus.BLOCKING_STATUSES
        ).exists()


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model with decimal handling for prices and weight."""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_id = serializers.IntegerField(source='service.id', read_only=True)
    groomer_name = serializers.CharField(source='groomer.name', read_only=True, allow_null=True)
    groomer_id = serializers.IntegerField(source='groomer.id', read_only=True, allow_null=True)
    preferred_groomer_name = serializers.CharField(source='preferred_groomer.name', read_only=True, allow_null=True)
    preferred_groomer_id = serializers.IntegerField(source='preferred_groomer.id', read_only=True, allow_null=True)
    dog_name = serializers.CharField(read_only=True)
    dog_breed = serializers.CharField(source='dog_breed.name', read_only=True, allow_null=True)
    dog_breed_id = serializers.IntegerField(source='dog_breed.id', read_only=True, allow_null=True)
    dog_weight = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
        allow_null=True,
        min_value=Decimal('0.00')
    )
    dog_age = serializers.CharField(read_only=True)
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    price_at_booking = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        allow_null=True,
        min_value=Decimal('0.00')
    )

    class Meta:
        model = Appointment
        fields = [
            'id', 'customer_name', 'customer_email', 'customer_phone',
            'service_name', 'service_id', 'groomer_name', 'groomer_id',
            'preferred_groomer_name', 'preferred_groomer_id',
            'dog_name', 'dog_breed', 'dog_breed_id', 'dog_weight', 'dog_age',
            'date', 'time', 'status', 'notes', 'price_at_booking'
        ]

    def get_date(self, obj):
        """Format date as YYYY-MM-DD."""
        return obj.date.strftime('%Y-%m-%d')

    def get_time(self, obj):
        """Format time as HH:MM."""
        return obj.time.strftime('%H:%M')


# =============================================================================
# Request Serializers for API Endpoints
# =============================================================================

class CalculatePriceRequestSerializer(serializers.Serializer):
    """Serializer for price calculation requests."""
    breed_id = serializers.IntegerField(required=True)
    dog_weight = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.00')
    )


class CalculateFinalPriceRequestSerializer(serializers.Serializer):
    """Serializer for final price calculation requests."""
    breed_id = serializers.IntegerField(required=True)
    service_id = serializers.IntegerField(required=True)
    dog_weight = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.00')
    )


class BookAppointmentSubmitSerializer(serializers.Serializer):
    """Serializer for appointment submission."""
    groomer_id = serializers.IntegerField(required=True)
    preferred_groomer_id = serializers.IntegerField(required=False, allow_null=True)
    breed_id = serializers.IntegerField(required=True)
    service_id = serializers.IntegerField(required=True)
    customer_name = serializers.CharField(required=True, max_length=200)
    customer_phone = serializers.CharField(required=True, max_length=20)
    customer_email = serializers.EmailField(required=True, max_length=200)
    dog_name = serializers.CharField(required=True, max_length=200)
    dog_weight = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.00')
    )
    dog_age = serializers.CharField(required=True, max_length=50)
    selected_date = serializers.DateField(required=True)
    selected_time = serializers.TimeField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


class TimeSlotCreateSerializer(serializers.Serializer):
    """Serializer for time slot creation."""
    groomer_id = serializers.IntegerField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    selected_days = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        required=False,
        default=[0, 1, 2, 3, 4, 5, 6]
    )
    time_slots = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=[]
    )

    def validate(self, attrs):
        """Validate that start date is before end date."""
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError('Start date must be before or equal to end date')
        return attrs


class TimeSlotSetSerializer(serializers.Serializer):
    """Serializer for setting time slots on a specific date."""
    groomer_id = serializers.CharField(required=True)
    date = serializers.DateField(required=True)
    time_slots = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        default=[]
    )


class TimeSlotDeleteSerializer(serializers.Serializer):
    """Serializer for deleting a specific time slot."""
    slot_id = serializers.IntegerField(required=True)


class TimeSlotDeleteDateSerializer(serializers.Serializer):
    """Serializer for deleting all time slots for a date."""
    groomer_id = serializers.IntegerField(required=True)
    date = serializers.DateField(required=True)


class AppointmentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating appointment status."""
    appointment_id = serializers.IntegerField(required=True)
    status = serializers.ChoiceField(
        choices=['pending', 'confirmed', 'completed', 'cancelled'],
        required=True
    )


class BreedCloneSerializer(serializers.Serializer):
    """Serializer for breed pricing cloning."""
    source_breed_id = serializers.IntegerField(required=True)
    target_breed_id = serializers.IntegerField(required=True)
    clone_note = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, attrs):
        """Validate that source and target breeds are different."""
        if attrs['source_breed_id'] == attrs['target_breed_id']:
            raise serializers.ValidationError('Cannot clone from the same breed')
        return attrs


class CreateBreedWithCloneSerializer(serializers.Serializer):
    """Serializer for creating a new breed with optional cloning."""
    name = serializers.CharField(required=True, max_length=200)
    clone_from_breed_id = serializers.IntegerField(required=False, allow_null=True)
    clone_note = serializers.CharField(required=False, allow_blank=True, max_length=500)
    typical_weight_min = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0.00')
    )
    typical_weight_max = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0.00')
    )


class BatchSavePricingManagementSerializer(serializers.Serializer):
    """Serializer for batch saving pricing management changes."""
    changes = serializers.ListField(
        child=serializers.ListField(),
        required=False,
        default=[]
    )


# Removed: BulkApplyWeightRangesSerializer, BulkUpdateBreedWeightSurchargesSerializer, ApplyTemplateToBreedsSerializer, UpdateBreedWeightPricingSerializer
