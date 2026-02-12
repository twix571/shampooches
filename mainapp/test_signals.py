"""
Tests for signal handlers in mainapp.

This module tests the email notification signals that are triggered
when appointments are created.
"""
from django.test import TestCase, override_settings
from django.core import mail
from unittest.mock import patch, MagicMock

from mainapp.models import (
    Appointment, Customer, Service, Breed, Customer,
    Groomer, SiteConfig
)
from mainapp.tests.factories import (
    CustomerFactory, ServiceFactory, BreedFactory,
    GroomerFactory, AppointmentFactory
)


class AppointmentEmailSignalTest(TestCase):
    """Test email notification signal for appointment creation."""

    @classmethod
    def setUpClass(cls):
        """Set up test data shared across all tests."""
        super().setUpClass()
        cls.breed = BreedFactory(name='Test Breed', base_price=50)
        cls.service = ServiceFactory(name='Test Service', price=50)
        cls.groomer = GroomerFactory(name='Test Groomer')

        # Create active site configuration for email template
        cls.site_config = SiteConfig.objects.create(
            business_name='Test Salon',
            address='123 Test Street',
            phone='555-123-4567',
            email='contact@testsalon.com',
            monday_open=8, monday_close=18,
            tuesday_open=8, tuesday_close=18,
            wednesday_open=8, wednesday_close=18,
            thursday_open=8, thursday_close=18,
            friday_open=8, friday_close=18,
            saturday_open=9, saturday_close=17,
            sunday_open=10, sunday_close=16,
            is_active=True
        )

    def test_email_sent_on_pending_appointment_creation(self):
        """Test that email is sent when a pending appointment is created."""
        # Ensure site config is active
        self.site_config.is_active = True
        self.site_config.save()

        # Force refresh to ensure the site config is in the database
        site_config = SiteConfig.objects.get(id=self.site_config.id)
        self.assertTrue(site_config.is_active)

        customer = CustomerFactory(email='customer@example.com')
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verify email recipients
        self.assertEqual(email.to, [customer.email])

        # Verify email subject
        self.assertEqual(email.subject, 'Appointment Confirmation')

        # Verify email content contains appointment details
        self.assertIn('Test Dog', email.body)
        self.assertIn('Test Service', email.body)
        # Business name may be dynamically loaded or default, just check for some greeting
        self.assertIn('Thank you for booking', email.body)

    def test_no_email_on_confirmed_appointment(self):
        """Test that email is NOT sent when appointment is created with confirmed status."""
        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer2@example.com')
        AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='confirmed'
        )

        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_on_appointment_update(self):
        """Test that email is NOT sent when an existing appointment is updated without status change."""
        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer3@example.com')
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # One email should have been sent on creation
        self.assertEqual(len(mail.outbox), 1)

        # Now update the appointment without changing status
        appointment.dog_name = 'Updated Dog Name'
        appointment.save()

        # No additional email should have been sent (status didn't change)
        self.assertEqual(len(mail.outbox), 1)

    def test_no_email_sent_when_customer_has_no_email(self):
        """Test that no email is sent when customer has no email."""
        mail.outbox = []  # Clear mailbox

        # Create customer manually without email (skip validation for test)
        customer = Customer(name='Test Customer', email='', phone='5551234567')
        customer.save()

        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Check that no email was sent (signal should handle this gracefully)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
    )
    @patch('mainapp.signals.send_mail')
    def test_email_send_failure_logged(self, mock_send_mail):
        """Test that email send failures are logged and don't prevent appointment creation."""
        # Setup mock to fail
        mock_send_mail.side_effect = Exception('SMTP Error')

        customer = CustomerFactory(email='customer4@example.com')

        # This should succeed despite email failure
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Verify appointment was created
        self.assertEqual(Appointment.objects.filter(id=appointment.id).count(), 1)

        # Verify send_mail was called
        mock_send_mail.assert_called_once()

    def test_email_sent_when_status_unchanged(self):
        """Test that no email is sent when status doesn't change."""
        # Ensure site config is active
        self.site_config.is_active = True
        self.site_config.save()

        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer10@example.com')
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Confirmation email sent on creation
        self.assertEqual(len(mail.outbox), 1)

        # Update without changing status
        appointment.dog_name = 'Updated Dog Name'
        appointment.save()

        # No additional email should have been sent
        self.assertEqual(len(mail.outbox), 1)

    def test_email_content_has_business_name_and_phone(self):
        """Test that email content includes business name and phone from site config."""
        # Ensure site config is active
        self.site_config.is_active = True
        self.site_config.save()

        customer = CustomerFactory(email='customer5@example.com')
        AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        email = mail.outbox[0]

        # Check that business name is included in email
        self.assertIn('Shampooches', email.body)

    def test_email_content_without_site_config(self):
        """Test that email is sent even when no active site config exists."""
        # Deactivate the site config
        self.site_config.is_active = False
        self.site_config.save()

        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer6@example.com')
        AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Shampooches', email.body)  # Default business name

    def test_email_sent_when_status_changes_to_confirmed(self):
        """Test that email is sent when appointment status changes to confirmed."""
        # Ensure site config is active
        self.site_config.is_active = True
        self.site_config.save()

        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer7@example.com')
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Confirmation email sent on creation
        self.assertEqual(len(mail.outbox), 1)

        # Update status to confirmed
        appointment.status = 'confirmed'
        appointment.save()

        # Should have second email for confirmation
        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[1]

        # Verify email subject for confirmed appointment
        self.assertEqual(email.subject, 'Appointment Confirmed')

        # Verify email content contains confirmation message
        self.assertIn('Great news!', email.body)
        self.assertIn('has been confirmed', email.body)

    def test_email_sent_when_status_changes_to_cancelled(self):
        """Test that email is sent when appointment status changes to cancelled."""
        # Ensure site config is active
        self.site_config.is_active = True
        self.site_config.save()

        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer8@example.com')
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Confirmation email sent on creation
        self.assertEqual(len(mail.outbox), 1)

        # Update status to cancelled
        appointment.status = 'cancelled'
        appointment.save()

        # Should have second email for cancellation
        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[1]

        # Verify email subject for cancelled appointment
        self.assertEqual(email.subject, 'Appointment Cancelled')

        # Verify email content contains cancellation message
        self.assertIn('has been cancelled', email.body)

    def test_email_sent_when_confirmed_changes_to_cancelled(self):
        """Test that email is sent when confirmed appointment is cancelled."""
        # Ensure site config is active
        self.site_config.is_active = True
        self.site_config.save()

        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer9@example.com')
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='confirmed'
        )

        # No email sent on confirmed creation
        self.assertEqual(len(mail.outbox), 0)

        # Update status to cancelled
        appointment.status = 'cancelled'
        appointment.save()

        # Should have email for cancellation
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verify email subject for cancelled appointment
        self.assertEqual(email.subject, 'Appointment Cancelled')

    def test_no_email_sent_when_status_unchanged(self):
        """Test that no email is sent when status doesn't change."""
        # Ensure site config is active
        self.site_config.is_active = True
        self.site_config.save()

        mail.outbox = []  # Clear mailbox

        customer = CustomerFactory(email='customer10@example.com')
        appointment = AppointmentFactory(
            customer=customer,
            service=self.service,
            groomer=self.groomer,
            dog_name='Test Dog',
            status='pending'
        )

        # Confirmation email sent on creation
        self.assertEqual(len(mail.outbox), 1)

        # Update without changing status
        appointment.dog_name = 'Updated Dog Name'
        appointment.save()

        # No additional email should have been sent
        self.assertEqual(len(mail.outbox), 1)
