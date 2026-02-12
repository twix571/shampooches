#!/usr/bin/env python
"""
Wait for the database to be ready before proceeding.
This script retries database connections until successful or timeout.
"""
import os
import sys
import time
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')
django.setup()

from django.db import connection
from django.core.management import call_command

def wait_for_db(max_retries=30, retry_interval=2):
    """Wait for database to be ready."""
    for attempt in range(max_retries):
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
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
        call_command('migrate', '--noinput')
        print("Migrations completed successfully")
        sys.exit(0)
    else:
        print("Database connection failed")
        sys.exit(1)
