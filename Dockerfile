FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ENV DJANGO_SUPERUSER_USERNAME=admin \
    DJANGO_SUPERUSER_EMAIL=admin@example.com \
    DJANGO_SUPERUSER_PASSWORD=admin123


WORKDIR /app
# deps de sistema para psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# instala requirements primero (cache de capas)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# copia el código
COPY backend/ /app/
EXPOSE 8000
RUN python manage.py collectstatic --noinput || true
RUN python manage.py migrate --noinput || true
RUN python manage.py createsuperuser --noinput || true



# por defecto: dev server (claro y directo)
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# para producción, usar gunicorn (más robusto)
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 90"]


