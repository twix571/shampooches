"""Views module for the grooming salon application.

This package contains all view functions organized by feature:
- auth_views.py: Login, logout, sign-up, health check
- landing_views.py: Landing pages for admin, customer, groomer
- booking_views.py: Booking modal and related views
- customer_views.py: Customer profile and dog management
- admin_views.py: Admin dashboard and modals
- pricing_views.py: Pricing management, import/export
- schedule_views.py: Time slots and schedule management
- messaging_views.py: Contact messaging system
"""

# For backward compatibility, maintain imports at package level
from .auth_views import *  # noqa: F401, F403
from .landing_views import *  # noqa: F401, F403
from .booking_views import *  # noqa: F401, F403
from .customer_views import *  # noqa: F401, F403
from .admin_views import *  # noqa: F401, F403
from .pricing_views import *  # noqa: F401, F403
from .schedule_views import *  # noqa: F401, F403
from .messaging_views import *  # noqa: F401, F403
