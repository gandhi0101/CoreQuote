#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# Ubicamos la raíz del proyecto (backend/) para ejecutar los comandos
cd "$(dirname "$0")"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
