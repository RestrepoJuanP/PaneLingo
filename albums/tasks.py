"""Tareas en segundo plano de la app albums (Huey, ADR-001 y ADR-002).

El trabajador las descubre solo: "python manage.py run_huey" carga el módulo
tasks.py de cada aplicación instalada.
"""

from huey.contrib.djhuey import db_task

from albums.processing import run_detection
from albums.translating import run_translation


@db_task()
def process_page_task(page_id):
    """Detecta las regiones de texto de una página (HU-12)."""
    run_detection(page_id)


@db_task()
def translate_page_task(page_id, region_id=None):
    """Traduce una página, o una de sus regiones, con IA (HU-16)."""
    run_translation(page_id, region_id)
