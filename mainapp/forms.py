"""Django forms for mainapp."""
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from mainapp.models import Breed, Dog


class DogForm(forms.ModelForm):
    """Form for adding/editing dog profiles."""

    # Custom field names to match existing templates
    dog_name = forms.CharField(
        label="Dog's Name",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold-500',
            'placeholder': "Enter your dog's name",
        })
    )

    breed_id = forms.IntegerField(
        label="Breed",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold-500',
        })
    )

    weight = forms.DecimalField(
        label="Weight (lbs)",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold-500',
            'placeholder': 'Weight in lbs',
            'step': '0.01',
            'min': '0.01',
        })
    )

    dog_age = forms.CharField(
        label="Age",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold-500',
            'placeholder': 'e.g., 2 years, 6 months',
        })
    )

    notes = forms.CharField(
        label="Notes",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold-500',
            'placeholder': 'Additional notes about your dog',
            'rows': 3,
        })
    )

    class Meta:
        model = Dog
        fields = []

    def __init__(self, *args, **kwargs):
        """Initialize form with breed choices."""
        super().__init__(*args, **kwargs)
        # Set breed choices
        breeds = Breed.objects.filter(is_active=True).order_by('name')
        breed_choices = [(0, 'Select breed (optional)')]
        breed_choices.extend([(breed.id, breed.name) for breed in breeds])
        self.fields['breed_id'].widget.choices = breed_choices

    def clean_dog_name(self):
        """Validate that name is not empty."""
        name = self.cleaned_data.get('dog_name')
        if not name or name.strip() == '':
            raise ValidationError('Dog name is required')
        return name.strip()

    def clean_breed_id(self):
        """Validate breed if provided."""
        breed_id = self.cleaned_data.get('breed_id')
        if breed_id:
            try:
                return Breed.objects.get(id=breed_id)
            except Breed.DoesNotExist:
                raise ValidationError('Invalid breed selected')
        return None

    def clean_weight(self):
        """Validate weight is positive if provided."""
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            try:
                weight = Decimal(weight)
                if weight <= 0:
                    raise ValidationError('Weight must be greater than 0')
            except (ValueError, TypeError):
                raise ValidationError('Invalid weight value')
        return weight

    def save(self, commit=True):
        """Save the dog with custom field mapping."""
        dog = super().save(commit=False)
        dog.name = self.cleaned_data.get('dog_name')
        dog.breed = self.cleaned_data.get('breed_id')
        dog.weight = self.cleaned_data.get('weight')
        dog.age = self.cleaned_data.get('dog_age')
        dog.notes = self.cleaned_data.get('notes')
        if commit:
            dog.save()
        return dog
