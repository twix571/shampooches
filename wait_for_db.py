#!/usr/bin/env python
"""
Wait for the database to be ready before proceeding.
Then run migrations and start gunicorn.
"""
import os
import sys
import time
import psycopg2

# Force Python to flush stdout immediately for proper logging in Railway
os.environ['PYTHONUNBUFFERED'] = '1'

def log(message):
    """Log to both stdout and stderr for Railway compatibility"""
    print(message, flush=True, file=sys.stdout)
    print(message, flush=True, file=sys.stderr)

def wait_for_db(max_retries=60, retry_interval=2):
    """Wait for database to be ready using direct PostgreSQL connection."""
    DATABASE_URL = os.getenv('DATABASE_URL')
    log(f"DATABASE_URL is set: {'Yes' if DATABASE_URL else 'No'}")
    if not DATABASE_URL:
        log("Error: DATABASE_URL environment variable not set")
        return False
    
    for attempt in range(max_retries):
        try:
            log(f"Attempting database connection (attempt {attempt + 1}/{max_retries})...")
            # Test database connection directly with psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            log(f"Database is ready after {attempt + 1} attempt(s)!")
            return True
        except Exception as e:
            log(f"Database not ready, retrying in {retry_interval} seconds...")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
    log(f"Failed to connect to database after {max_retries} attempts")
    return False

def run_migrations():
    """Run Django migrations."""
    log("Running database migrations...")
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')

    import django
    django.setup()

    from django.core.management import call_command
    call_command('migrate', '--noinput')
    log("Migrations completed successfully")

def collect_static():
    """Collect static files."""
    log("Collecting static files...")
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')

    import django
    django.setup()

    from django.core.management import call_command
    try:
        call_command('collectstatic', '--noinput')
        log("Static files collected successfully")
    except Exception as e:
        log(f"Warning: Static file collection failed: {e}")

def start_gunicorn():
    """Start gunicorn with production settings."""
    log("Starting gunicorn...")
    # Ensure DJANGO_SETTINGS_MODULE is set for gunicorn
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
    # Use PORT environment variable if set (Railway sets this), default to 8000
    port = os.getenv('PORT', '8000')
    log(f"Binding to port: {port}")
    log(f"PORT environment variable: {port}")
    # Use os.exec to properly replace the current process with gunicorn
    # This ensures proper signal handling and process management in Railway
    args = [
        'gunicorn',
        'myproject.wsgi:application',
        '--bind', f'0.0.0.0:{port}',
        '--timeout', '300',
        '--workers', '2',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info'
    ]
    log(f"Executing: {' '.join(args)}")
    os.execvp(args[0], args)

if __name__ == '__main__':
    log("=== Starting Railway deployment script ===")
    log(f"Python version: {sys.version}")
    log(f"Current working directory: {os.getcwd()}")
    
    # Create media directory
    os.makedirs('/data/media', exist_ok=True)
    log("Starting Railway deployment...")
    
    if wait_for_db():
        log("Database ready, proceeding with migrations...")
        run_migrations()
        log("Migrations complete, proceeding with static files collection...")
        collect_static()
        log("Static files collection complete, starting gunicorn...")
        start_gunicorn()
    else:
        log("Database connection failed, exiting...")
        sys.exit(1)
