#!/bin/bash
set -e

echo "Starting Railway deployment..."

# Create media directory
mkdir -p /data/media

# Wait for PostgreSQL to be ready
echo "Waiting for database to be ready..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if python -c "import psycopg2; import os; psycopg2.connect(os.getenv('DATABASE_URL')); exit(0)" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "Database not ready (attempt $retry_count/$max_retries), retrying in 5 seconds..."
    sleep 5
done

if [ $retry_count -eq $max_retries ]; then
    echo "ERROR: Database failed to become available after $max_retries attempts"
    exit 1
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn myproject.wsgi:application --bind 0.0.0.0:8000 --timeout 300 --workers 2 --access-logfile -
