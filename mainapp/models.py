"""
Models module for the grooming salon application.

This module contains all the database models for the salon application,
including breeds, services, customers, appointments, groomers, and
pricing-related models.
"""

from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal


class Breed(models.Model):
    """Model representing a dog breed with pricing information."""

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Name of the dog breed"
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True,
        blank=True,
        help_text="Base starting price for this breed (for services requiring bath/grooming)"
    )
    typical_weight_min = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Typical minimum weight (lbs) for default pricing reference"
    )
    typical_weight_max = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Typical maximum weight (lbs) for default pricing reference"
    )
    weight_range_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Weight increment size in lbs (e.g., 10 lbs)"
    )
    weight_price_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Additional charge per weight increment (e.g., $15 per 10 lbs)"
    )
    start_weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Starting weight threshold in lbs (e.g., 15 lbs)"
    )
    breed_pricing_complex = models.BooleanField(
        default=False,
        help_text="Mark if this breed has complex pricing rules requiring manual review"
    )
    pricing_cloned_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cloned_to',
        help_text="If pricing was cloned from another breed"
    )
    clone_note = models.TextField(
        blank=True,
        help_text="Note about why pricing was cloned from another breed"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Breed'
        verbose_name_plural = 'Breeds'

    def __str__(self):
        return self.name

    def clean(self):
        """Validate that breed pricing configuration is complete or empty."""
        pricing_fields = [
            self.start_weight,
            self.weight_range_amount,
            self.weight_price_amount
        ]

        has_pricing = any(field is not None and field != 0 for field in pricing_fields)

        if has_pricing:
            mandatory_fields = [
                ('start_weight', self.start_weight),
                ('weight_range_amount', self.weight_range_amount),
                ('weight_price_amount', self.weight_price_amount)
            ]

            missing = [name for name, value in mandatory_fields
                       if value is None or value == 0]

            if missing:
                raise ValidationError({
                    'start_weight': 'If using weight-based pricing, all pricing fields must be set together.',
                    'weight_range_amount': f'Missing or zero. Required fields: {", ".join(missing)}',
                    'weight_price_amount': f'Missing or zero. Required fields: {", ".join(missing)}',
                })

    def calculate_weight_surcharge(self, dog_weight):
        """Calculate weight surcharge for a given dog weight.

        Uses integer division to determine number of weight increments above threshold.
        This creates discrete pricing thresholds (e.g., every 10 lbs adds $15).

        Args:
            dog_weight: Decimal weight in lbs

        Returns:
            Decimal: Weight surcharge amount (0 if not configured or dog below threshold)
        """
        if dog_weight is None:
            return Decimal('0')

        if not (self.start_weight and self.weight_range_amount and self.weight_price_amount):
            return Decimal('0')

        if dog_weight <= self.start_weight:
            return Decimal('0')

        excess_weight = dog_weight - self.start_weight
        num_increments = excess_weight // self.weight_range_amount
        weight_surcharge = num_increments * self.weight_price_amount

        return weight_surcharge

    def get_service_price(self, service):
        """Get breed-specific price for a service, or breed base price for base_required services."""
        if service.pricing_type == 'base_required':
            return self.base_price
        else:
            try:
                mapping = self.service_mappings.get(service=service)
                if mapping.is_available:
                    return mapping.base_price
            except BreedServiceMapping.DoesNotExist:
                pass
            return service.price

    def get_final_price(self, service, dog_weight):
        """Calculate final price for a service and dog weight.

        The pricing logic:
        1. For base_required services: breed_base_price + weight_surcharge + service.addon_amount
        2. For standalone services: breed_service_price or service.price + weight_surcharge (if not exempt)
        3. Calculate weight surcharge using breed-specific formula
        4. Check if service is exempt from surcharge

        Args:
            service: Service object
            dog_weight: Decimal weight in lbs

        Returns:
            Decimal: Final price
        """
        weight_surcharge = Decimal('0')

        if not service.exempt_from_surcharge:
            weight_surcharge = self.calculate_weight_surcharge(dog_weight)

        if service.pricing_type == 'base_required':
            return self.base_price + weight_surcharge + service.price
        else:
            base_price = self.get_service_price(service)
            return base_price + weight_surcharge


class BreedServiceMapping(models.Model):
    """Model mapping breeds to services with custom pricing."""

    breed = models.ForeignKey(
        Breed,
        on_delete=models.CASCADE,
        related_name='service_mappings',
        db_index=True
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='breed_mappings',
        db_index=True
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether this service is offered for this breed"
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Custom service price (for standalone services only)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['breed', 'service']
        ordering = ['breed__name', 'service__name']
        verbose_name = 'Breed Service Mapping'
        verbose_name_plural = 'Breed Service Mappings'

    def __str__(self):
        status = "Available" if self.is_available else "Not Available"
        return f"{self.breed.name} - {self.service.name}: {status} @ ${self.base_price}"


class Service(models.Model):
    """Model representing a service offered by the salon."""

    PRICING_TYPE_CHOICES = [
        ('base_required', 'Base Required (uses breed base price)'),
        ('standalone', 'Standalone (direct pricing)'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Service name"
    )
    description = models.TextField(help_text="Service description")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Price for standalone services or add-on amount for base-required services"
    )
    pricing_type = models.CharField(
        max_length=20,
        choices=PRICING_TYPE_CHOICES,
        default='base_required',
        help_text="How this service is priced"
    )
    duration_minutes = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Service duration in minutes"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    exempt_from_surcharge = models.BooleanField(
        default=False,
        help_text="If checked, this service won't apply weight range surcharges"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    def __str__(self):
        return f"{self.name} - ${self.price} ({self.get_pricing_type_display()})"


class Customer(models.Model):
    """Model representing a salon customer.

    This model represents the business entity for a customer. It can be linked
    to a User account (for registered customers) or exist independently (for guest bookings).
    """

    user = models.OneToOneField(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile',
        db_index=True,
        help_text="Linked User account (null for guest bookings)"
    )
    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Customer's full name (auto-populated from User if linked)"
    )
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Customer's email address (auto-populated from User if linked)"
    )
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Phone number must be entered in the format: +1234567890 or 1234567890. Up to 15 digits allowed.'
        )],
        help_text="Customer's phone number (auto-populated from User if linked)"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Customer's address"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        if self.user:
            return f"{self.name} ({self.phone}) [Account: {self.user.username}]"
        return f"{self.name} ({self.phone}) [Guest]"

    def save(self, *args, **kwargs):
        """Auto-populate fields from linked User when saving."""
        if self.user:
            # Populate name from User if not set
            if not self.name:
                self.name = self.user.get_full_name() or self.user.username
            # Populate email from User if not set
            if not self.email:
                self.email = self.user.email
            # Populate phone from User if not set
            if not self.phone:
                self.phone = self.user.phone or ''
        super().save(*args, **kwargs)


