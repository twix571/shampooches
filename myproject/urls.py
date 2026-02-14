"""
URL configuration for myproject project.

This module defines the URL patterns and routing for the application.
"""

import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from mainapp import views
from mainapp.views import admin_views, messaging_views
from mainapp.viewsets import (
    ServiceViewSet, BreedViewSet, GroomerViewSet, BreedServiceMappingViewSet
)

# ============================================================================
# DRF Router Configuration
# ============================================================================

router = routers.DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'breeds', BreedViewSet, basename='breed')
router.register(r'groomers', GroomerViewSet, basename='groomer')
router.register(r'breed-service-mappings', BreedServiceMappingViewSet, basename='breedservicemapping')

# ============================================================================
# URL Patterns
# ============================================================================

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='health_check'),
    
    # Authentication URLs
    path('admin/logout/', views.custom_logout, name='custom_logout'),
    path('login/', views.custom_login, name='custom_login'),
    path('customer/sign-up/', views.customer_sign_up, name='customer_sign_up'),
    path('customer/profile/', views.customer_profile, name='customer_profile'),
    
    # Dog profile management URLs
    path('customer/dogs/add/', views.add_dog, name='add_dog'),
    path('customer/dogs/edit/<int:dog_id>/', views.edit_dog, name='edit_dog'),
    path('customer/dogs/delete/<int:dog_id>/', views.delete_dog, name='delete_dog'),
    path('customer/dogs/add-modal/', views.add_dog_modal, name='add_dog_modal'),
    path('customer/dogs/edit-modal/<int:dog_id>/', views.edit_dog_modal, name='edit_dog_modal'),
    path('customer/dogs/request-deletion-modal/<int:dog_id>/', views.request_dog_deletion_modal, name='request_dog_deletion_modal'),
    path('customer/dogs/request-deletion/<int:dog_id>/', views.request_dog_deletion, name='request_dog_deletion'),
    path('customer/dogs/book/<int:dog_id>/', views.book_with_dog, name='book_with_dog'),

    # Appointment management URLs
    path('customer/appointments/rebook/<int:appointment_id>/', views.rebook_appointment, name='rebook_appointment'),
    path('customer/appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('customer/appointments/cancel-confirm/<int:appointment_id>/', views.cancel_appointment_confirm_modal, name='cancel_appointment_confirm_modal'),
    
    # Booking URLs
    
    # Landing pages
    path('', views.customer_landing, name='customer_landing'),
    path('admin-landing/', views.admin_landing, name='admin_landing'),
    path('groomer-landing/', views.groomer_landing, name='groomer_landing'),
    
    # Booking and appointment URLs
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('services/', views.services_list, name='services_list'),
    path('appointments/', views.appointments_modal, name='appointments_modal'),
    
    # Management modals
    path('customers/', views.customers_modal, name='customers_modal'),
    path('groomers/', views.groomers_modal, name='groomers_modal'),
    path('admin/groomers-management/', views.groomers_management_modal, name='groomers_management_modal'),
    path('admin/site-config/', views.site_config_modal, name='site_config_modal'),
    path('admin/legal-agreements/', views.legal_agreements_modal, name='legal_agreements_modal'),
    
    # Pricing management URLs
    path('admin/pricing/', views.pricing_management, name='pricing_management'),
    path('admin/weight-ranges-editor/<int:breed_id>/', views.weight_ranges_editor_modal, name='weight_ranges_editor_modal'),
    path('admin/update-breed-weight-pricing/', views.update_breed_weight_pricing, name='update_breed_weight_pricing'),
    path('admin/breed-pricing-table/<int:breed_id>/', views.breed_pricing_table_modal, name='breed_pricing_table_modal'),
    path('admin/breed-cloning-wizard/', views.breed_cloning_wizard_modal, name='breed_cloning_wizard_modal'),
    path('admin/export-pricing-config/', views.export_pricing_config, name='export_pricing_config'),
    path('admin/import-pricing-config/', views.import_pricing_config, name='import_pricing_config'),
    
    # Time slot management URLs
    path('admin/time-slot-editor/', views.time_slot_editor_modal, name='time_slot_editor_modal'),

    # HTMX partial rendering URLs
    path('htmx/groomer-options/', views.render_groomer_options, name='htmx_groomer_options'),
    path('htmx/time-slots/', views.render_time_slots, name='htmx_time_slots'),

    # Contact/Messaging URLs
    path('contact/', messaging_views.contact_page, name='contact_page'),
    path('contact/staff/', messaging_views.staff_contact_page, name='staff_contact_page'),
    path('contact/authenticated/', messaging_views.contact_page_authenticated, name='contact_page_authenticated'),
    path('contact/why-account/', messaging_views.why_create_account_page, name='why_create_account'),

    # Messaging API endpoints
    path('api/contact/threads/create/', messaging_views.create_message_thread, name='create_message_thread'),
    path('api/contact/threads/<int:thread_id>/messages/', messaging_views.get_thread_messages, name='get_thread_messages'),
    path('api/contact/threads/<int:thread_id>/send/', messaging_views.send_message, name='send_message'),
    path('api/contact/threads/<int:thread_id>/update-view/', messaging_views.update_thread_view, name='update_thread_view'),
    path('api/contact/threads/<int:thread_id>/typing/', messaging_views.set_typing_indicator, name='set_typing_indicator'),
    path('api/contact/threads/<int:thread_id>/status/', messaging_views.get_thread_status, name='get_thread_status'),

    # Staff messaging API endpoints
    path('api/contact/staff/threads/', messaging_views.customer_threads_list, name='customer_threads_list'),
    path('api/contact/staff/threads/<int:thread_id>/messages/', messaging_views.staff_thread_messages, name='staff_thread_messages'),

    # API URLs
    path('api/v1/', include('mainapp.api_v1_urls')),
    path('api/', include(router.urls)),
]

# Django admin interface
urlpatterns.append(path('admin/', admin.site.urls))

# ============================================================================
# Static and Media Files (Development Only)
# ============================================================================

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
