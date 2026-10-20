"""Servicio de procesamiento de páginas: regiones de texto y OCR (HU-12, HU-13).

El flujo tiene dos mitades. start_processing corre dentro de la petición web:
marca la página y encola la tarea. run_detection corre en el trabajador de
Huey: llama al proveedor y guarda el resultado. Ver ADR-001.
"""

import io
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from PIL import Image

from albums.models import ComicPage, TextRegion
from albums.ocr import OcrProviderError, get_provider
from albums.ocr.layout import arrange_regions, is_balloon
from albums.ocr.review import needs_review

logger = logging.getLogger(__name__)

UNEXPECTED_ERROR_MESSAGE = "No se pudo procesar la página por un error inesperado."
STALE_MESSAGE = "El procesamiento tardó demasiado y se interrumpió."


def start_processing(page):
    """Pone la página en "Procesando" y encola su detección.

    Devuelve False, sin encolar nada, si la página ya se está procesando: dos
    pulsaciones seguidas no deben lanzar dos detecciones.

    La tarea se encola con on_commit para que el trabajador no lea la página
    antes de que se haya guardado el cambio de estado.
    """
    # Import local: albums.tasks importa este módulo para ejecutar la tarea.
    from albums.tasks import process_page_task

    if page.is_processing:
        return False
    page.status = ComicPage.Status.PROCESSING
    page.processing_started_at = timezone.now()
    page.processing_error = ""
    page.save(update_fields=["status", "processing_started_at", "processing_error"])
    page_id = page.pk
    transaction.on_commit(lambda: process_page_task(page_id))
    return True


def read_image_bytes(page):
    """Lee del almacenamiento la imagen original de la página."""
    with page.image.open("rb") as image_file:
        return image_file.read()


def build_regions(page, image_bytes, detected):
    """Convierte lo que devolvió el proveedor en regiones listas para guardar.

    Recorta las cajas a la página, agrupa las líneas en globos y las ordena
    según el idioma de origen del álbum (HU-12). Cada región guarda además su
    texto y su confianza, y se marca para revisión si no se puede confiar en
    lo leído (HU-13).
    """
    language_code = page.album.source_language.code
    ordered = arrange_regions(detected, page.width, page.height, language_code)
    threshold = settings.OCR_REVIEW_THRESHOLD

    with Image.open(io.BytesIO(image_bytes)) as image:
        return [
            TextRegion(
                page=page,
                reading_order=position,
                kind=(
                    TextRegion.Kind.BALLOON
                    if is_balloon(image, region)
                    else TextRegion.Kind.NARRATION
                ),
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
                source_text=region.text,
                confidence=region.confidence,
                needs_review=needs_review(region, language_code, threshold),
            )
            for position, region in enumerate(ordered, start=1)
        ]


def save_regions(page, regions):
    """Reemplaza las regiones de la página y actualiza su estado.

    La página queda "Necesita revisión" si alguna región lo necesita
    (CA-13.3) y "Procesada" en caso contrario. El borrado y la inserción van
    en la misma transacción: si algo falla al guardar, la página conserva sus
    regiones anteriores (CA-12.4).
    """
    has_doubtful_regions = any(region.needs_review for region in regions)
    with transaction.atomic():
        page.regions.all().delete()
        TextRegion.objects.bulk_create(regions)
        page.status = (
            ComicPage.Status.NEEDS_REVIEW
            if has_doubtful_regions
            else ComicPage.Status.PROCESSED
        )
        page.processing_started_at = None
        page.processing_error = ""
        page.save(update_fields=["status", "processing_started_at", "processing_error"])


def mark_failed(page, message):
    """Pasa la página a "Error" y guarda el motivo del fallo.

    Las regiones que ya tuviera no se tocan (CA-12.4): siguen visibles junto
    al error y se reemplazan solo si un reintento termina bien.
    """
    page.status = ComicPage.Status.FAILED
    page.processing_started_at = None
    page.processing_error = message[:255]
    page.save(update_fields=["status", "processing_started_at", "processing_error"])


def expire_if_stale(page):
    """Pasa a "Error" una página que lleva demasiado tiempo "Procesando".

    Cubre la caída del trabajador a mitad de una tarea: nadie más la sacaría
    de PROCESSING. Se comprueba al consultar la página, que es justo cuando
    importa, en lugar de con una tarea periódica que habría que mantener.
    Si el trabajador termina después, run_detection ya no la toca, porque
    solo procesa páginas que siguen en PROCESSING.
    """
    if page.is_processing_stale:
        mark_failed(page, STALE_MESSAGE)


def run_detection(page_id):
    """Detecta las regiones de texto de una página y guarda el resultado.

    Corre en el trabajador. Si la página se borró o dejó de estar en
    "Procesando" mientras esperaba en la cola, no hace nada.
    """
    page = (
        ComicPage.objects.select_related("album__source_language")
        .filter(pk=page_id, status=ComicPage.Status.PROCESSING)
        .first()
    )
    if page is None:
        return

    try:
        image_bytes = read_image_bytes(page)
        detected = get_provider().detect(image_bytes)
        regions = build_regions(page, image_bytes, detected)
    except OcrProviderError as error:
        mark_failed(page, str(error))
        return
    except Exception:
        # Frontera del trabajador: cualquier otro fallo (un archivo que ya no
        # está, una imagen corrupta, un error de programación) no puede dejar
        # la página bloqueada en "Procesando". Se registra con su traza y se
        # ofrece reintentar.
        logger.exception("Fallo inesperado al procesar la página %s.", page_id)
        mark_failed(page, UNEXPECTED_ERROR_MESSAGE)
        return

    save_regions(page, regions)
