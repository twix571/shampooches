"""Pricing management views for admins including import/export functionality."""

import json

from decimal import Decimal

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from mainapp.models import Breed, BreedServiceMapping, Service
from mainapp.utils import admin_required, parse_json_request


@admin_required
def pricing_management(request):
    """
    Admin page for managing services, breeds, weight ranges, and prices (server-side rendered).

    Creates a default service if none exists (required for base prices).
    Displays:
    - All configured services
    - All active breeds with their base prices and weight-based pricing
    - Service-breed pricing mappings
    """
    # Create a default service if none exists (required for base prices)
    if not Service.objects.exists():
        Service.objects.create(
            name='Default Service',
            description='Default service for base pricing',
            price=Decimal('0.00'),
            pricing_type='base_required',
            duration_minutes=60
        )
    services = Service.objects.all().order_by('name')
    breeds = Breed.objects.filter(is_active=True).order_by('name')
    service_breed_prices = BreedServiceMapping.objects.all().select_related('service', 'breed')

    # Create mapping of breed_id to base_price for the first service
    # Fall back to Breed.base_price if ServiceMapping doesn't have a price
    breed_data = []
    if services.exists():
        first_service = services.first()
        prices_for_service = service_breed_prices.filter(service=first_service)
        service_mapping_prices = {str(price.breed_id): str(price.base_price) for price in prices_for_service if price.base_price}

        for breed in breeds:
            breed_id = str(breed.id)
            # Use ServiceMapping price if it exists, otherwise fall back to Breed.base_price
            base_price = None
            if breed_id in service_mapping_prices:
                base_price = service_mapping_prices[breed_id]
            elif breed.base_price:
                base_price = str(breed.base_price)

            breed_data.append({
                'id': breed.id,
                'name': breed.name,
                'base_price': base_price,
                'weight_range_amount': breed.weight_range_amount,
                'weight_price_amount': breed.weight_price_amount,
                'start_weight': breed.start_weight,
            })

    context = {
        'services': services,
        'breeds': breed_data,
        'service_breed_prices': service_breed_prices,
        'default_service': services.first(),
    }
    return render(request, 'mainapp/pricing/pricing_management.html', context)


@admin_required
def weight_ranges_editor_modal(request, breed_id):
    """
    Render the weight-based pricing editor modal for a specific breed.

    Allows admins to configure:
    - Start weight threshold
    - Weight range amount (increment size)
    - Price per weight increment

    Args:
        request: The HTTP request object.
        breed_id: The ID of the breed to edit weight pricing for.
    """
    breed = get_object_or_404(Breed, id=breed_id)
    return render(request, 'mainapp/pricing/weight_pricing_modal.html', {'breed': breed})