class AppointmentManager(models.Manager):
    """Custom manager for Appointment model with dashboard statistics."""

    def get_dashboard_stats(self, include_schedule=False):
        """Get dashboard statistics for admin overview.

        Args:
            include_schedule: If True, includes today's schedule in the response.

        Returns:
            dict: Dictionary containing count stats and optionally today's schedule.
                - today_appointments: Number of appointments scheduled for today
                - pending_appointments: Number of pending appointments
                - total_customers: Total number of customers
                - monthly_revenue: Revenue from confirmed/completed appointments this month
                - today_schedule: List of today's appointments (if include_schedule=True)
        """
        today = date.today()
        start_of_month = today.replace(day=1)

        stats = {
            'today_appointments': self.filter(date=today).count(),
            'pending_appointments': self.filter(status='pending').count(),
            'total_customers': Customer.objects.count(),
            'monthly_revenue': self.filter(
                date__gte=start_of_month,
                date__lte=today,
                status__in=['confirmed', 'completed']
            ).aggregate(
                total=models.Sum('price_at_booking')
            )['total'] or Decimal('0.00'),
        }

        if include_schedule:
            stats['today_schedule'] = list(self.filter(
                date=today
            ).values(
                'id',
                'customer__name',
                'service__name',
                'dog_name',
                'time',
                'status'
            ).order_by('time'))

        return stats


