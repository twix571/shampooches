# Standard library imports (none in this file)

# Third-party imports
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from typing import Optional

# Django imports (none in this file)

# Local imports
from .models import (
    Breed, BreedServiceMapping, Groomer, Service
)
from .serializers import (
    BreedSerializer, BreedServiceMappingSerializer,
    GroomerSerializer, ServiceSerializer
)
from .utils import admin_required_for_viewsets
from .api_helpers import StandardResponse, StandardPagination, handle_api_errors


class AdminModelViewSet(viewsets.ModelViewSet):
    """Base ViewSet that enforces admin authentication for create, update, and destroy operations."""

    def get_permissions(self):
        """Allow unauthenticated read access, require auth for write operations."""
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @admin_required_for_viewsets
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @admin_required_for_viewsets
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @admin_required_for_viewsets
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def success_response(
        self,
        data=None,
        message="Success",
        status_code=status.HTTP_200_OK,
        meta=None
    ) -> Response:
        """Create a success response using StandardResponse."""
        return StandardResponse.success(
            data=data,
            message=message,
            status_code=status_code,
            meta=meta
        )

    def error_response(
        self,
        message="Error",
        errors=None,
        status_code=status.HTTP_400_BAD_REQUEST,
        data=None
    ) -> Response:
        """Create an error response using StandardResponse."""
        return StandardResponse.error(
            message=message,
            errors=errors,
            status_code=status_code,
            data=data
        )

    def validate_required_fields(self, request_data, required_fields):
        """
        Validate that required fields are present in request data.

        Args:
            request_data: Request data dictionary
            required_fields: List of required field names

        Returns:
            (None, None) if all fields present
            (error_response, None) if validation fails
        """
        missing_fields = {field: f'{field} is required' for field in required_fields if not request_data.get(field)}

        if missing_fields:
            return self.error_response(
                message='Missing required fields',
                errors=missing_fields
            ), None

        return None, None


class ServiceViewSet(AdminModelViewSet):
    """ViewSet for Service CRUD operations."""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    pagination_class = StandardPagination

    @action(detail=False, methods=['post'], url_path='exempt-update')
    @handle_api_errors('ServiceViewSet.exempt_update')
    def exempt_update(self, request):
        """Update the exempt_from_surcharge flag for a service."""
        service_id = request.data.get('service_id')
        exempt = request.data.get('exempt') == 'true'

        error_response, _ = self.validate_required_fields(request.data, ['service_id'])
        if error_response:
            return error_response

        try:
            service = Service.objects.get(id=service_id)
            service.exempt_from_surcharge = exempt
            service.save()
            return self.success_response(
                data={'service_id': service.id, 'exempt': service.exempt_from_surcharge},
                message='Service exemption updated'
            )
        except Service.DoesNotExist:
            return self.error_response(
                message='Service not found',
                status_code=status.HTTP_404_NOT_FOUND
            )


class BreedViewSet(AdminModelViewSet):
    """ViewSet for Breed CRUD operations."""
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    pagination_class = StandardPagination

    @action(detail=True, methods=['post'], url_path='update-base-price')
    @handle_api_errors('BreedViewSet.update_base_price')
    def update_base_price(self, request, pk=None):
        """Update the breed's base price."""
        breed = self.get_object()
        base_price = request.data.get('base_price')

        error_response, _ = self.validate_required_fields(request.data, ['base_price'])
        if error_response:
            return error_response

        breed.base_price = base_price
        breed.save()

        return self.success_response(
            data={'breed_id': breed.id, 'base_price': str(breed.base_price)},
            message='Base price updated successfully'
        )


class GroomerViewSet(AdminModelViewSet):
    """ViewSet for Groomer CRUD operations."""
    queryset = Groomer.objects.order_by('order', 'name').prefetch_related('time_slots')
    serializer_class = GroomerSerializer
    pagination_class = StandardPagination


class BreedServiceMappingViewSet(AdminModelViewSet):
    """ViewSet for BreedServiceMapping CRUD operations."""
    queryset = BreedServiceMapping.objects.select_related('service', 'breed').order_by('breed__name', 'service__name')
    serializer_class = BreedServiceMappingSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        service_id = self.request.query_params.get('service_id')
        breed_id = self.request.query_params.get('breed_id')

        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if breed_id:
            queryset = queryset.filter(breed_id=breed_id)

        return queryset

    @handle_api_errors('BreedServiceMappingViewSet.create')
    def create(self, request, *args, **kwargs):
        service_id = request.data.get('service')
        breed_id = request.data.get('breed')
        base_price = request.data.get('base_price')

        error_response, _ = self.validate_required_fields(request.data, ['service', 'breed', 'base_price'])
        if error_response:
            return error_response

        try:
            service = Service.objects.get(id=service_id)
            breed = Breed.objects.get(id=breed_id)
        except Service.DoesNotExist:
            return self.error_response(
                message='Service not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Breed.DoesNotExist:
            return self.error_response(
                message='Breed not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        obj, created = BreedServiceMapping.objects.update_or_create(
            service=service,
            breed=breed,
            defaults={'base_price': base_price, 'is_available': True}
        )

        serializer = self.get_serializer(obj)
        return self.success_response(
            data=serializer.data,
            message='Price updated/created successfully'
        )
