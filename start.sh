#!/bin/bash
set -e

echo "Starting Railway deployment..."

# Create media directory
mkdir -p /data/media

# Wait for PostgreSQL to be ready
echo "Waiting for database to be ready..."
echo "DATABASE_URL is set: $([ -n "$DATABASE_URL" ] && echo "Yes" || echo "No")"
max_retries=60
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    echo "Attempting database connection (attempt $((retry_count + 1))/$max_retries)..."
    if python -c "import psycopg2; import os; import sys; db_url = os.getenv('DATABASE_URL'); print(f'DB URL: {db_url[:20]}...' if db_url else 'No DB URL'); conn = psycopg2.connect(db_url); print('Connected!'); conn.close(); sys.exit(0)" 2>&1; then
        echo "Database is ready!"
        break
    fi
    retry_count=$((retry_count + 1))
    echo "Database not ready, retrying in 5 seconds..."
    sleep 5
done

if [ $retry_count -eq $max_retries ]; then
    echo "ERROR: Database failed to become available after $max_retries attempts (300 seconds)"
    echo "Please check if PostgreSQL service is running in Railway"
    exit 1
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Start gunicorn
echo "Starting gunicorn..."
# Use PORT environment variable if set (Railway sets this), default to 8000
PORT=${PORT:-8000}
echo "Binding to port: $PORT"
exec gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT --timeout 300 --workers 2 --access-logfile -