class Appointment(models.Model):
    """Model representing an appointment at the salon."""

    objects = AppointmentManager()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='appointments',
        db_index=True,
        help_text="Customer for this appointment"
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        db_index=True,
        help_text="Optional User account (null for guest bookings)"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointments',
        help_text="Service being booked"
    )
    groomer = models.ForeignKey(
        'Groomer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        help_text="Groomer performing the service (this represents the actual groomer assigned to the appointment)"
    )
    preferred_groomer = models.ForeignKey(
        'Groomer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_appointments',
        help_text="Customer's preferred groomer (may differ from actual groomer if override slot was selected)"
    )
    dog_name = models.CharField(
        max_length=100,
        help_text="Name of the dog"
    )
    dog_breed = models.ForeignKey(
        Breed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        help_text="Breed of the dog"
    )
    dog_size = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Size of the dog"
    )
    dog_weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Dog's weight in lbs (measured at shop)"
    )
    dog_age = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Dog's age for our records"
    )
    date = models.DateField(
        db_index=True,
        help_text="Date of the appointment"
    )
    time = models.TimeField(
        db_index=True,
        help_text="Time of the appointment"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Appointment status"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the appointment"
    )
    price_at_booking = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Price at time of booking (for historical accuracy)"
    )
    agreement_version = models.ForeignKey(
        'LegalAgreement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        help_text="The legal agreement version the customer accepted"
    )
    agreement_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the customer accepted the agreement"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'

    def __str__(self):
        return f"{self.customer.name} - {self.service.name} on {self.date} at {self.time}"


class Groomer(models.Model):
    """Model representing a groomer at the salon."""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Groomer's full name"
    )
    bio = models.TextField(
        help_text="Professional biography"
    )
    specialties = models.CharField(
        max_length=200,
        help_text="Comma-separated specialties"
    )
    image = models.ImageField(
        upload_to='groomer_images/%Y/%m/',
        blank=True,
        null=True,
        help_text="Upload groomer's photo"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this groomer is currently active"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Groomer'
        verbose_name_plural = 'Groomers'

    def __str__(self):
        return self.name

    def clean(self):
        """Validate groomer data."""
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Groomer name cannot be empty.'})


class TimeSlot(models.Model):
    """Model representing available time slots for appointments."""

    groomer = models.ForeignKey(
        'Groomer',
        on_delete=models.CASCADE,
        related_name='time_slots',
        db_index=True,
        help_text="Groomer for this time slot"
    )
    date = models.DateField(
        db_index=True,
        help_text="Date for this time slot"
    )
    start_time = models.TimeField(
        db_index=True,
        help_text="Start time (e.g., 09:00)"
    )
    end_time = models.TimeField(
        help_text="End time (e.g., 10:00)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this slot is available for booking"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['groomer', 'date', 'start_time']
        ordering = ['date', 'start_time']
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'

    def __str__(self):
        return f"{self.groomer.name} - {self.date} {self.start_time} to {self.end_time}"

    def clean(self):
        """Validate time slot data."""
        if self.start_time >= self.end_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})


