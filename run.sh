#!/bin/bash
set -e

# Force unbuffered output
export PYTHONUNBUFFERED=1

echo "=== Starting Railway deployment via run.sh ==="
echo "Process ID: $$"
echo "Working directory: $(pwd)"

# Set Django settings
export DJANGO_SETTINGS_MODULE=myproject.settings.production

# Create media directory
mkdir -p /data/media

# Wait for database
echo "Waiting for database..."
python -c "
import os
import time
import psycopg2

max_retries = 30
for i in range(max_retries):
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise Exception('DATABASE_URL not set')
        conn = psycopg2.connect(db_url)
        conn.close()
        print('Database is ready!')
        break
    except Exception as e:
        if i < max_retries - 1:
            print(f'Database not ready, retrying... ({i+1}/{max_retries})')
            time.sleep(2)
        else:
            print(f'Failed to connect to database after {max_retries} attempts')
            exit(1)
"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed"

# Start gunicorn
echo "Starting gunicorn on port ${PORT:-8080}..."
echo "PORT variable: ${PORT:-NOT SET}"

gunicorn myproject.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --timeout 300 \
    --workers 1 \
    --threads 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
