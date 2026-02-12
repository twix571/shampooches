from django.test import TestCase, override_settings
from django.urls import reverse, resolve


class URLPatternsTestCase(TestCase):
    """Test URL patterns configuration and naming."""

    def test_update_breed_weight_pricing_url_name_is_correct(self):
        """Test that update_breed_weight_pricing URL has correct spelling in its name."""
        # This URL should be named 'update_breed_weight_pricing' not 'update_breed_weight_picing'
        try:
            url = reverse('update_breed_weight_pricing')
            self.assertIsNotNone(url, "URL 'update_breed_weight_pricing' should be resolvable")
        except Exception as e:
            self.fail(f"URL 'update_breed_weight_pricing' should be resolvable, got error: {e}")

    def test_update_breed_weight_pricing_url_resolves_correctly(self):
        """Test that the URL resolves to the correct path."""
        url = reverse('update_breed_weight_pricing')
        self.assertEqual(url, '/admin/update-breed-weight-pricing/')

    def test_admin_dashboard_url_not_conflicting(self):
        """Test that admin URLs don't have conflicting paths."""
        # admin-landing/ should be for custom admin landing page
        url = reverse('admin_landing')
        # Should point to /admin-landing/
        self.assertEqual(url, '/admin-landing/')

    def test_admin_panel_url_exists(self):
        """Test that admin panel URL exists for Django admin."""
        # Admin panel is at a non-obvious URL for security
        url = '/django-panel-secret-8f3k2Lm9/'
        response = self.client.get(url)
        # Should get a redirect to login page (302) because admin requires auth
        self.assertIn(response.status_code, [302, 301])
