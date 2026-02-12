web: python manage.py migrate --noinput && python manage.py collectstatic --noinput || true && gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 300
