#!/usr/bin/env python
"""
Wait for the database to be ready before proceeding.
This script retries database connections until successful or timeout.
"""
import os
import sys
import time
import psycopg2

def wait_for_db(max_retries=60, retry_interval=2):
    """Wait for database to be ready using direct PostgreSQL connection."""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        return False
    
    for attempt in range(max_retries):
        try:
            # Test database connection directly with psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print(f"Database is ready after {attempt + 1} attempt(s)")
            return True
        except Exception as e:
            print(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
    print(f"Failed to connect to database after {max_retries} attempts")
    return False

if __name__ == '__main__':
    if wait_for_db():
        print("Running migrations...")
        # Set up Django settings AFTER database is ready
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
        
        import django
        django.setup()
        
        from django.core.management import call_command
        call_command('migrate', '--noinput')
        print("Migrations completed successfully")
        sys.exit(0)
    else:
        print("Database connection failed")
        sys.exit(1)
