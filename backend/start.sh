#!/usr/bin/env bash
set -e

# Opcional: espera cortita a la DB (descomenta si lo necesitas)
# if command -v pg_isready >/dev/null 2>&1; then
#   echo "==> esperando a Postgres..."
#   pg_isready -h "${PGHOST}" -p "${PGPORT:-5432}" -U "${PGUSER}" -d "${PGDATABASE}" -t 5 || true
# fi

echo "==> migrate"
python manage.py migrate --noinput

# Si usas Whitenoise/STATIC_ROOT y ya hay vars listas:
# echo "==> collectstatic"
# python manage.py collectstatic --noinput || true

echo "==> createsuperuser (si no existe)"
python - <<'PY'
import os
from django.contrib.auth import get_user_model
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
get_wsgi_application()

User = get_user_model()
u = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
e = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
p = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "Admin123!")
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(username=u, email=e, password=p)
    print(f"   -> Superusuario creado: {u}")
else:
    print(f"   -> Superusuario ya existe: {u}")
PY

echo "==> gunicorn"
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 90
