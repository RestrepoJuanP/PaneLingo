"""Corrección manual del texto detectado (HU-15).

El texto que leyó el OCR (source_text) no se toca nunca: la corrección se
guarda aparte, para poder consultarlo y restaurarlo (CA-15.1 y CA-15.3).
"""

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from albums.models import ComicPage
from albums.ocr.review import text_needs_review

# Longitud máxima de una corrección. Un globo de cómic no se acerca ni de
# lejos; el límite solo impide guardar textos desmesurados por error.
MAX_CORRECTION_LENGTH = 2000

# Estados en los que el estado de la página depende de sus regiones. Una
# página aprobada (HU-19) o en proceso no se toca desde aquí.
REVIEWABLE_STATUSES = (ComicPage.Status.PROCESSED, ComicPage.Status.NEEDS_REVIEW)


def clean_correction(text):
    """Normaliza los saltos de línea y recorta el texto enviado."""
    return (
        text.replace("\r\n", "\n").replace("\r", "\n").strip()[:MAX_CORRECTION_LENGTH]
    )


def refresh_page_review_status(page):
    """Pone la página en "Necesita revisión" o "Procesada" según sus regiones."""
    if page.status not in REVIEWABLE_STATUSES:
        return
    pending = page.regions.filter(needs_review=True).exists()
    status = ComicPage.Status.NEEDS_REVIEW if pending else ComicPage.Status.PROCESSED
    if page.status != status:
        page.status = status
        page.save(update_fields=["status", "updated_at"])


def correct_region(region, text):
    """Guarda la corrección del usuario y da la región por revisada.

    Un texto vacío se acepta como "sin texto que traducir" (decisión del
    2026-10-20 sobre CA-15.5): la región no se borra.
    """
    with transaction.atomic():
        region.corrected_text = clean_correction(text)
        region.is_corrected = True
        region.corrected_at = timezone.now()
        region.needs_review = False
        region.save(
            update_fields=[
                "corrected_text",
                "is_corrected",
                "corrected_at",
                "needs_review",
            ]
        )
        refresh_page_review_status(region.page)


def restore_region(region):
    """Vuelve al texto del OCR y recalcula si la región necesita revisión."""
    with transaction.atomic():
        region.corrected_text = ""
        region.is_corrected = False
        region.corrected_at = None
        region.needs_review = text_needs_review(
            region.source_text,
            region.confidence,
            region.page.album.source_language.code,
            settings.OCR_REVIEW_THRESHOLD,
        )
        region.save(
            update_fields=[
                "corrected_text",
                "is_corrected",
                "corrected_at",
                "needs_review",
            ]
        )
        refresh_page_review_status(region.page)
