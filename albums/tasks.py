"""Tareas en segundo plano de la app albums (Huey, ADR-001 y ADR-002).

El trabajador las descubre solo: "python manage.py run_huey" carga el módulo
tasks.py de cada aplicación instalada.
"""

from huey.contrib.djhuey import db_task

from albums.exporting import run_album_export
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


@db_task()
def export_album_task(export_id):
    """Prepara el DOCX de traducciones aprobadas de un álbum (HU-27)."""
    run_album_export(export_id)
