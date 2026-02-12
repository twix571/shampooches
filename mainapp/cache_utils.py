"""
Cache utilities for Django models and frequently accessed data.
"""
import logging
from django.core.cache import cache
from django.conf import settings
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def cache_model_result(
    prefix: str,
    timeout: int = 300,
    args_to_keys: Optional[Callable] = None
):
    """
    Decorator to cache results of model-based functions.

    Args:
        prefix: Cache key prefix.
        timeout: Cache timeout in seconds.
        args_to_keys: Optional function to convert args to cache key parts.

    Example:
        @cache_model_result('breed_prices', timeout=600)
        def get_breed_price(breed_id):
            return Breed.objects.get(id=breed_id).base_price
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            if args_to_keys:
                key_parts = args_to_keys(*args, **kwargs)
            else:
                key_parts = [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]

            cache_key = f'{prefix}_{"_".join(key_parts)}'

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)

            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(prefix: str) -> None:
    """
    Invalidate all cache keys starting with a given prefix.

    Args:
        prefix: Cache key prefix to invalidate.

    Note:
        For Redis cache, uses SCAN and DELETE for efficient pattern-based invalidation.
        For other backends, falls back to simpler invalidation methods.
    """
    if 'REDIS_REDIS_CACHE' in settings.CACHES.get('default', {}).get('BACKEND', ''):
        # Redis-specific implementation - use SCAN and DELETE
        try:
            cache_instance = cache
            client = cache_instance._cache
            keys = []
            for key in client.scan_iter(match=f'*{prefix}*'):
                keys.append(key)
            if keys:
                client.delete(*keys)
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.warning(f'Failed to invalidate Redis cache pattern {prefix}: {e}')
    else:
        # For local memory cache or DB cache
        # Use a simple approach: clear the specific keys we know about
        known_keys = [
            f'{prefix}_True',
            f'{prefix}_False',
            f'services_list_{""}',
            f'breeds_list_{""}',
            f'groomers_list_{""}',
            f'weight_ranges_list_{""}'
        ]
        for key in known_keys:
            cache.delete(key)


class QueryCache:
    """
    Helper class for caching common query results.
    """

    @staticmethod
    def get_cached_services(active_only: bool = True, timeout: int = 600) -> list:
        """
        Get cached list of services.

        Args:
            active_only: Whether to only return active services.
            timeout: Cache timeout in seconds.

        Returns:
            List of Service objects.
        """
        from .models import Service

        cache_key = f'services_list_{active_only}'
        services = cache.get(cache_key)

        if services is None:
            queryset = Service.objects.all()
            if active_only:
                queryset = queryset.filter(is_active=True)
            services = list(queryset.values('id', 'name', 'price', 'pricing_type', 'duration_minutes'))
            cache.set(cache_key, services, timeout)

        return services

    @staticmethod
    def get_cached_breeds(active_only: bool = True, timeout: int = 600) -> list:
        """
        Get cached list of breeds.

        Args:
            active_only: Whether to only return active breeds.
            timeout: Cache timeout in seconds.

        Returns:
            List of Breed objects.
        """
        from .models import Breed

        cache_key = f'breeds_list_{active_only}'
        breeds = cache.get(cache_key)

        if breeds is None:
            queryset = Breed.objects.all()
            if active_only:
                queryset = queryset.filter(is_active=True)
            breeds = list(queryset.values('id', 'name', 'base_price'))
            cache.set(cache_key, breeds, timeout)

        return breeds

    @staticmethod
    def get_cached_groomers(active_only: bool = True, timeout: int = 300) -> list:
        """
        Get cached list of groomers.

        Args:
            active_only: Whether to only return active groomers.
            timeout: Cache timeout in seconds.

        Returns:
            List of Groomer objects.
        """
        from .models import Groomer

        cache_key = f'groomers_list_{active_only}'
        groomers = cache.get(cache_key)

        if groomers is None:
            queryset = Groomer.objects.all()
            if active_only:
                queryset = queryset.filter(is_active=True)
            groomers = list(queryset.values('id', 'name', 'bio'))
            cache.set(cache_key, groomers, timeout)

        return groomers

    @staticmethod
    def invalidate_services() -> None:
        """Invalidate services cache."""
        cache.delete('services_list_True')
        cache.delete('services_list_False')

    @staticmethod
    def invalidate_breeds() -> None:
        """Invalidate breeds cache."""
        cache.delete('breeds_list_True')
        cache.delete('breeds_list_False')

    @staticmethod
    def invalidate_groomers() -> None:
        """Invalidate groomers cache."""
        cache.delete('groomers_list_True')
        cache.delete('groomers_list_False')

    @staticmethod
    def invalidate_all() -> None:
        """Invalidate all cached query results."""
        invalidate_cache_pattern('services_list')
        invalidate_cache_pattern('breeds_list')
        invalidate_cache_pattern('groomers_list')


class CacheInvalidationMixin:
    """
    Mixin for Django models to automatically invalidate cache on save/delete.
    """

    def save(self, *args, **kwargs):
        """Override save to invalidate related cache."""
        self._invalidate_cache()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to invalidate related cache."""
        self._invalidate_cache()
        super().delete(*args, **kwargs)

    def _invalidate_cache(self) -> None:
        """
        Invalidate cache for this model instance.
        Override in models that specific caching needs.
        """
        pass
