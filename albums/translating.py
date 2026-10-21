"""Servicio de traducción asistida por IA de una página (HU-16, ADR-002).

Sigue el mismo patrón que el OCR (albums/processing.py): start_translation
corre dentro de la petición web, marca la página y encola la tarea;
run_translation corre en el trabajador de Huey, llama al proveedor y guarda
el resultado.
"""

import logging

from django.db import transaction
from django.utils import timezone

from albums.models import ComicPage, TextRegion
from albums.translation import TranslationError, get_translator
from albums.translation.context import build_page_request

logger = logging.getLogger(__name__)

UNEXPECTED_ERROR_MESSAGE = "No se pudo traducir la página por un error inesperado."
STALE_MESSAGE = "La traducción tardó demasiado y se interrumpió."


def translatable_regions(page):
    """Regiones de la página que tienen texto que traducir (ADR-002, T5)."""
    return [region for region in page.regions.all() if region.needs_translation]


def can_translate(page):
    """Indica si la página tiene algo que traducir (CA-16.5).

    Hace falta que el OCR haya terminado y que alguna región tenga texto sin
    aprobar: traducir una página con todo aprobado no cambiaría nada.
    """
    if not page.was_processed or page.is_processing:
        return False
    return any(
        not region.is_translation_approved for region in translatable_regions(page)
    )


def start_translation(page, region=None):
    """Pone la página en "Traduciendo" y encola su traducción.

    Con region, solo se vuelve a traducir esa región (el "Reintentar con IA"
    del mockup), aunque viaja la página entera como contexto. Devuelve False,
    sin encolar nada, si la página ya se está traduciendo.
    """
    # Import local: albums.tasks importa este módulo para ejecutar la tarea.
    from albums.tasks import translate_page_task

    if page.is_translating:
        return False
    page.translation_state = ComicPage.TranslationState.TRANSLATING
    page.translation_started_at = timezone.now()
    page.translation_error = ""
    page.save(
        update_fields=[
            "translation_state",
            "translation_started_at",
            "translation_error",
        ]
    )
    page_id = page.pk
    region_id = region.pk if region else None
    transaction.on_commit(lambda: translate_page_task(page_id, region_id))
    return True


def finish_translation(page, error=""):
    """Saca la página de "Traduciendo", con o sin error."""
    page.translation_state = (
        ComicPage.TranslationState.FAILED if error else ComicPage.TranslationState.IDLE
    )
    page.translation_started_at = None
    page.translation_error = error[:255]
    page.save(
        update_fields=[
            "translation_state",
            "translation_started_at",
            "translation_error",
        ]
    )


def expire_translation_if_stale(page):
    """Pasa a error una página que lleva demasiado tiempo "Traduciendo"."""
    if page.is_translation_stale:
        finish_translation(page, STALE_MESSAGE)


def apply_translations(page, regions, translations):
    """Guarda las propuestas de la IA en sus regiones (CA-16.1).

    Cada propuesta queda "Generada", también como texto de trabajo. Las
    regiones aprobadas no se tocan aunque la respuesta las traiga (CA-16.3).
    """
    by_number = {region.reading_order: region for region in regions}
    now = timezone.now()
    changed = []
    for item in translations:
        region = by_number.get(item.number)
        if region is None or region.is_translation_approved:
            continue
        region.machine_translation = item.translation
        region.translation = item.translation
        region.translation_status = TextRegion.TranslationStatus.GENERATED
        region.translated_at = now
        changed.append(region)
    with transaction.atomic():
        TextRegion.objects.bulk_update(
            changed,
            [
                "machine_translation",
                "translation",
                "translation_status",
                "translated_at",
            ],
        )
        finish_translation(page)
    return len(changed)


def run_translation(page_id, region_id=None):
    """Traduce una página, o una de sus regiones, y guarda el resultado.

    Corre en el trabajador. Si la página se borró o dejó de estar
    "Traduciendo" mientras esperaba en la cola, no hace nada. Si el proveedor
    falla, las traducciones que ya existían no se pierden (CA-16.4).
    """
    page = (
        ComicPage.objects.select_related(
            "album__source_language", "album__target_language"
        )
        .filter(pk=page_id, translation_state=ComicPage.TranslationState.TRANSLATING)
        .first()
    )
    if page is None:
        return

    try:
        regions = list(page.regions.all())
        request = build_page_request(page, regions, only_region_id=region_id)
        translations = (
            get_translator().translate(request) if request.numbers_to_translate else []
        )
    except TranslationError as error:
        finish_translation(page, str(error))
        return
    except Exception:
        # Frontera del trabajador: ningún fallo puede dejar la página
        # bloqueada en "Traduciendo". Se registra con su traza.
        logger.exception("Fallo inesperado al traducir la página %s.", page_id)
        finish_translation(page, UNEXPECTED_ERROR_MESSAGE)
        return

    apply_translations(page, regions, translations)
