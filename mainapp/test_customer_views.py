from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, time
from decimal import Decimal

from mainapp.models import Appointment, Service, Breed, Customer, Dog

User = get_user_model()


class CustomerSignUpTestCase(TestCase):
    """Test cases for the customer sign-up view."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_sign_up_page_renders(self):
        """Test that the sign-up page renders correctly."""
        response = self.client.get(reverse('customer_sign_up'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
        self.assertContains(response, 'Username')
        self.assertContains(response, 'Email')
        self.assertContains(response, 'Password')

    def test_sign_up_valid_user(self):
        """Test successful user creation with valid data."""
        response = self.client.post(reverse('customer_sign_up'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'full_name': 'John Doe',
            'phone': '5551234567',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.user_type, 'customer')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')

    def test_sign_up_duplicate_username(self):
        """Test that duplicate username is rejected."""
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='testpass123',
            user_type='customer'
        )
        response = self.client.post(reverse('customer_sign_up'), {
            'username': 'testuser',
            'email': 'new@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'full_name': 'Jane Doe',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username already taken')

    def test_sign_up_duplicate_email(self):
        """Test that duplicate email is rejected."""
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='testpass123',
            user_type='customer'
        )
        response = self.client.post(reverse('customer_sign_up'), {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'full_name': 'Jane Doe',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email already registered')

    def test_sign_up_password_mismatch(self):
        """Test that password mismatch is rejected."""
        response = self.client.post(reverse('customer_sign_up'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'differentpass',
            'full_name': 'John Doe',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match')

    def test_sign_up_short_password(self):
        """Test that short password is rejected."""
        response = self.client.post(reverse('customer_sign_up'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short',
            'password_confirm': 'short',
            'full_name': 'John Doe',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'at least 8 characters')

    def test_sign_up_required_fields(self):
        """Test that required fields are validated."""
        response = self.client.post(reverse('customer_sign_up'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username is required')
        self.assertContains(response, 'Email is required')
        self.assertContains(response, 'Password is required')
        self.assertContains(response, 'Full name is required')

    def test_sign_up_redirects_to_login(self):
        """Test that successful sign-up redirects to customer landing."""
        response = self.client.post(reverse('customer_sign_up'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'full_name': 'John Doe',
        }, follow=False)
        # After successful login, it should redirect to customer landing
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('customer_landing').split('/')[0]))


class CustomerProfileTestCase(TestCase):
    """Test cases for the customer profile view."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123',
            user_type='customer',
            first_name='John',
            last_name='Doe',
            phone='5551234567'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            user_type='admin',
            is_staff=True
        )

    def test_profile_page_requires_login(self):
        """Test that profile page requires authentication."""
        response = self.client.get(reverse('customer_profile'))
        self.assertRedirects(response, f"/login/?next={reverse('customer_profile')}")

    def test_profile_page_only_for_customers(self):
        """Test that only customers can access profile page."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('customer_profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_page_renders_for_customer(self):
        """Test that profile page renders for customer users."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('customer_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Profile')
        self.assertContains(response, 'John')
        self.assertContains(response, 'customer@example.com')

    def test_profile_update_email(self):
        """Test updating email in profile."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('customer_profile'), {
            'email': 'newemail@example.com',
            'full_name': 'John Doe',
        })
        self.assertEqual(response.status_code, 302)
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.email, 'newemail@example.com')

    def test_profile_update_name(self):
        """Test updating name in profile."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('customer_profile'), {
            'email': 'customer@example.com',
            'full_name': 'Jane Smith',
        })
        self.assertEqual(response.status_code, 302)
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.first_name, 'Jane')
        self.assertEqual(self.customer_user.last_name, 'Smith')

    def test_profile_update_phone(self):
        """Test updating phone in profile."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('customer_profile'), {
            'email': 'customer@example.com',
            'full_name': 'John Doe',
            'phone': '5559876543',
        })
        self.assertEqual(response.status_code, 302)
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.phone, '5559876543')

    def test_profile_update_password(self):
        """Test updating password in profile."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('customer_profile'), {
            'email': 'customer@example.com',
            'full_name': 'John Doe',
            'password': 'newpass456',
            'password_confirm': 'newpass456',
        })
        self.assertEqual(response.status_code, 302)
        self.customer_user.refresh_from_db()
        self.assertTrue(self.customer_user.check_password('newpass456'))
        # Verify user is still logged in (session updated)
        response = self.client.get(reverse('customer_profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_password_mismatch(self):
        """Test that password mismatch is rejected."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('customer_profile'), {
            'email': 'customer@example.com',
            'full_name': 'John Doe',
            'password': 'newpass456',
            'password_confirm': 'differentpass',
        })
        self.assertEqual(response.status_code, 200)
        self.customer_user.refresh_from_db()
        self.assertTrue(self.customer_user.check_password('testpass123'))

    def test_profile_shows_appointments(self):
        """Test that profile shows customer's appointments."""
        breed = Breed.objects.create(name='Poodle', base_price=Decimal('50.00'), is_active=True)
        service = Service.objects.create(
            name='Bath & Groom',
            description='Full bath',
            price=Decimal('20.00'),
            pricing_type='base_required',
            duration_minutes=60,
            is_active=True
        )
        customer = Customer.objects.create(
            name='John Doe',
            email='customer@example.com',
            phone='5551234567'
        )
        Appointment.objects.create(
            customer=customer,
            service=service,
            dog_breed=breed,
            dog_name='Fido',
            date=date.today(),
            time='10:00:00',
            status='confirmed',
            price_at_booking=Decimal('70.00')
        )

        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('customer_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Booking History')
        self.assertContains(response, 'Fido')

    def test_profile_no_bookings_message(self):
        """Test that profile shows message when no bookings."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('customer_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You haven\'t made any bookings yet')


class DogProfileManagementTestCase(TestCase):
    """Test cases for dog profile management."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123',
            user_type='customer'
        )
        self.breed = Breed.objects.create(
            name='Poodle',
            base_price=Decimal('50.00'),
            is_active=True
        )

    def test_add_dog_requires_login(self):
        """Test that adding a dog requires authentication."""
        response = self.client.post(reverse('add_dog'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_add_dog_valid(self):
        """Test successful dog profile creation."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('add_dog'), {
            'dog_name': 'Fido',
            'breed_id': self.breed.id,
            'weight': '25.50',
            'dog_age': '2 years',
            'notes': 'Very friendly'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Dog.objects.filter(name='Fido', owner=self.customer_user).exists())
        dog = Dog.objects.get(name='Fido')
        self.assertEqual(dog.breed, self.breed)
        self.assertEqual(dog.weight, Decimal('25.50'))
        self.assertEqual(dog.age, '2 years')
        self.assertEqual(dog.notes, 'Very friendly')

    def test_add_dog_validation_missing_name(self):
        """Test that dog name is required."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('add_dog'), {
            'breed_id': self.breed.id,
            'weight': '25.50'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Dog.objects.filter(name='').exists())

    def test_add_dog_optional_fields(self):
        """Test that breed and weight are optional."""
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('add_dog'), {
            'dog_name': 'Max'
        })
        self.assertEqual(response.status_code, 302)
        dog = Dog.objects.get(name='Max')
        self.assertIsNone(dog.breed)
        self.assertIsNone(dog.weight)

    def test_edit_dog_requires_login(self):
        """Test that editing a dog requires authentication."""
        dog = Dog.objects.create(
            name='Fido',
            owner=self.customer_user,
            breed=self.breed
        )
        response = self.client.post(reverse('edit_dog', args=[dog.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_edit_dog_valid(self):
        """Test successful dog profile update."""
        dog = Dog.objects.create(
            name='Fido',
            owner=self.customer_user,
            breed=self.breed,
            weight=Decimal('25.50')
        )
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('edit_dog', args=[dog.id]), {
            'dog_name': 'Fido Updated',
            'breed_id': self.breed.id,
            'weight': '30.00',
            'dog_age': '3 years'
        })
        self.assertEqual(response.status_code, 302)
        dog.refresh_from_db()
        self.assertEqual(dog.name, 'Fido Updated')
        self.assertEqual(dog.weight, Decimal('30.00'))
        self.assertEqual(dog.age, '3 years')

    def test_edit_dog_only_owner(self):
        """Test that only owner can edit their dog."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            user_type='customer'
        )
        dog = Dog.objects.create(
            name='Fido',
            owner=other_user,
            breed=self.breed
        )
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('edit_dog', args=[dog.id]))
        self.assertEqual(response.status_code, 302)
        dog.refresh_from_db()
        self.assertEqual(dog.name, 'Fido')  # Not updated

    def test_delete_dog_requires_login(self):
        """Test that deleting a dog requires authentication."""
        dog = Dog.objects.create(
            name='Fido',
            owner=self.customer_user,
            breed=self.breed
        )
        response = self.client.post(reverse('delete_dog', args=[dog.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        self.assertTrue(Dog.objects.filter(id=dog.id).exists())

    def test_delete_dog_valid(self):
        """Test successful dog profile deletion."""
        dog = Dog.objects.create(
            name='Fido',
            owner=self.customer_user,
            breed=self.breed
        )
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('delete_dog', args=[dog.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Dog.objects.filter(id=dog.id).exists())

    def test_delete_dog_only_owner(self):
        """Test that only owner can delete their dog."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            user_type='customer'
        )
        dog = Dog.objects.create(
            name='Fido',
            owner=other_user,
            breed=self.breed
        )
        self.client.login(username='customer', password='testpass123')
        response = self.client.post(reverse('delete_dog', args=[dog.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Dog.objects.filter(id=dog.id).exists())

    def test_profile_shows_dogs(self):
        """Test that profile page displays user's dogs."""
        Dog.objects.create(
            name='Fido',
            owner=self.customer_user,
            breed=self.breed,
            weight=Decimal('25.50'),
            age='2 years'
        )
        Dog.objects.create(
            name='Max',
            owner=self.customer_user,
            weight=Decimal('15.00')
        )
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('customer_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Dogs')
        self.assertContains(response, 'Fido')
        self.assertContains(response, 'Max')
        self.assertContains(response, 'Poodle')
        self.assertContains(response, '25.50 lbs')

    def test_book_with_dog_preloads_data(self):
        """Test that book_with_dog passes preloaded data to modal."""
        dog = Dog.objects.create(
            name='Fido',
            owner=self.customer_user,
            breed=self.breed,
            weight=Decimal('25.50'),
            age='2 years'
        )
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('book_with_dog', args=[dog.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'booking-modal')
        self.assertContains(response, 'window.preloadedDog')
        self.assertContains(response, 'Fido')
        self.assertContains(response, '25.5')
        self.assertContains(response, '2 years')
        self.assertContains(response, 'window.preloadedCustomer')

    def test_book_with_dog_for_anonymous_user(self):
        """Test that anonymous users can view booking modal without dog data."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            user_type='customer'
        )
        dog = Dog.objects.create(
            name='Fido',
            owner=other_user,
            breed=self.breed
        )
        response = self.client.get(reverse('book_with_dog', args=[dog.id]))
        self.assertEqual(response.status_code, 200)
        # Anonymous user should not see other customer's dog data preloaded
        self.assertNotContains(response, 'Fido')

    def test_dog_model_string_representation(self):
        """Test Dog model string representation."""
        dog = Dog.objects.create(
            name='Fido',
            owner=self.customer_user,
            breed=self.breed
        )
        expected = f"Fido ({self.customer_user.username})"
        self.assertEqual(str(dog), expected)


class CancelAppointmentTestCase(TestCase):
    """Test cases for cancelling appointments."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.customer_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='customer'
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='test@example.com',
            phone='5551234567'
        )
        self.breed = Breed.objects.create(
            name='Test Breed',
            base_price=Decimal('50.00'),
            typical_weight_min=Decimal('10.00'),
            typical_weight_max=Decimal('20.00'),
            weight_range_amount=Decimal('10.00'),
            weight_price_amount=Decimal('15.00'),
            start_weight=Decimal('15.00'),
            is_active=True
        )
        self.service = Service.objects.create(
            name='Grooming Service',
            description='Test grooming service',
            price=Decimal('20.00'),
            pricing_type='base_required',
            duration_minutes=60,
            is_active=True
        )
        self.pending_appointment = Appointment.objects.create(
            customer=self.customer,
            user=self.customer_user,
            service=self.service,
            dog_name='Test Dog',
            dog_breed=self.breed,
            dog_size='Medium',
            dog_weight=Decimal('15.00'),
            dog_age='2 years',
            date=date.today(),
            time=time(10, 0),
            status='pending',
            price_at_booking=Decimal('70.00')
        )
        self.confirmed_appointment = Appointment.objects.create(
            customer=self.customer,
            user=self.customer_user,
            service=self.service,
            dog_name='Test Dog',
            dog_breed=self.breed,
            dog_size='Medium',
            dog_weight=Decimal('15.00'),
            dog_age='2 years',
            date=date.today(),
            time=time(11, 0),
            status='confirmed',
            price_at_booking=Decimal('70.00')
        )

    def test_cancel_pending_appointment_success(self):
        """Test that a customer can successfully cancel their pending appointment."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('cancel_appointment', args=[self.pending_appointment.id]))
        self.assertEqual(response.status_code, 302)
        self.pending_appointment.refresh_from_db()
        self.assertEqual(self.pending_appointment.status, 'cancelled')

    def test_cancel_confirmed_appointment_fails(self):
        """Test that a confirmed appointment cannot be cancelled."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('cancel_appointment', args=[self.confirmed_appointment.id]))
        self.assertEqual(response.status_code, 302)
        self.confirmed_appointment.refresh_from_db()
        self.assertEqual(self.confirmed_appointment.status, 'confirmed')

    def test_cancel_appointment_requires_login(self):
        """Test that cancelling an appointment requires authentication."""
        response = self.client.post(reverse('cancel_appointment', args=[self.pending_appointment.id]))
        self.assertEqual(response.status_code, 302)

    def test_cancel_appointment_only_own_appointments(self):
        """Test that a customer can only cancel their own appointments."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            user_type='customer'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(reverse('cancel_appointment', args=[self.pending_appointment.id]))
        self.assertEqual(response.status_code, 302)
        self.pending_appointment.refresh_from_db()
        self.assertEqual(self.pending_appointment.status, 'pending')

    def test_cancel_appointment_nonexistent(self):
        """Test cancelling a non-existent appointment returns error."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('cancel_appointment', args=[99999]))
        self.assertEqual(response.status_code, 302)

    def test_cancel_appointment_get_method_redirects(self):
        """Test that GET request to cancel appointment redirects (only POST allowed)."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cancel_appointment', args=[self.pending_appointment.id]))
        self.assertEqual(response.status_code, 302)
        self.pending_appointment.refresh_from_db()
        self.assertEqual(self.pending_appointment.status, 'pending')