@require_http_methods(["POST"])
@admin_required
def update_breed_weight_pricing(request):
    """
    Update weight-based pricing configuration for a breed.

    Expects JSON POST data with:
    - breed_id: The breed to update
    - weight_range_amount: The increment size in lbs
    - weight_price_amount: The price per increment
    - start_weight: The threshold weight in lbs

    Returns:
        JsonResponse: Success/error status
    """
    success, data, error_response = parse_json_request(request)
    if not success:
        return error_response

    breed_id = data.get('breed_id')
    weight_range_amount = data.get('weight_range_amount')
    weight_price_amount = data.get('weight_price_amount')
    start_weight = data.get('start_weight')

    if not breed_id:
        return JsonResponse({'success': False, 'error': 'Breed ID is required'}, status=400)

    try:
        breed = get_object_or_404(Breed, id=breed_id)
        breed.weight_range_amount = weight_range_amount
        breed.weight_price_amount = weight_price_amount
        breed.start_weight = start_weight
        breed.save()
        return JsonResponse({'success': True, 'message': 'Weight pricing saved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@admin_required
def breed_pricing_table_modal(request, breed_id):
    """
    Render the breed pricing table preview modal.

    Shows a pricing matrix for all services at various sample weights
    to help admins understand weight-based pricing impact.

    Sample weights include:
    - Start weight
    - Start + 1 increment
    - Start + 3 increments
    - Typical maximum (if configured) or Start + 5 increments

    Args:
        request: The HTTP request object.
        breed_id: The ID of the breed to preview pricing for.
    """
    breed = get_object_or_404(Breed, id=breed_id)
    services = Service.objects.all().order_by('name')
    service_breed_prices = BreedServiceMapping.objects.filter(breed=breed).select_related('service')

    sample_weights = []

    if breed.start_weight and breed.weight_range_amount and breed.weight_price_amount:
        sample_weights.append({
            'key': 'start',
            'weight': breed.start_weight,
            'label': f"{breed.start_weight} lbs",
            'description': 'Start weight'
        })

        sample_weights.append({
            'key': 'increment_1',
            'weight': breed.start_weight + breed.weight_range_amount,
            'label': f"{breed.start_weight + breed.weight_range_amount} lbs",
            'description': f"Start + 1 × {breed.weight_range_amount} lbs"
        })

        # Add start + 3 increments
        sample_weights.append({
            'key': 'increment_3',
            'weight': breed.start_weight + (breed.weight_range_amount * 3),
            'label': f"{breed.start_weight + (breed.weight_range_amount * 3)} lbs",
            'description': f"Start + 3 × {breed.weight_range_amount} lbs"
        })

        if breed.typical_weight_max:
            sample_weights.append({
                'key': 'typical_max',
                'weight': breed.typical_weight_max,
                'label': f"{breed.typical_weight_max} lbs",
                'description': 'Typical maximum'
            })
        else:
            sample_weights.append({
                'key': 'increment_5',
                'weight': breed.start_weight + (breed.weight_range_amount * 5),
                'label': f"{breed.start_weight + (breed.weight_range_amount * 5)} lbs",
                'description': f"Start + 5 × {breed.weight_range_amount} lbs"
            })

    pricing_matrix = {}
    for service in services:
        pricing_matrix[service.id] = {}
        try:
            breed_price = service_breed_prices.get(service=service)
            base_price = float(breed_price.base_price)
        except BreedServiceMapping.DoesNotExist:
            base_price = float(service.price)

        for sample in sample_weights:
            weight_surcharge = 0.0
            if not service.exempt_from_surcharge:
                weight_surcharge = float(breed.calculate_weight_surcharge(sample['weight']))
            final_price = base_price + weight_surcharge
            pricing_matrix[service.id][sample['key']] = {
                'base_price': base_price,
                'weight_surcharge': weight_surcharge,
                'final_price': final_price
            }

    return render(request, 'mainapp/pricing/pricing_preview_modal.html', {
        'breed': breed,
        'services': services,
        'sample_weights': sample_weights,
        'pricing_matrix': pricing_matrix,
    })


@admin_required
def breed_cloning_wizard_modal(request):
    """
    Render the breed cloning wizard modal.

    Allows admins to clone pricing configuration from one breed to new breeds.
    Useful for setting up similar breeds quickly.
    """
    existing_breeds = Breed.objects.filter(is_active=True).order_by('name')
    return render(request, 'mainapp/pricing/breed_cloning_wizard_modal.html', {'existing_breeds': existing_breeds})


@admin_required
def export_pricing_config(request):
    """
    Export the complete pricing configuration as a JSON file.

    Exports:
    - All breed configurations (including weight-based pricing)
    - All service configurations
    - All breed-service pricing mappings

    Returns:
        HttpResponse: JSON file download with all pricing data
    """
    config = {
        'breeds': [],
        'services': [],
        'breed_prices': [],
    }

    for breed in Breed.objects.all():
        config['breeds'].append({
            'name': breed.name,
            'base_price': str(breed.base_price) if breed.base_price else None,
            'typical_weight_min': str(breed.typical_weight_min) if breed.typical_weight_min else None,
            'typical_weight_max': str(breed.typical_weight_max) if breed.typical_weight_max else None,
            'start_weight': str(breed.start_weight) if breed.start_weight else None,
            'weight_range_amount': str(breed.weight_range_amount) if breed.weight_range_amount else None,
            'weight_price_amount': str(breed.weight_price_amount) if breed.weight_price_amount else None,
            'breed_pricing_complex': breed.breed_pricing_complex,
            'clone_note': breed.clone_note,
            'is_active': breed.is_active,
        })

    for service in Service.objects.all():
        config['services'].append({
            'name': service.name,
            'description': service.description,
            'price': str(service.price),
            'pricing_type': service.pricing_type,
            'duration_minutes': service.duration_minutes,
            'is_active': service.is_active,
            'exempt_from_surcharge': service.exempt_from_surcharge,
        })

    for bp in BreedServiceMapping.objects.all():
        config['breed_prices'].append({
            'service': bp.service.name,
            'breed': bp.breed.name,
            'base_price': str(bp.base_price),
            'is_available': bp.is_available,
        })

    response = HttpResponse(
        json.dumps(config, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="pricing_config.json"'
    return response


@require_http_methods(["POST"])
@admin_required
def import_pricing_config(request):
    """
    Import pricing configuration from a JSON file.

    Expected JSON format:
    {
        "services": [...],
        "breeds": [...],
        "breed_prices": [...]
    }

    Creates or updates services, breeds, and breed-service mappings.

    Returns:
        JsonResponse: Import results with success/error details
    """
    data = json.loads(request.FILES.get('config_file').read().decode('utf-8'))

    results = {
        'success': True,
        'message': '',
        'details': {
            'services_created': 0,
            'breeds_created': 0,
            'breed_prices_created': 0,
            'errors': []
        }
    }

    try:
        for service_data in data.get('services', []):
            try:
                service_name = service_data['name']
                Service.objects.update_or_create(
                    name=service_name,
                    defaults=service_data
                )
                results['details']['services_created'] += 1
            except Exception as e:
                results['details']['errors'].append(f"Failed to import service {service_data['name']}: {str(e)}")

        for breed_data in data.get('breeds', []):
            try:
                breed_name = breed_data['name']
                Breed.objects.update_or_create(
                    name=breed_name,
                    defaults=breed_data
                )
                results['details']['breeds_created'] += 1
            except Exception as e:
                results['details']['errors'].append(f"Failed to import breed {breed_data['name']}: {str(e)}")

        for price_data in data.get('breed_prices', []):
            try:
                service = Service.objects.get(name=price_data['service'])
                breed = Breed.objects.get(name=price_data['breed'])
                BreedServiceMapping.objects.update_or_create(
                    service=service,
                    breed=breed,
                    defaults={'base_price': price_data['base_price'], 'is_available': price_data.get('is_available', True)}
                )
                results['details']['breed_prices_created'] += 1
            except Exception as e:
                results['details']['errors'].append(f"Failed to import breed price: {str(e)}")

        results['message'] = 'Import completed successfully'
        return JsonResponse(results)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }, status=500)
