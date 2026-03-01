#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

echo "Esperando a que la base de datos este lista en $POSTGRES_HOST:$POSTGRES_PORT..."

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

cd "$(dirname "$0")"

python manage.py migrate --noinput

echo "Verificando si el superusuario existe..."

DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-}"
DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-admin123}"

python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME}"
if username and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email="${DJANGO_SUPERUSER_EMAIL}",
        password="${DJANGO_SUPERUSER_PASSWORD}",
    )
    print("Superusuario creado.")
else:
    print("Superusuario ya existe o no se definio DJANGO_SUPERUSER_USERNAME.")
END

exec python manage.py runserver 0.0.0.0:8000
