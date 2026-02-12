"""
Input validation utility classes for common validation patterns.

This module provides reusable validator classes for common input validation patterns
such as phone numbers, email addresses, date ranges, and numeric values.
"""

import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Tuple

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator
from django.utils.translation import gettext as _


class ValidationErrorType:
    """Base class for validation errors."""
    pass


class PhoneValidator:
    """Validator for phone numbers with multiple format support.

    Supports formats:
    - (555) 123-4567
    - 555-123-4567
    - 555.123.4567
    - 5551234567
    - +1 555 123 4567
    """

    # Pattern to match various phone number formats
    PHONE_PATTERN = re.compile(
        r'^(\+?[1-9]?\d{0,2}[-.\s]?)?'
        r'(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]}?\d{4}$'
    )

    SIMPLE_DIGIT_PATTERN = re.compile(r'^\d{10}$')

    @classmethod
    def validate(cls, phone: str) -> None:
        """Validate a phone number.

        Args:
            phone: Phone number string to validate.

        Raises:
            ValidationError: If phone number is invalid.
        """
        if not phone or not isinstance(phone, str):
            raise ValidationError(_("Phone number must be a non-empty string."))

        # Extract digits
        digits = re.sub(r'[^\d]', '', phone)

        # Check for valid length (10 or 11 digits for US numbers with country code)
        if len(digits) < 10 or len(digits) > 15:
            raise ValidationError(
                _("Phone number must contain 10-15 digits. Found {count} digits.").format(
                    count=len(digits)
                )
            )

        # Validate format
        if not cls.SIMPLE_DIGIT_PATTERN.match(phone) and not cls.PHONE_PATTERN.match(phone):
            # For flexibility, just check the digit count
            pass

    @classmethod
    def clean_phone(cls, phone: str) -> str:
        """Clean and normalize a phone number.

        Args:
            phone: Phone number string to clean.

        Returns:
            Normalized phone number string (10 digits).

        Raises:
            ValidationError: If phone number is invalid.
        """
        cls.validate(phone)

        # Extract digits and return last 10 (for US numbers)
        digits = re.sub(r'[^\d]', '', phone)

        # If 11 digits and starts with 1 (US country code), remove it
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]

        return digits

    @classmethod
    def format_phone(cls, phone: str) -> str:
        """Format a phone number in standard US format.

        Args:
            phone: 10-digit phone number string.

        Returns:
            Formatted phone number: (555) 123-4567
        """
        clean = cls.clean_phone(phone)
        return f'({clean[:3]}) {clean[3:6]}-{clean[6:]}'


class EmailValidatorExt:
    """Extended email validator with additional checks."""

    def __init__(self):
        self.validator = EmailValidator()

    def validate(self, email: str) -> None:
        """Validate an email address.

        Args:
            email: Email address to validate.

        Raises:
            ValidationError: If email is invalid.
        """
        if not email or not isinstance(email, str):
            raise ValidationError(_("Email must be a non-empty string."))

        email = email.strip()
        if not email:
            raise ValidationError(_("Email cannot be empty."))

        # Use Django built-in validator
        try:
            self.validator(email)
        except ValidationError:
            raise ValidationError(_("Please enter a valid email address."))

    def clean_email(self, email: str) -> str:
        """Clean and normalize an email address.

        Args:
            email: Email address to clean.

        Returns:
            Normalized email address (lowercase, trimmed).
        """
        self.validate(email)
        return email.strip().lower()


class DateRangeValidator:
    """Validator for date range inputs."""

    @classmethod
    def validate_future_date(cls, date_value: date, allow_today: bool = True) -> None:
        """Validate that a date is in the future (or today if allowed).

        Args:
            date_value: Date to validate.
            allow_today: Whether to allow today's date.

        Raises:
            ValidationError: If date is in the past.
        """
        today = date.today()

        if not allow_today and date_value <= today:
            raise ValidationError(
                _("Date must be in the future. Selected date: {date}").format(
                    date=date_value.strftime('%Y-%m-%d')
                )
            )

        if allow_today and date_value < today:
            raise ValidationError(
                _("Date cannot be in the past. Selected date: {date}").format(
                    date=date_value.strftime('%Y-%m-%d')
                )
            )

    @classmethod
    def validate_date_range(
        cls,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        max_days: int = 365
    ) -> None:
        """Validate a date range.

        Args:
            start_date: Start date.
            end_date: End date.
            max_days: Maximum allowed days in range.

        Raises:
            ValidationError: If date range is invalid.
        """
        if start_date and end_date and end_date < start_date:
            raise ValidationError(
                _("End date cannot be before start date.")
            )

        if start_date and end_date:
            delta = end_date - start_date
            if delta.days > max_days:
                raise ValidationError(
                    _("Date range cannot exceed {max} days. Found {days} days.").format(
                        max=max_days,
                        days=delta.days
                    )
                )


