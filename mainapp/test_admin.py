from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.test import Client
from django.contrib.messages.storage.fallback import FallbackStorage
from mainapp.models import Service, Customer, Appointment, Groomer, Breed
import datetime

User = get_user_model()


class AdminActionsTestCase(TestCase):
    """Test admin actions for valid status updates."""

    def setUp(self):
        """Set up test data."""
        # Create superuser for admin access
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.force_login(self.superuser)

        # Create test data
        self.breed = Breed.objects.create(name='Test Breed', base_price=50.00)
        self.service = Service.objects.create(
            name='Test Service',
            description='Test description',
            price=30.00,
            duration_minutes=30,
            pricing_type='standalone'
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='test@test.com',
            phone='1234567890'
        )
        self.groomer = Groomer.objects.create(
            name='Test Groomer',
            bio='Test bio',
            specialties='Grooming'
        )
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Fido',
            dog_breed=self.breed,
            date=datetime.date.today(),
            time=datetime.time(10, 0),
            status='pending'
        )

    def test_admin_mark_as_completed_action_exists(self):
        """Test that mark_as_completed admin action exists."""
        from django.contrib.admin import site
        admin_class = site._registry[Appointment]
        # mark_as_completed should exist
        self.assertTrue(hasattr(admin_class, 'mark_as_completed'))

    def test_admin_mark_as_cancelled_action_exists(self):
        """Test that mark_as_cancelled admin action exists."""
        from django.contrib.admin import site
        admin_class = site._registry[Appointment]
        # mark_as_cancelled should exist
        self.assertTrue(hasattr(admin_class, 'mark_as_cancelled'))

    def test_appointment_admin_has_autocomplete_fields(self):
        """Test that AppointmentAdmin has autocomplete_fields."""
        from django.contrib.admin import site
        admin_class = site._registry[Appointment]
        # Should have customer, service, dog_breed
        self.assertIn('customer', admin_class.autocomplete_fields)
        self.assertIn('service', admin_class.autocomplete_fields)
        self.assertIn('dog_breed', admin_class.autocomplete_fields)

    def test_appointment_autocomplete_includes_groomer(self):
        """Test that AppointmentAdmin includes groomer in autocomplete_fields."""
        from django.contrib.admin import site
        admin_class = site._registry[Appointment]
        # groomer should also be in autocomplete for performance
        self.assertIn('groomer', admin_class.autocomplete_fields)

    def test_valid_status_choices(self):
        """Test that Appointment model only accepts valid status choices."""
        VALID_STATUS_CHOICES = ['pending', 'confirmed', 'completed', 'cancelled']

        # Test each valid status
        for status in VALID_STATUS_CHOICES:
            appointment = Appointment.objects.create(
                customer=self.customer,
                service=self.service,
                groomer=self.groomer,
                dog_name=f'Dog_{status}',
                dog_breed=self.breed,
                date=datetime.date.today(),
                time=datetime.time(10, 0),
                status=status
            )
            appointment.refresh_from_db()
            self.assertEqual(appointment.status, status)

    def test_invalid_status_choice_raises_error(self):
        """Test that 'scheduled' status is not valid."""
        # 'scheduled' is not in STATUS_CHOICES
        with self.assertRaises(Exception):
            # This should fail when trying to create with invalid status
            # The actual error depends on how Django validates
            appointment = Appointment(
                customer=self.customer,
                service=self.service,
                groomer=self.groomer,
                dog_name='Test Dog',
                dog_breed=self.breed,
                date=datetime.date.today(),
                time=datetime.time(10, 0),
                status='scheduled'  # This is invalid
            )
            appointment.full_clean()  # This should raise ValidationError

    def test_admin_status_update_to_confirmed(self):
        """Test that admin can update appointment status to confirmed."""
        from django.contrib.admin import site
        admin_class = site._registry[Appointment]

        # mark_as_confirmed action should exist (after fix)
        self.assertTrue(hasattr(admin_class, 'mark_as_confirmed'))

        # Create a request object with message support
        factory = RequestFactory()
        request = factory.post('/admin/mainapp/appointment/')
        request.user = self.superuser
        # Add message storage
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Test the action works
        appointments = Appointment.objects.filter(id=self.appointment.id)
        admin_class.mark_as_confirmed(request, appointments)

        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'confirmed')


class AdminViewsSecurityTestCase(TestCase):
    """Test security of admin views to ensure proper authentication."""

    def setUp(self):
        """Set up test data."""
        # Create superuser for admin access
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='regularpass123'
        )
        self.client = Client()

        # Create test groomer
        self.groomer = Groomer.objects.create(
            name='Test Groomer',
            bio='Test bio',
            specialties='Grooming'
        )

    def test_customers_modal_requires_admin(self):
        """Test that customers_modal requires admin authentication."""
        # Unauthenticated user should be redirected
        response = self.client.get('/customers/')
        self.assertEqual(response.status_code, 302)
        # admin_required uses Django's redirect_to_login, which redirects to login page
        self.assertIn('/login', response.url)

        # Regular user should be denied access
        self.client.force_login(self.regular_user)
        response = self.client.get('/customers/')
        self.assertEqual(response.status_code, 302)

    def test_groomers_modal_requires_admin(self):
        """Test that groomers_modal requires admin authentication."""
        # Unauthenticated user should be redirected
        response = self.client.get('/groomers/')
        self.assertEqual(response.status_code, 302)
        # admin_required uses Django's redirect_to_login, which redirects to login page
        self.assertIn('/login', response.url)

        # Regular user should be denied access
        self.client.force_login(self.regular_user)
        response = self.client.get('/groomers/')
        self.assertEqual(response.status_code, 302)

        # Admin user should be able to access
        self.client.force_login(self.admin_user)
        response = self.client.get('/groomers/')
        self.assertEqual(response.status_code, 200)

    def test_appointments_modal_requires_admin(self):
        """Test that appointments_modal requires admin authentication."""
        # Unauthenticated user should be redirected
        response = self.client.get('/appointments/')
        self.assertEqual(response.status_code, 302)
        # admin_required uses Django's redirect_to_login, which redirects to login page
        self.assertIn('/login', response.url)

        # Regular user should be denied access
        self.client.force_login(self.regular_user)
        response = self.client.get('/appointments/')
        self.assertEqual(response.status_code, 302)
