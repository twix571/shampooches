#!/bin/bash
set -e

# Force unbuffered output for Python
export PYTHONUNBUFFERED=1

echo "=== Starting Railway deployment ==="
echo "PID: $$"
echo "PORT environment variable: ${PORT:-NOT SET}"

# Create media directory
mkdir -p /data/media

# Set Django settings
export DJANGO_SETTINGS_MODULE=myproject.settings.production

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed"

# Start gunicorn
echo "Starting gunicorn on port ${PORT:-8080}..."
exec gunicorn myproject.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --timeout 300 \
    --workers 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
