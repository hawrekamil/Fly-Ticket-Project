#!/bin/sh
set -e

echo "=== BookingSoft Backend Starting ==="

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files for Django admin and Swagger UI
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo "Starting application server..."
exec "$@"
