# Website Development Rules

## Django Project Rules

PROFESSIONAL AND MINIMALISTIC


### Project Structure
- Follow the standard Django project structure: myproject (settings) and mainapp (main application)
- Keep all Django apps in the root directory alongside myproject
- Store static files in the `static` directory with appropriate subdirectories (css, js, images)
- Use `mainapp/templates/mainapp/` for templates following Django app convention

### Django Settings & Configuration
- Keep DEBUG=True only in development environments
- Never commit actual SECRET_KEY values to version control (use environment variables)
- Always list all custom apps in INSTALLED_APPS
- Use Pathlib's `BASE_DIR` for all path operations
- SQLite for development, consider PostgreSQL/MySQL for production

### Models
- Create models in `mainapp/models.py` 
- Always create migrations after model changes: `python3 manage.py makemigrations`
- Apply migrations with: `python3 manage.py migrate`
- Use descriptive field names and appropriate field types
- Add `__str__` methods to models for better admin representation

### Views
- Organize views in `mainapp/views.py` for small applications
- For larger projects (500+ lines), create `mainapp/views/` package with feature-specific modules:
  - `auth_views.py` - Authentication and health check views
  - `landing_views.py` - Landing pages (admin/customer/groomer)
  - `booking_views.py` - Booking and appointment views
  - `customer_views.py` - Customer profile and dog management
  - `admin_views.py` - Admin dashboard and management views
  - `pricing_views.py` - Pricing configuration views
  - `schedule_views.py` - Schedule and time slot management
- Use function-based views for simplicity unless class-based views are clearly beneficial
- Always use `render()` shortcut for template responses
- Pass context as dictionary when needed
- Use meaningful view function names

### URLs
- Define URLs in `myproject/urls.py` for project-level routing
- Create `mainapp/urls.py` for app-specific routing when app has multiple views
- Always use `name=` parameter in path definitions for reverse URL resolution
- Use `{% url 'viewname' %}` in templates instead of hardcoded URLs

### Templates
- Use `{% extends "mainapp/base.html" %}` for all page templates
- Define content in `{% block content %}` blocks
- Customize page titles in `{% block title %}` blocks
- Keep HTML5 DOCTYPE and meta tags in base template
- Load template tags at the top of templates when needed

## Python Code Rules

### Code Style
- Follow PEP 8 Python style guide
- Use 4 spaces for indentation (no tabs)
- Use snake_case for variable names and function names
- Use CamelCase for class names
- Use UPPER_CASE for constants

### Imports
- Group imports: standard library, third-party, local application imports
- Keep imports at the top of files, before any code
- Use absolute imports over relative imports in Django projects
- Remove unused imports

### Documentation
- Add docstrings to all functions that are not self-explanatory
- Keep comments minimal and meaningful
- Explain "why" not "what" in comments

### Error Handling
- Use Django's built-in error handling (404, 500 pages)
- Validate forms in views before processing
- Use try-except blocks for operations that might fail

## Tailwind CSS Rules

### CSS Organization
- Load Tailwind CSS using `{% tailwind_css %}` tag in base template
- Use utility classes from Tailwind instead of custom CSS when possible
- Use `static/css/` directory for any custom CSS files
- Use responsive prefixes (md:, lg:, xl:) for responsive design

### Design Consistency
- Maintain consistent color scheme using predefined Tailwind colors
- Use spacing scale (2, 4, 8, 16, etc.) consistently
- Apply consistent rounded corners, shadows, and transitions
- Use hover states for all interactive elements

### Responsive Design
- Design mobile-first: base styles for mobile, add md: and lg: for larger screens
- Test layouts on viewport sizes below 768px (mobile), 768px+ (tablet), 1024px+ (desktop)
- Ensure navigation is usable on all screen sizes

## Database Rules

### Development
- Use SQLite for development (already configured)
- Reset database by deleting db.sqlite3 then running `python3 manage.py migrate` when needed
- Keep database file in project root (not in version control)
- Never commit db.sqlite3 to version control

### Model Changes
- Always create migrations before applying: `makemigrations` then `migrate`
- Check migration files to understand what changes will be applied
- Use `--fake` flag if migrations have already been applied manually

## Development Workflow

### Running the Project
- Use `run.bat` to start development server
- Default address: http://127.0.0.1:8000
- Keep server running for hot reload with django-browser-reload

### Testing
- Write tests in `mainapp/tests.py`
- Run tests with: `python3 manage.py test`
- Keep tests simple and focused

### Admin Panel
- Access admin at /admin/
- Create superuser with: `python3 manage.py createsuperuser`
- Register models in `mainapp/admin.py` for admin interface

## Security Rules

### Development vs Production
- Set DEBUG=False in production
- Configure ALLOWED_HOSTS properly in production
- Use environment variables for secrets in production
- Enable SSL/HTTPS in production

### Data Protection
- Never hardcode sensitive data (API keys, passwords)
- Use Django's built-in authentication system
- Validate all user input
- Use CSRF protection (enabled by default)

## File Naming Conventions

### Django Files
- Models: `models.py` (one file per app)
- Views: `views.py` for small apps or `views/` package with feature modules for large apps
- URLs: `urls.py` for project and app-level routing
- Forms: `forms.py` if forms are complex
- Templates: `{app_name}/{page_name}.html`

### Static Files
- CSS: `static/css/{name}.css`
- JavaScript: `static/js/{name}.js`
- Images: `static/images/{category}/{name}.ext`

## Git Workflow (when initialized)

### Commits
- Write clear, descriptive commit messages
- Commit related changes together
- Review changes with `git diff` before committing
- Never commit `db.sqlite3` or `__pycache__/`

### .gitignore
- Ignore: `db.sqlite3`, `__pycache__/`, `*.pyc`, `.django_tailwind_cli/`, `node_modules/`
- Ignore environment variable files (`.env`)
- Ignore IDE files (.vscode/, .idea/)

## Common Commands

```bash
# Start development server
python3 manage.py runserver

# Create migrations after model changes
python3 manage.py makemigrations

# Apply migrations
python3 manage.py migrate

# Create superuser for admin
python3 manage.py createsuperuser

# Run tests
python3 manage.py test

# Collect static files (production)
python3 manage.py collectstatic

# Start Django shell
python3 manage.py shell
```

## Design Principles

### Keep It Simple
- Start with simple solutions, add complexity only when needed
- Prefer Django's built-in functionality over custom solutions
- Use existing packages when they solve the problem well

### Maintainability
- Write code that others can understand
- Keep functions focused and short
- Avoid deeply nested code
- Use meaningful variable names

### Performance
- Optimize database queries (use select_related, prefetch_related)
- Use Django's caching for expensive operations
- Load static files efficiently
- Consider CDN for production static files
