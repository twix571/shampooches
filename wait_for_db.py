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

def wait_for_db(max_retries=60, retry_interval=2):
    """Wait for database to be ready using direct PostgreSQL connection."""
    DATABASE_URL = os.getenv('DATABASE_URL')
    print(f"DATABASE_URL is set: {'Yes' if DATABASE_URL else 'No'}", flush=True)
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set", flush=True)
        return False
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting database connection (attempt {attempt + 1}/{max_retries})...", flush=True)
            # Test database connection directly with psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print(f"Database is ready after {attempt + 1} attempt(s)!", flush=True)
            return True
        except Exception as e:
            print(f"Database not ready, retrying in {retry_interval} seconds...", flush=True)
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
    print(f"Failed to connect to database after {max_retries} attempts", flush=True)
    return False

def run_migrations():
    """Run Django migrations."""
    print("Running database migrations...", flush=True)
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
    
    import django
    django.setup()
    
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    print("Migrations completed successfully", flush=True)

def collect_static():
    """Collect static files."""
    print("Collecting static files...", flush=True)
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
    
    import django
    django.setup()
    
    from django.core.management import call_command
    try:
        call_command('collectstatic', '--noinput', '--clear')
        print("Static files collected successfully", flush=True)
    except Exception as e:
        print(f"Warning: Static file collection failed: {e}", flush=True)

def start_gunicorn():
    """Start gunicorn with production settings."""
    print("Starting gunicorn...", flush=True)
    # Ensure DJANGO_SETTINGS_MODULE is set for gunicorn
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
    # Use PORT environment variable if set (Railway sets this), default to 8000
    port = os.getenv('PORT', '8000')
    print(f"Binding to port: {port}", flush=True)
    print(f"PORT environment variable: {port}", flush=True)
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
    print(f"Executing: {' '.join(args)}", flush=True)
    os.execvp(args[0], args)

if __name__ == '__main__':
    print("=== Starting Railway deployment script ===", flush=True)
    print(f"Python version: {sys.version}", flush=True)
    print(f"Current working directory: {os.getcwd()}", flush=True)
    
    # Create media directory
    os.makedirs('/data/media', exist_ok=True)
    print("Starting Railway deployment...", flush=True)
    
    if wait_for_db():
        print("Database ready, proceeding with migrations...", flush=True)
        run_migrations()
        print("Migrations complete, proceeding with static files collection...", flush=True)
        collect_static()
        print("Static files collection complete, starting gunicorn...", flush=True)
        start_gunicorn()
    else:
        print("Database connection failed, exiting...", flush=True)
        sys.exit(1)
