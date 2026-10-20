"""Tareas en segundo plano de la app albums (Huey, ADR-001).

El trabajador las descubre solo: "python manage.py run_huey" carga el módulo
tasks.py de cada aplicación instalada.
"""

from huey.contrib.djhuey import db_task

from albums.processing import run_detection


@db_task()
def process_page_task(page_id):
    """Detecta las regiones de texto de una página (HU-12)."""
    run_detection(page_id)