class Dog(models.Model):
    """Model representing a customer's dog profile."""

    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Dog's name"
    )
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='dogs',
        db_index=True,
        help_text="Customer who owns this dog"
    )
    breed = models.ForeignKey(
        Breed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dogs',
        db_index=True,
        help_text="Breed of the dog"
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
        help_text="Dog's weight in lbs"
    )
    age = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Dog's age (e.g., '2 years', '6 months')"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the dog"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Dog'
        verbose_name_plural = 'Dogs'

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class DogDeletionRequest(models.Model):
    """Model representing a customer's request to delete a dog profile."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name='deletion_requests',
        help_text="Dog profile requested for deletion"
    )
    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='dog_deletion_requests',
        help_text="User who requested the deletion"
    )
    reason = models.TextField(
        help_text="Reason for requesting deletion"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of the deletion request"
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Admin notes about this request"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dog Deletion Request'
        verbose_name_plural = 'Dog Deletion Requests'

    def __str__(self):
        return f"Delete request for {self.dog.name} - {self.get_status_display()}"


class LegalAgreement(models.Model):
    """Model representing a legal agreement that customers must accept when booking."""

    title = models.CharField(
        max_length=200,
        help_text="Title of the legal agreement"
    )
    content = models.TextField(
        help_text="Full text of the legal agreement"
    )
    effective_date = models.DateField(
        db_index=True,
        help_text="Date when this agreement version becomes effective"
    )
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this is the currently active agreement version"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date']
        verbose_name = 'Legal Agreement'
        verbose_name_plural = 'Legal Agreements'

    def __str__(self):
        active_label = " [ACTIVE]" if self.is_active else ""
        return f"{self.title}{active_label} - Effective {self.effective_date}"

    @classmethod
    def get_active_agreement(cls):
        """Get the currently active legal agreement."""
        return cls.objects.filter(is_active=True).first()


class SiteConfig(models.Model):
    """Model representing site-wide configuration including business hours and contact info."""

    BUSINESS_HOUR_CHOICES = [
        (0, 'Closed'),
        (8, '8:00 AM'),
        (9, '9:00 AM'),
        (10, '10:00 AM'),
        (11, '11:00 AM'),
        (12, '12:00 PM'),
        (13, '1:00 PM'),
        (14, '2:00 PM'),
        (15, '3:00 PM'),
        (16, '4:00 PM'),
        (17, '5:00 PM'),
        (18, '6:00 PM'),
        (19, '7:00 PM'),
        (20, '8:00 PM'),
        (21, '9:00 PM'),
    ]

    # Contact Information
    business_name = models.CharField(
        max_length=200,
        default="Shampooches",
        db_index=True,
        help_text="Business name displayed on the website"
    )
    address = models.TextField(help_text="Business address")
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Phone number must be entered in the format: +1234567890 or 1234567890. Up to 15 digits allowed.'
        )],
        help_text="Business phone number"
    )
    email = models.EmailField(help_text="Business email address")

    # Business Hours
    monday_open = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=8, help_text="Monday opening time")
    monday_close = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=18, help_text="Monday closing time")
    tuesday_open = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=8, help_text="Tuesday opening time")
    tuesday_close = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=18, help_text="Tuesday closing time")
    wednesday_open = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=8, help_text="Wednesday opening time")
    wednesday_close = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=18, help_text="Wednesday closing time")
    thursday_open = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=8, help_text="Thursday opening time")
    thursday_close = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=18, help_text="Thursday closing time")
    friday_open = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=8, help_text="Friday opening time")
    friday_close = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=18, help_text="Friday closing time")
    saturday_open = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=9, help_text="Saturday opening time")
    saturday_close = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=17, help_text="Saturday closing time")
    sunday_open = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=10, help_text="Sunday opening time")
    sunday_close = models.IntegerField(choices=BUSINESS_HOUR_CHOICES, default=16, help_text="Sunday closing time")

    # Booking Configuration
    max_dogs_per_day = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of dogs a customer can book in a single day"
    )

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configurations'

    def __str__(self):
        return f"{self.business_name} - Site Config"

    def get_hours_display(self):
        """Get formatted business hours for all days."""
        hours = []
        days = [
            ('Monday', self.monday_open, self.monday_close),
            ('Tuesday', self.tuesday_open, self.tuesday_close),
            ('Wednesday', self.wednesday_open, self.wednesday_close),
            ('Thursday', self.thursday_open, self.thursday_close),
            ('Friday', self.friday_open, self.friday_close),
            ('Saturday', self.saturday_open, self.saturday_close),
            ('Sunday', self.sunday_open, self.sunday_close),
        ]
        for day_name, open_time, close_time in days:
            if open_time == 0:
                hours.append(f"{day_name}: Closed")
            else:
                am_pm_open = "AM" if open_time < 12 else "PM"
                open_display = f"{open_time if open_time <= 12 else open_time - 12}:00 {am_pm_open}"

                am_pm_close = "AM" if close_time < 12 else "PM"
                close_display = f"{close_time if close_time <= 12 else close_time - 12}:00 {am_pm_close}"

                hours.append(f"{day_name}: {open_display} - {close_display}")
        return hours

    @classmethod
    def get_active_config(cls):
        """Get the active site configuration."""
        return cls.objects.filter(is_active=True).first()

    def clean(self):
        """Validate site configuration data."""
        day_pairs = [
            (self.monday_open, self.monday_close, 'Monday'),
            (self.tuesday_open, self.tuesday_close, 'Tuesday'),
            (self.wednesday_open, self.wednesday_close, 'Wednesday'),
            (self.thursday_open, self.thursday_close, 'Thursday'),
            (self.friday_open, self.friday_close, 'Friday'),
            (self.saturday_open, self.saturday_close, 'Saturday'),
            (self.sunday_open, self.sunday_close, 'Sunday'),
        ]

        for open_time, close_time, day_name in day_pairs:
            if open_time != 0 and close_time != 0 and open_time >= close_time:
                raise ValidationError(
                    {f'{day_name.lower()}_close': f'{day_name} closing time must be after opening time.'}
                )


class MessageThread(models.Model):
    """Model representing a conversation thread between a customer and staff."""

    customer = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='customer_threads',
        db_index=True,
        help_text="Customer user who initiated this thread"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Subject/topic of this conversation"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this thread is active (can receive new messages)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Message Thread'
        verbose_name_plural = 'Message Threads'

    def __str__(self):
        return f"{self.customer.username} - {self.subject}"

    def get_last_message(self):
        """Get the most recent message in this thread."""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """Model representing an individual message in a thread."""

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True,
        help_text="Thread this message belongs to"
    )
    sender = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='sent_messages',
        db_index=True,
        help_text="User who sent this message"
    )
    content = models.TextField(
        help_text="Message content"
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this message has been read by recipients"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.sender.username}: {preview}"


class ThreadView(models.Model):
    """Model tracking which users are currently viewing a message thread."""

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='active_views',
        db_index=True,
        help_text="Thread being viewed"
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='thread_views',
        db_index=True,
        help_text="User viewing the thread"
    )
    last_seen_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time this user was confirmed to be viewing the thread"
    )

    class Meta:
        unique_together = ['thread', 'user']
        verbose_name = 'Thread View'
        verbose_name_plural = 'Thread Views'

    def __str__(self):
        return f"{self.user.username} viewing {self.thread.subject}"

    @classmethod
    def get_active_viewers(cls, thread, timeout_seconds=30):
        """Get active viewers for a thread (those who've been active within timeout)."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff_time = timezone.now() - timedelta(seconds=timeout_seconds)
        return cls.objects.filter(thread=thread, last_seen_at__gte=cutoff_time).select_related('user')


class TypingIndicator(models.Model):
    """Model tracking which users are currently typing in a message thread."""

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='typing_indicators',
        db_index=True,
        help_text="Thread where typing is happening"
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='typing_activity',
        db_index=True,
        help_text="User who is typing"
    )
    last_typed_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time this user was confirmed to be typing"
    )

    class Meta:
        unique_together = ['thread', 'user']
        verbose_name = 'Typing Indicator'
        verbose_name_plural = 'Typing Indicators'

    def __str__(self):
        return f"{self.user.username} typing in {self.thread.subject}"

    @classmethod
    def get_active_typers(cls, thread, timeout_seconds=5):
        """Get active typers for a thread (those who've been typing within timeout)."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff_time = timezone.now() - timedelta(seconds=timeout_seconds)
        return cls.objects.filter(thread=thread, last_typed_at__gte=cutoff_time).select_related('user')
