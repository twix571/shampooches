"""Admin views for managing customers, groomers, and site configuration."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from mainapp.models import Customer, Groomer, SiteConfig, LegalAgreement
from mainapp.utils import admin_required


@admin_required
def customers_modal(request):
    """
    Render the customers list modal.

    Displays all customers in the database ordered by name.
    """
    customers = Customer.objects.all().order_by('name')
    return render(request, 'mainapp/admin/customers_modal.html', {'customers': customers})


def groomers_modal(request):
    """
    Render the groomers list modal.

    Displays only active groomers ordered by display order and name.
    """
    groomers = Groomer.objects.filter(is_active=True).order_by('order', 'name')
    return render(request, 'mainapp/admin/groomers_list_modal.html', {'groomers': groomers})


@admin_required
def groomers_management_modal(request):
    """
    Render the groomers management modal.

    Displays all including inactive groomers for administrative purposes.
    """
    groomers = Groomer.objects.all().order_by('order', 'name')
    return render(request, 'mainapp/admin/groomers_management_modal.html', {'groomers': groomers})


@admin_required
def site_config_modal(request):
    """
    Render the site configuration modal.

    Displays business information, contact details, and business hours.
    Changes affect the customer landing page, booking flow, and contact displays.
    """
    site_config = SiteConfig.get_active_config()
    return render(request, 'mainapp/admin/site_config_modal.html', {'site_config': site_config})


@admin_required
def legal_agreements_modal(request):
    """
    Render the legal agreements modal.

    Displays all legal agreement versions with the active one highlighted.
    Staff can create, edit, and manage agreement versions.
    """
    active_agreement = LegalAgreement.get_active_agreement()
    agreements = LegalAgreement.objects.all().order_by('-effective_date')
    return render(request, 'mainapp/admin/legal_agreements_modal.html', {
        'active_agreement': active_agreement,
        'agreements': agreements,
        'agreement_count': agreements.count()
    })