class TimeValidator:
    """Validator for time inputs."""

    @classmethod
    def validate_business_hours(
        cls,
        time_value: time,
        start_hour: int = 8,
        end_hour: int = 18
    ) -> None:
        """Validate that a time is within business hours.

        Args:
            time_value: Time to validate.
            start_hour: Business opening hour (24-hour format).
            end_hour: Business closing hour (24-hour format).

        Raises:
            ValidationError: If time is outside business hours.
        """
        hour = time_value.hour

        if hour < start_hour or hour >= end_hour:
            raise ValidationError(
                _("Time must be between {start}:00 and {end}:00.").format(
                    start=start_hour,
                    end=end_hour
                )
            )

    @classmethod
    def validate_time_interval(
        cls,
        time_value: time,
        interval_minutes: int = 30
    ) -> None:
        """Validate that a time is on a specific interval.

        Args:
            time_value: Time to validate.
            interval_minutes: Interval in minutes (default 30).

        Raises:
            ValidationError: If time is not on the specified interval.
        """
        minutes = time_value.hour * 60 + time_value.minute

        if minutes % interval_minutes != 0:
            raise ValidationError(
                _("Time must be on {interval}-minute intervals.").format(
                    interval=interval_minutes
                )
            )


class NumericValidator:
    """Validator for numeric inputs."""

    @classmethod
    def validate_positive_integer(
        cls,
        value: Any,
        min_value: int = 1,
        max_value: Optional[int] = None
    ) -> int:
        """Validate and convert a positive integer.

        Args:
            value: Value to validate.
            min_value: Minimum allowed value.
            max_value: Maximum allowed value.

        Returns:
            Validated integer.

        Raises:
            ValidationError: If value is invalid.
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                _("Value must be a whole number.")
            )

        if int_value < min_value:
            raise ValidationError(
                _("Value must be at least {min}.").format(min=min_value)
            )

        if max_value is not None and int_value > max_value:
            raise ValidationError(
                _("Value cannot exceed {max}.").format(max=max_value)
            )

        return int_value

    @classmethod
    def validate_positive_decimal(
        cls,
        value: Any,
        min_value: Decimal = Decimal('0'),
        max_value: Optional[Decimal] = None,
        decimal_places: int = 2
    ) -> Decimal:
        """Validate and convert a positive decimal.

        Args:
            value: Value to validate.
            min_value: Minimum allowed value.
            max_value: Maximum allowed value.
            decimal_places: Maximum decimal places.

        Returns:
            Validated decimal.

        Raises:
            ValidationError: If value is invalid.
        """
        try:
            decimal_value = Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError(
                _("Value must be a number.")
            )

        if decimal_value < min_value:
            raise ValidationError(
                _("Value must be at least {min}.").format(min=float(min_value))
            )

        if max_value is not None and decimal_value > max_value:
            raise ValidationError(
                _("Value cannot exceed {max}.").format(max=float(max_value))
            )

        # Check decimal places
        quantized = decimal_value.quantize(Decimal(f'1.{"0" * decimal_places}'))
        if quantized != decimal_value:
            raise ValidationError(
                _("Value cannot have more than {places} decimal places.").format(
                    places=decimal_places
                )
            )

        return decimal_value

    @classmethod
    def validate_percentage(
        cls,
        value: Any
    ) -> Decimal:
        """Validate a percentage (0-100).

        Args:
            value: Value to validate.

        Returns:
            Validated decimal.

        Raises:
            ValidationError: If value is invalid.
        """
        return cls.validate_positive_decimal(
            value,
            min_value=Decimal('0'),
            max_value=Decimal('100'),
            decimal_places=2
        )


class NameValidator:
    """Validator for name inputs."""

    @classmethod
    def validate(cls, name: str, min_length: int = 2, max_length: int = 100) -> None:
        """Validate a name.

        Args:
            name: Name to validate.
            min_length: Minimum length.
            max_length: Maximum length.

        Raises:
            ValidationError: If name is invalid.
        """
        if not name or not isinstance(name, str):
            raise ValidationError(_("Name must be a non-empty string."))

        name = name.strip()
        if not name:
            raise ValidationError(_("Name cannot be empty."))

        if len(name) < min_length:
            raise ValidationError(
                _("Name must be at least {min} characters.").format(min=min_length)
            )

        if len(name) > max_length:
            raise ValidationError(
                _("Name cannot exceed {max} characters.").format(max=max_length)
            )

    @classmethod
    def validate_no_special_chars(cls, name: str, allow_spaces: bool = True) -> None:
        """Validate that name doesn't contain special characters.

        Args:
            name: Name to validate.
            allow_spaces: Whether to allow spaces.

        Raises:
            ValidationError: If name contains special characters.
        """
        cls.validate(name)

        # Allow letters, numbers, hyphens, apostrophes, and optionally spaces
        pattern = r"^[a-zA-Z0-9\-']+$"
        if allow_spaces:
            pattern = r"^[a-zA-Z0-9\s\-']+$"

        if not re.match(pattern, name.strip()):
            raise ValidationError(
                _("Name can only contain letters, numbers, hyphens, and apostrophes.")
            )

    @classmethod
    def clean_name(cls, name: str) -> str:
        """Clean and normalize a name.

        Args:
            name: Name to clean.

        Returns:
            Normalized name (trimmed, title case if appropriate).
        """
        cls.validate(name)
        return name.strip()


class AddressValidator:
    """Validator for address inputs."""

    @classmethod
    def validate_required_parts(cls, address: Dict[str, Any]) -> None:
        """Validate that required address parts are present.

        Args:
            address: Dictionary containing address components.

        Raises:
            ValidationError: If required parts are missing.
        """
        required_fields = ['street', 'city', 'state', 'zip_code']
        for field in required_fields:
            if field not in address or not address[field]:
                raise ValidationError(
                    _("Address must include {field}.").format(field=field)
                )

    @classmethod
    def validate_zip_code(cls, zip_code: str, country: str = 'US') -> None:
        """Validate a zip code.

        Args:
            zip_code: Zip code to validate.
            country: Country code (default US).

        Raises:
            ValidationError: If zip code is invalid.
        """
        if not zip_code or not isinstance(zip_code, str):
            raise ValidationError(_("Zip code must be a non-empty string."))

        zip_code = zip_code.strip().upper()

        if country == 'US':
            # US ZIP codes: 5 digits or 5+4 format
            us_pattern = r'^\d{5}(-\d{4})?$'
            if not re.match(us_pattern, zip_code):
                raise ValidationError(
                    _("Please enter a valid US ZIP code (5 digits or 5+4 format).")
                )
        else:
            # For other countries, just validate length
            if len(zip_code) < 3 or len(zip_code) > 10:
                raise ValidationError(
                    _("Zip code must be between 3 and 10 characters.")
                )


class BookingValidator:
    """Validator for booking-related inputs."""

    @classmethod
    def validate_booking_date_time(
        cls,
        booking_date: date,
        booking_time: time,
        groomer_time_slots: Optional[list[time]] = None,
        interval_minutes: int = 30
    ) -> Tuple[date, time]:
        """Validate booking date and time.

        Args:
            booking_date: Date to validate.
            booking_time: Time to validate.
            groomer_time_slots: Available time slots for groomer.
            interval_minutes: Time slot interval.

        Returns:
            Tuple of validated (date, time).

        Raises:
            ValidationError: If date or time is invalid.
        """
        # Validate date is in future
        DateRangeValidator.validate_future_date(booking_date, allow_today=False)

        # Validate time is on interval
        TimeValidator.validate_time_interval(booking_time, interval_minutes)

        # Validate time is in available slots
        if groomer_time_slots and booking_time not in groomer_time_slots:
            raise ValidationError(
                _("Selected time is not available.")
            )

        return booking_date, booking_time



