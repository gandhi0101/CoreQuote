FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# deps de sistema (psycopg2 / libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# instala requirements primero (cache de capas)
# OJO: si tu requirements.txt está en la raíz, copia desde ahí;
# si está en backend/, déjalo como estaba:
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# copia el código del backend (manage.py, config/, apps, start.sh, etc.)
COPY backend/ /app/

# (quitar esto: ahora lo hace start.sh)
# RUN python manage.py collectstatic --noinput || true

# permisos al script
RUN chmod +x /app/start.sh

# puerto de Railway
ENV PORT=8000
EXPOSE 8000

# usa el script combinado
CMD ["bash", "-lc", "/app/start.sh"]
