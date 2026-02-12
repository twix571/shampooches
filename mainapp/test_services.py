from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Appointment, Breed, Customer, Groomer, Service
from .services import create_booking


class CreateBookingTestCase(TestCase):
    """Test cases for the create_booking service function."""

    def setUp(self):
        """Set up test data."""
        # Create a groomer
        self.groomer = Groomer.objects.create(
            name='Test Groomer',
            bio='Test bio',
            specialties='Test specialties',
            is_active=True
        )

        # Create a breed with pricing structure
        self.breed = Breed.objects.create(
            name='Golden Retriever',
            base_price=Decimal('50.00'),
            start_weight=Decimal('15'),
            weight_range_amount=Decimal('10'),
            weight_price_amount=Decimal('15'),
            is_active=True
        )

        # Create a base_required service
        self.base_service = Service.objects.create(
            name='Bath & Groom',
            description='Full bath and grooming',
            price=Decimal('20.00'),  # Add-on amount
            pricing_type='base_required',
            duration_minutes=60,
            exempt_from_surcharge=False,
            is_active=True
        )

        # Create a standalone service
        self.standalone_service = Service.objects.create(
            name='Nail Trimming',
            description='Nail trimming only',
            price=Decimal('15.00'),
            pricing_type='standalone',
            duration_minutes=15,
            exempt_from_surcharge=True,
            is_active=True
        )

    def test_create_booking_new_customer(self):
        """Test booking creation with a new customer."""
        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='new@example.com',
            customer_name='Jane Doe',
            customer_phone='5559876543',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Rex',
            dog_weight=Decimal('25.0'),  # Will incur surcharge: (25-15)/10 = 1 increment
            dog_age='2 years',
            booking_date=tomorrow,
            booking_time=time(14, 0),
            notes='Special requests'
        )

        # Verify appointment was created
        self.assertIsNotNone(appointment.id)
        self.assertEqual(appointment.dog_name, 'Rex')
        self.assertEqual(appointment.dog_weight, Decimal('25.0'))
        self.assertEqual(appointment.customer.email, 'new@example.com')
        self.assertEqual(appointment.customer.name, 'Jane Doe')
        self.assertEqual(appointment.status, 'pending')

    def test_create_booking_existing_customer(self):
        """Test that existing customer is updated with new info."""
        # Create customer first
        Customer.objects.create(
            email='existing@example.com',
            name='Old Customer Name',
            phone='5551112222'
        )

        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='existing@example.com',
            customer_name='New Customer Name',  # Should update
            customer_phone='5559998888',  # Should update
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Max',
            dog_weight=Decimal('30.0'),
            dog_age='3 years',
            booking_date=tomorrow,
            booking_time=time(11, 0)
        )

        # Verify customer was updated (not just reused)
        self.assertEqual(appointment.customer.email, 'existing@example.com')
        self.assertEqual(appointment.customer.name, 'New Customer Name')  # Updated name
        self.assertEqual(appointment.customer.phone, '5559998888')  # Updated phone

    def test_base_required_pricing_calculation(self):
        """Test price calculation for base_required services."""
        # Dog weight: 20 lbs
        # Surcharge: (20 - 15) / 10 = 0.5 increments = $0 (floor division)
        # Total = base_price (50) + surcharge (0) + service_price (20) = $70

        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='price1@example.com',
            customer_name='Price Tester',
            customer_phone='5551111111',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Dog1',
            dog_weight=Decimal('20.0'),
            dog_age='1 year',
            booking_date=tomorrow,
            booking_time=time(9, 0)
        )

        # Price should be: 50 (base) + 0 (surcharge) + 20 (service) = 70
        self.assertEqual(appointment.price_at_booking, Decimal('70.00'))

    def test_standalone_pricing_no_surcharge(self):
        """Test standalone service with surcharge exemption."""
        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='standalone@example.com',
            customer_name='Stand Alone',
            customer_phone='5552222222',
            service_id=self.standalone_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Nails',
            dog_weight=Decimal('40.0'),  # Weight shouldn't matter
            dog_age='5 years',
            booking_date=tomorrow,
            booking_time=time(10, 0)
        )

        # Exempt from surcharge, so should just be service price
        self.assertEqual(appointment.price_at_booking, Decimal('15.00'))

    def test_weight_surcharge_calculation(self):
        """Test weight surcharge calculation."""
        # Dog weight: 35 lbs
        # Surcharge: (35 - 15) / 10 = 2 increments = $30
        # Total = base_price (50) + surcharge (30) + service_price (20) = $100

        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='surcharge@example.com',
            customer_name='Surcharge Tester',
            customer_phone='5553333333',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='BigDog',
            dog_weight=Decimal('35.0'),
            dog_age='4 years',
            booking_date=tomorrow,
            booking_time=time(9, 0)
        )

        # Price should be: 50 (base) + 30 (surcharge) + 20 (service) = 100
        self.assertEqual(appointment.price_at_booking, Decimal('100.00'))

    def test_no_surcharge_below_threshold(self):
        """Test that dogs below start_weight don't get surcharge."""
        # Dog weight: 10 lbs (below 15 start_weight)
        # No surcharge should apply

        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='small@example.com',
            customer_name='Small Dog Owner',
            customer_phone='5554444444',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Tiny',
            dog_weight=Decimal('10.0'),
            dog_age='1 year',
            booking_date=tomorrow,
            booking_time=time(13, 0)
        )

        # Price should be: 50 (base) + 0 (surcharge) + 20 (service) = 70
        self.assertEqual(appointment.price_at_booking, Decimal('70.00'))

    def test_nonexistent_service_raises_404(self):
        """Test that booking with non-existent service raises Http404."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(Exception):  # Http404 is raised
            create_booking(
                customer_email='test@example.com',
                customer_name='Test',
                customer_phone='5551234567',
                service_id=999999,  # Non-existent
                breed_id=self.breed.id,
                groomer_id=self.groomer.id,
                dog_name='Dog',
                dog_weight=Decimal('20.0'),
                dog_age='2 years',
                booking_date=tomorrow,
                booking_time=time(10, 0)
            )

    def test_nonexistent_breed_raises_404(self):
        """Test that booking with non-existent breed raises Http404."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(Exception):  # Http404 is raised
            create_booking(
                customer_email='test@example.com',
                customer_name='Test',
                customer_phone='5551234567',
                service_id=self.base_service.id,
                breed_id=999999,  # Non-existent
                groomer_id=self.groomer.id,
                dog_name='Dog',
                dog_weight=Decimal('20.0'),
                dog_age='2 years',
                booking_date=tomorrow,
                booking_time=time(10, 0)
            )

    def test_nonexistent_groomer_raises_404(self):
        """Test that booking with non-existent groomer raises Http404."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(Exception):  # Http404 is raised
            create_booking(
                customer_email='test@example.com',
                customer_name='Test',
                customer_phone='5551234567',
                service_id=self.base_service.id,
                breed_id=self.breed.id,
                groomer_id=999999,  # Non-existent
                dog_name='Dog',
                dog_weight=Decimal('20.0'),
                dog_age='2 years',
                booking_date=tomorrow,
                booking_time=time(10, 0)
            )

    def test_appointment_count_increments(self):
        """Test that appointment count increases after booking."""
        initial_count = Appointment.objects.count()

        tomorrow = date.today() + timedelta(days=1)
        create_booking(
            customer_email='count@example.com',
            customer_name='Counter',
            customer_phone='5555555555',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='CountDog',
            dog_weight=Decimal('20.0'),
            dog_age='2 years',
            booking_date=tomorrow,
            booking_time=time(10, 0)
        )

        self.assertEqual(Appointment.objects.count(), initial_count + 1)

    def test_empty_notes_allowed(self):
        """Test that empty notes are allowed."""
        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='notes@example.com',
            customer_name='Notes Tester',
            customer_phone='5556666666',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Buddy',
            dog_weight=Decimal('20.0'),
            dog_age='2 years',
            booking_date=tomorrow,
            booking_time=time(10, 0),
            notes=''  # Empty notes
        )

        self.assertEqual(appointment.notes, '')

    def test_custom_notes_stored(self):
        """Test that custom notes are stored correctly."""
        custom_note = 'Please trim nails short, dog is nervous'
        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='notes@example.com',
            customer_name='Notes Tester',
            customer_phone='5556666666',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Buddy',
            dog_weight=Decimal('20.0'),
            dog_age='2 years',
            booking_date=tomorrow,
            booking_time=time(10, 0),
            notes=custom_note
        )

        self.assertEqual(appointment.notes, custom_note)

    def test_default_status_pending(self):
        """Test that new appointments default to pending status."""
        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='status@example.com',
            customer_name='Status Tester',
            customer_phone='5557777777',
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='StatusDog',
            dog_weight=Decimal('20.0'),
            dog_age='2 years',
            booking_date=tomorrow,
            booking_time=time(10, 0)
        )

        self.assertEqual(appointment.status, 'pending')

    def test_empty_dog_name_raises_validation_error(self):
        """Test that empty dog_name raises ValidationError."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_booking(
                customer_email='empty@example.com',
                customer_name='Empty Tester',
                customer_phone='5551111111',
                service_id=self.base_service.id,
                breed_id=self.breed.id,
                groomer_id=self.groomer.id,
                dog_name='',  # Empty string
                dog_weight=Decimal('20.0'),
                dog_age='1 year',
                booking_date=tomorrow,
                booking_time=time(9, 0)
            )

    def test_empty_customer_name_raises_validation_error(self):
        """Test that empty customer_name raises ValidationError."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_booking(
                customer_email='emptyname@example.com',
                customer_name='',  # Empty string
                customer_phone='5551111111',
                service_id=self.base_service.id,
                breed_id=self.breed.id,
                groomer_id=self.groomer.id,
                dog_name='Dog',
                dog_weight=Decimal('20.0'),
                dog_age='1 year',
                booking_date=tomorrow,
                booking_time=time(9, 0)
            )

    def test_empty_customer_phone_raises_validation_error(self):
        """Test that empty customer_phone raises ValidationError."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_booking(
                customer_email='emptyphone@example.com',
                customer_name='Phone Tester',
                customer_phone='',  # Empty string
                service_id=self.base_service.id,
                breed_id=self.breed.id,
                groomer_id=self.groomer.id,
                dog_name='Dog',
                dog_weight=Decimal('20.0'),
                dog_age='1 year',
                booking_date=tomorrow,
                booking_time=time(9, 0)
            )

    def test_empty_dog_age_raises_validation_error(self):
        """Test that empty dog_age raises ValidationError."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_booking(
                customer_email='emptyage@example.com',
                customer_name='Age Tester',
                customer_phone='5551111111',
                service_id=self.base_service.id,
                breed_id=self.breed.id,
                groomer_id=self.groomer.id,
                dog_name='Dog',
                dog_weight=Decimal('20.0'),
                dog_age='',  # Empty string
                booking_date=tomorrow,
                booking_time=time(9, 0)
            )

    def test_negative_weight_raises_validation_error(self):
        """Test that negative dog_weight raises ValidationError."""
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_booking(
                customer_email='negative@example.com',
                customer_name='Weight Tester',
                customer_phone='5551111111',
                service_id=self.base_service.id,
                breed_id=self.breed.id,
                groomer_id=self.groomer.id,
                dog_name='Dog',
                dog_weight=Decimal('-5.0'),  # Negative weight
                dog_age='1 year',
                booking_date=tomorrow,
                booking_time=time(9, 0)
            )

    def test_customer_info_updated_on_existing_customer(self):
        """Test that customer name and phone are updated for existing customers."""
        # Create customer first
        Customer.objects.create(
            email='update@example.com',
            name='Old Name',
            phone='5551112222'
        )

        tomorrow = date.today() + timedelta(days=1)
        appointment = create_booking(
            customer_email='update@example.com',
            customer_name='New Name',  # Should update
            customer_phone='5559998888',  # Should update
            service_id=self.base_service.id,
            breed_id=self.breed.id,
            groomer_id=self.groomer.id,
            dog_name='Dog',
            dog_weight=Decimal('20.0'),
            dog_age='1 year',
            booking_date=tomorrow,
            booking_time=time(9, 0)
        )

        # Verify customer was updated
        self.assertEqual(appointment.customer.email, 'update@example.com')
        self.assertEqual(appointment.customer.name, 'New Name')
        self.assertEqual(appointment.customer.phone, '5559998888')
