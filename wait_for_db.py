#!/usr/bin/env python
"""
Wait for the database to be ready before proceeding.
Then run migrations and start gunicorn.
"""
import os
import sys
import time
import psycopg2
import subprocess

def wait_for_db(max_retries=60, retry_interval=2):
    """Wait for database to be ready using direct PostgreSQL connection."""
    DATABASE_URL = os.getenv('DATABASE_URL')
    print(f"DATABASE_URL is set: {'Yes' if DATABASE_URL else 'No'}")
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        return False
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting database connection (attempt {attempt + 1}/{max_retries})...")
            # Test database connection directly with psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print(f"Database is ready after {attempt + 1} attempt(s)!")
            return True
        except Exception as e:
            print(f"Database not ready, retrying in {retry_interval} seconds...")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
    print(f"Failed to connect to database after {max_retries} attempts")
    return False

def run_migrations():
    """Run Django migrations."""
    print("Running database migrations...")
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
    
    import django
    django.setup()
    
    from django.core.management import call_command
    call_command('migrate', '--noinput')
    print("Migrations completed successfully")

def start_gunicorn():
    """Start gunicorn with production settings."""
    print("Starting gunicorn...")
    # Use the same settings as production
    # Subprocess will inherit the environment including DATABASE_URL
    subprocess.run([
        'gunicorn', 
        'myproject.wsgi:application',
        '--bind', '0.0.0.0:8000',
        '--timeout', '300',
        '--workers', '2',
        '--access-logfile', '-'
    ], check=True)

if __name__ == '__main__':
    # Create media directory
    os.makedirs('/data/media', exist_ok=True)
    print("Starting Railway deployment...")
    
    if wait_for_db():
        run_migrations()
        start_gunicorn()
    else:
        print("Database connection failed, exiting...")
        sys.exit(1)
