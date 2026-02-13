from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import Service, Customer, Appointment, Groomer, Breed, BreedServiceMapping, SiteConfig


class BreedServiceMappingInline(admin.TabularInline):
    """Inline admin interface for BreedServiceMapping model."""
    model = BreedServiceMapping
    extra = 0
    autocomplete_fields = ['service']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['service', 'is_available', 'base_price', 'created_at', 'updated_at']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model with comprehensive fieldsets."""
    list_display = ['name', 'price', 'pricing_type', 'duration_minutes', 
                    'exempt_from_surcharge', 'is_active', 'breed_count', 'created_at']
    list_filter = ['pricing_type', 'is_active', 'exempt_from_surcharge', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    actions = ['mark_as_active', 'mark_as_inactive']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Pricing Configuration', {
            'fields': ('price', 'pricing_type', 'exempt_from_surcharge'),
            'classes': ('collapse',)
        }),
        ('Service Details', {
            'fields': ('duration_minutes', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def breed_count(self, obj):
        """Count number of breeds associated with this service."""
        count = obj.breed_mappings.filter(is_available=True).count()
        return count
    breed_count.short_description = 'Active Breeds'

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} services marked as active.')
    mark_as_active.short_description = 'Mark selected services as active'

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} services marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected services as inactive'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model."""
    list_display = ['name', 'email', 'phone', 'user_status', 'appointment_count', 'created_at']
    list_filter = ['user__user_type', 'created_at']
    search_fields = ['name', 'email', 'phone', 'user__username']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user']

    fieldsets = (
        ('Linked Account', {
            'fields': ('user',)
        }),
        ('Customer Information', {
            'fields': ('name', 'email', 'phone', 'address')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_status(self, obj):
        """Display whether customer has an account."""
        if obj.user:
            return obj.user.username
        return 'Guest'
    user_status.short_description = 'Account'

    def appointment_count(self, obj):
        """Count number of appointments for this customer."""
        return obj.appointments.count()
    appointment_count.short_description = 'Appointments'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for Appointment model with organized fieldsets."""
    list_display = ['customer', 'service', 'dog_name', 'groomer', 'date', 'time', 
                    'status', 'price_at_booking', 'created_at']
    list_filter = ['status', 'date', 'service', 'groomer']
    search_fields = ['customer__name', 'dog_name', 'dog_breed__name', 'customer__email']
    ordering = ['-date', '-time']
    readonly_fields = ['created_at', 'updated_at', 'price_at_booking']
    date_hierarchy = 'date'
    autocomplete_fields = ['customer', 'service', 'dog_breed', 'groomer']
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('customer', 'service', 'date', 'time', 'status')
        }),
        ('Personnel', {
            'fields': ('groomer',)
        }),
        ('Dog Information', {
            'fields': ('dog_name', 'dog_breed', 'dog_weight', 'dog_age', 'dog_size')
        }),
        ('Pricing', {
            'fields': ('price_at_booking',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_cancelled']

    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} appointments marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected as confirmed'

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointments marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} appointments marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected as cancelled'


@admin.register(Groomer)
class GroomerAdmin(admin.ModelAdmin):
    """Admin interface for Groomer model."""
    list_display = ['name', 'specialties', 'is_active', 'order', 'appointment_count', 'created_at']
    list_display_links = ['name']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'bio', 'specialties']
    ordering = ['order', 'name']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Groomer Information', {
            'fields': ('name', 'bio', 'specialties', 'image')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def appointment_count(self, obj):
        """Count number of appointments for this groomer."""
        return obj.appointments.count()
    appointment_count.short_description = 'Appointments'


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    """Admin interface for Breed model with comprehensive pricing fieldsets."""
    list_display = ['name', 'base_price', 'pricing_summary', 'is_active', 'service_count', 'created_at']
    list_filter = ['is_active', 'breed_pricing_complex', 'created_at']
    search_fields = ['name', 'description', 'clone_note']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'pricing_cloned_from']
    inlines = [BreedServiceMappingInline]
    actions = ['mark_as_active', 'mark_as_inactive']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (('name', 'is_active'),)
        }),
        ('Base Pricing', {
            'fields': (('base_price', 'breed_pricing_complex'),)
        }),
        ('Weight-Based Pricing', {
            'fields': (
                ('start_weight', 'weight_range_amount'),
                ('weight_price_amount'),
                ('typical_weight_min', 'typical_weight_max'),
            ),
            'classes': ('collapse',)
        }),
        ('Cloning Information', {
            'fields': ('pricing_cloned_from', 'clone_note'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def pricing_summary(self, obj):
        """Show pricing summary for this breed."""
        if obj.breed_pricing_complex:
            return format_html('<span style="color: orange;">Complex pricing</span>')
        elif obj.base_price:
            return f'${obj.base_price}'
        return 'Not configured'
    pricing_summary.short_description = 'Pricing'

    def service_count(self, obj):
        """Count number of available services for this breed."""
        return obj.service_mappings.filter(is_available=True).count()
    service_count.short_description = 'Available Services'

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} breeds marked as active.')
    mark_as_active.short_description = 'Mark selected as active'

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} breeds marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected as inactive'


@admin.register(BreedServiceMapping)
class BreedServiceMappingAdmin(admin.ModelAdmin):
    """Admin interface for BreedServiceMapping model."""
    list_display = ['breed', 'service', 'is_available', 'base_price', 'created_at']
    list_filter = ['breed', 'service', 'is_available', 'created_at']
    search_fields = ['breed__name', 'service__name']
    ordering = ['breed__name', 'service__name']
    list_editable = ['is_available']
    autocomplete_fields = ['breed', 'service']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Mapping Details', {
            'fields': (('breed', 'service'), 'is_available', 'base_price')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    """Admin interface for SiteConfig model."""
    list_display = ['business_name', 'phone', 'email', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at', 'created_at']
    search_fields = ['business_name', 'email', 'phone']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Business Information', {
            'fields': ('business_name',)
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Business Hours', {
            'fields': (
                ('monday_open', 'monday_close'),
                ('tuesday_open', 'tuesday_close'),
                ('wednesday_open', 'wednesday_close'),
                ('thursday_open', 'thursday_close'),
                ('friday_open', 'friday_close'),
                ('saturday_open', 'saturday_close'),
                ('sunday_open', 'sunday_close'),
            ),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_active', 'mark_as_inactive']

    def mark_as_active(self, request, queryset):
        """Mark selected configurations as active (only one can be active)."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} site configuration(s) marked as active.')
    mark_as_active.short_description = 'Mark as active'

    def mark_as_inactive(self, request, queryset):
        """Mark selected configurations as inactive."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} site configuration(s) marked as inactive.')
    mark_as_inactive.short_description = 'Mark as inactive'
