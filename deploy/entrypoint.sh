#!/bin/sh
# Punto de entrada del contenedor de PaneLingo.
# Solo el servicio web aplica las migraciones (RUN_MIGRATIONS=1), para que el
# trabajador de Huey no compita por la base al arrancar a la vez.
set -e

mkdir -p "${DJANGO_MEDIA_ROOT:-/data/media}"

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    python manage.py migrate --noinput
    # Copia los estáticos al volumen compartido con Caddy.
    if [ -d /srv/static ]; then
        cp -r /app/staticfiles/. /srv/static/
    fi
fi

exec "$@"
