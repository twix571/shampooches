from django.core.management.base import BaseCommand
from decimal import Decimal
from mainapp.models import Breed

class Command(BaseCommand):
    help = 'Populate common US dog breeds with base prices'

    def handle(self, *args, **options):
        # Common US breeds with typical base prices (Eastern US market)
        breeds_data = [
            # Small Breeds (0-15 lbs)
            {'name': 'Chihuahua', 'base_price': 35.00, 'typical_weight_min': 2.00, 'typical_weight_max': 6.00},
            {'name': 'Yorkshire Terrier', 'base_price': 40.00, 'typical_weight_min': 3.00, 'typical_weight_max': 7.00},
            {'name': 'Maltese', 'base_price': 40.00, 'typical_weight_min': 4.00, 'typical_weight_max': 7.00},
            {'name': 'Pomeranian', 'base_price': 40.00, 'typical_weight_min': 3.00, 'typical_weight_max': 7.00},
            {'name': 'Shih Tzu', 'base_price': 45.00, 'typical_weight_min': 9.00, 'typical_weight_max': 16.00},
            {'name': 'Cavalier King Charles Spaniel', 'base_price': 45.00, 'typical_weight_min': 13.00, 'typical_weight_max': 18.00},
            {'name': 'Boston Terrier', 'base_price': 50.00, 'typical_weight_min': 10.00, 'typical_weight_max': 25.00},
            {'name': 'Pug', 'base_price': 45.00, 'typical_weight_min': 14.00, 'typical_weight_max': 18.00},
            {'name': 'French Bulldog', 'base_price': 55.00, 'typical_weight_min': 16.00, 'typical_weight_max': 28.00},

            # Medium Breeds (16-40 lbs)
            {'name': 'Cocker Spaniel', 'base_price': 50.00, 'typical_weight_min': 20.00, 'typical_weight_max': 28.00},
            {'name': 'Beagle', 'base_price': 50.00, 'typical_weight_min': 20.00, 'typical_weight_max': 30.00},
            {'name': 'Corgi (Pembroke Welsh)', 'base_price': 55.00, 'typical_weight_min': 22.00, 'typical_weight_max': 31.00},
            {'name': 'Brittany Spaniel', 'base_price': 55.00, 'typical_weight_min': 30.00, 'typical_weight_max': 40.00},
            {'name': 'Border Collie', 'base_price': 60.00, 'typical_weight_min': 30.00, 'typical_weight_max': 55.00},
            {'name': 'Whippet', 'base_price': 55.00, 'typical_weight_min': 25.00, 'typical_weight_max': 40.00},
            {'name': 'Shiba Inu', 'base_price': 60.00, 'typical_weight_min': 17.00, 'typical_weight_max': 23.00},
            {'name': 'Australian Shepherd', 'base_price': 65.00, 'typical_weight_min': 40.00, 'typical_weight_max': 65.00},
            {'name': 'Standard Poodle', 'base_price': 70.00, 'typical_weight_min': 40.00, 'typical_weight_max': 70.00},

            # Large Breeds (41-80 lbs)
            {'name': 'Golden Retriever', 'base_price': 65.00, 'typical_weight_min': 55.00, 'typical_weight_max': 75.00},
            {'name': 'Labrador Retriever', 'base_price': 65.00, 'typical_weight_min': 55.00, 'typical_weight_max': 80.00},
            {'name': 'German Shepherd', 'base_price': 70.00, 'typical_weight_min': 50.00, 'typical_weight_max': 90.00},
            {'name': 'Boxer', 'base_price': 60.00, 'typical_weight_min': 50.00, 'typical_weight_max': 80.00},
            {'name': 'English Bulldog', 'base_price': 70.00, 'typical_weight_min': 40.00, 'typical_weight_max': 50.00},
            {'name': 'Siberian Husky', 'base_price': 75.00, 'typical_weight_min': 35.00, 'typical_weight_max': 60.00},
            {'name': 'Australian Cattle Dog', 'base_price': 60.00, 'typical_weight_min': 35.00, 'typical_weight_max': 50.00},
            {'name': 'Vizsla', 'base_price': 55.00, 'typical_weight_min': 45.00, 'typical_weight_max': 65.00},

            # Giant Breeds (80+ lbs)
            {'name': 'Bernese Mountain Dog', 'base_price': 80.00, 'typical_weight_min': 70.00, 'typical_weight_max': 115.00},
            {'name': 'Great Pyrenees', 'base_price': 85.00, 'typical_weight_min': 85.00, 'typical_weight_max': 115.00},
            {'name': 'Newfoundland', 'base_price': 90.00, 'typical_weight_min': 100.00, 'typical_weight_max': 150.00},
            {'name': 'Saint Bernard', 'base_price': 90.00, 'typical_weight_min': 120.00, 'typical_weight_max': 180.00},
            {'name': 'Great Dane', 'base_price': 100.00, 'typical_weight_min': 110.00, 'typical_weight_max': 175.00},
            {'name': 'Irish Wolfhound', 'base_price': 95.00, 'typical_weight_min': 105.00, 'typical_weight_max': 180.00},

            # Popular Mixed Breeds
            {'name': 'Goldendoodle', 'base_price': 65.00, 'typical_weight_min': 50.00, 'typical_weight_max': 90.00},
            {'name': 'Labradoodle', 'base_price': 65.00, 'typical_weight_min': 50.00, 'typical_weight_max': 65.00},
            {'name': 'Cockapoo', 'base_price': 45.00, 'typical_weight_min': 12.00, 'typical_weight_max': 24.00},
            {'name': 'Maltipoo', 'base_price': 40.00, 'typical_weight_min': 5.00, 'typical_weight_max': 12.00},
            {'name': 'Puggle', 'base_price': 45.00, 'typical_weight_min': 15.00, 'typical_weight_max': 30.00},
            {'name': 'Schnauzer (Miniature)', 'base_price': 40.00, 'typical_weight_min': 11.00, 'typical_weight_max': 20.00},
            {'name': 'Schnauzer (Standard)', 'base_price': 50.00, 'typical_weight_min': 30.00, 'typical_weight_max': 45.00},
        ]

        created_count = 0
        updated_count = 0

        for breed_data in breeds_data:
            breed, created = Breed.objects.get_or_create(
                name=breed_data['name'],
                defaults={
                    'base_price': Decimal(str(breed_data['base_price'])),
                    'typical_weight_min': Decimal(str(breed_data['typical_weight_min'])),
                    'typical_weight_max': Decimal(str(breed_data['typical_weight_max'])),
                    'is_active': True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {breed.name} (Base: ${breed.base_price})'))
            else:
                # Update existing breed with new base price if not set
                if breed.base_price is None:
                    breed.base_price = Decimal(str(breed_data['base_price']))
                    breed.typical_weight_min = Decimal(str(breed_data['typical_weight_min']))
                    breed.typical_weight_max = Decimal(str(breed_data['typical_weight_max']))
                    breed.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'Updated: {breed.name} with base price ${breed.base_price}'))
                else:
                    self.stdout.write(self.style.NOTICE(f'Skipped (already has base price): {breed.name}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created_count} breeds, updated {updated_count} breeds.'))
