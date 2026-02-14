"""
API v1 URL configuration for REST Framework endpoints.
This router handles all DRF ViewSets with versioned URLs (/api/v1/).
"""
from django.urls import path
from rest_framework import routers
from .viewsets import (
    ServiceViewSet, BreedViewSet, GroomerViewSet, BreedServiceMappingViewSet
)
from .apiviews import (
    # Booking Flow
    BookingCalculatePriceView, BookingCalculateFinalPriceView,
    BookingAvailableDaysView, BookingTimeSlotsView, BookingSubmitView,
    # Appointment Management
    DashboardStatsView, UpdateAppointmentStatusView,
    # Time Slot Management
    TimeSlotCreateView, TimeSlotManageView, TimeSlotDeleteView,
    TimeSlotDeleteDateView, DayTimeSlotsView, SetDayTimeSlotsView,
    BatchDayTimeSlotsView,
    # Pricing Management
    CloneBreedPricingView, CreateBreedWithCloneView,
    BatchSavePricingManagementView,
    # Legal Agreements
    ActiveAgreementView,
    # Customer Dogs
    CustomerDogsView
)

# DRF Router for v1 API
router = routers.DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'breeds', BreedViewSet, basename='breed')
router.register(r'groomers', GroomerViewSet, basename='groomer')
router.register(r'breed-service-mappings', BreedServiceMappingViewSet, basename='breedservicemapping')

urlpatterns = router.urls + [
    # =============================================================================
    # Booking Flow Endpoints (public)
    # =============================================================================
    path('booking/calculate-price/', BookingCalculatePriceView.as_view(), name='api_v1_booking_calculate_price'),
    path('booking/calculate-final-price/', BookingCalculateFinalPriceView.as_view(), name='api_v1_booking_calculate_final_price'),
    path('booking/available-days/', BookingAvailableDaysView.as_view(), name='api_v1_booking_available_days'),
    path('booking/time-slots/', BookingTimeSlotsView.as_view(), name='api_v1_booking_time_slots'),
    path('booking/submit/', BookingSubmitView.as_view(), name='api_v1_booking_submit'),

    # =============================================================================
    # Appointment Management Endpoints
    # =============================================================================
    path('admin/dashboard-stats/', DashboardStatsView.as_view(), name='api_v1_dashboard_stats'),
    path('admin/appointments/update-status/', UpdateAppointmentStatusView.as_view(), name='api_v1_update_appointment_status'),

    # =============================================================================
    # Time Slot Management Endpoints
    # =============================================================================
    path('admin/time-slots/create/', TimeSlotCreateView.as_view(), name='api_v1_time_slots_create'),
    path('admin/time-slots/manage/', TimeSlotManageView.as_view(), name='api_v1_time_slots_manage'),
    path('admin/time-slots/delete/', TimeSlotDeleteView.as_view(), name='api_v1_time_slot_delete'),
    path('admin/time-slots/delete-date/', TimeSlotDeleteDateView.as_view(), name='api_v1_time_slots_delete_date'),
    path('admin/time-slots/day/', DayTimeSlotsView.as_view(), name='api_v1_day_time_slots'),
    path('admin/time-slots/set-day/', SetDayTimeSlotsView.as_view(), name='api_v1_set_day_time_slots'),
    path('admin/time-slots/batch/', BatchDayTimeSlotsView.as_view(), name='api_v1_batch_day_time_slots'),

    # =============================================================================
    # Pricing Management Endpoints
    # =============================================================================
    path('admin/pricing/batch-save/', BatchSavePricingManagementView.as_view(), name='api_v1_batch_save_pricing_management'),
    path('admin/pricing/breed/clone/', CloneBreedPricingView.as_view(), name='api_v1_clone_breed_pricing'),
    path('admin/pricing/breed/create-with-clone/', CreateBreedWithCloneView.as_view(), name='api_v1_create_breed_with_clone'),

    # =============================================================================
    # Legal Agreement Endpoints
    # =============================================================================
    path('booking/active-agreement/', ActiveAgreementView.as_view(), name='api_v1_active_agreement'),

    # =============================================================================
    # Customer Dogs Endpoints
    # =============================================================================
    path('customer/dogs/', CustomerDogsView.as_view(), name='api_v1_customer_dogs'),
]
