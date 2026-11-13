# Imagen de PaneLingo para producción: Django servido por Gunicorn.
# El mismo contenedor sirve como trabajador de Huey cambiando el comando.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_DATA_DIR=/data \
    DJANGO_MEDIA_ROOT=/data/media

WORKDIR /app

COPY requirements.txt requirements-prod.txt ./
RUN pip install -r requirements-prod.txt

COPY . .

# collectstatic necesita una SECRET_KEY para importar la configuración; esta
# solo existe durante la construcción y nunca llega al contenedor en marcha.
# La cola de Huey abre su archivo SQLite al importar la configuración, así que
# /data debe existir antes; el archivo de construcción se borra al final.
RUN mkdir -p /data/media /srv/static \
    && DJANGO_SECRET_KEY=solo-para-collectstatic python manage.py collectstatic --noinput \
    && rm -f /data/huey.sqlite3* \
    && useradd --create-home --uid 1000 panelingo \
    && chown -R panelingo:panelingo /data /srv/static /app/staticfiles \
    && chmod +x deploy/entrypoint.sh

USER panelingo

EXPOSE 8000
VOLUME ["/data"]

ENTRYPOINT ["deploy/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", \
     "--workers", "3", "--timeout", "120", "--access-logfile", "-"]
