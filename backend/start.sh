#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# Esperamos a que la base de datos esté disponible
echo "Esperando a que la base de datos esté lista en $POSTGRES_HOST:$POSTGRES_PORT..."

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "Base de datos disponible. Ejecutando migraciones y colecta de estáticos..."

# Ubicamos la raíz del proyecto (backend/) para ejecutar los comandos
cd "$(dirname "$0")"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Crear superusuario si no existe
echo "Verificando si el superusuario existe..."

python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="${DJANGO_SUPERUSER_USERNAME}").exists():
    User.objects.create_superuser(
        username="${DJANGO_SUPERUSER_USERNAME}",
        email="${DJANGO_SUPERUSER_EMAIL}",
        password="${DJANGO_SUPERUSER_PASSWORD}"
    )
    print("Superusuario creado.")
else:
    print("Superusuario ya existe.")
END


exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
