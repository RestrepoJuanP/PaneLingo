"""Revisión, edición y aprobación de las traducciones (HU-17, HU-18 y HU-19).

La propuesta de la IA (machine_translation) no se toca al editar: se
conserva para consultarla (CA-18.1). Lo que cambia es el texto de trabajo
(translation), que es el que se aprueba en HU-19.
"""

from django.db import transaction
from django.utils import timezone

from albums.models import ComicPage, TextRegion

# Longitud máxima de una traducción. Un globo no se acerca ni de lejos; el
# límite solo impide guardar textos desmesurados por error.
MAX_TRANSLATION_LENGTH = 2000


def clean_translation(text):
    """Normaliza los saltos de línea y nada más (CA-18.3).

    Los signos ¿ ¡, los puntos suspensivos y los saltos de línea se guardan
    tal cual. Un texto que solo tiene espacios cuenta como vacío.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")[:MAX_TRANSLATION_LENGTH]
    return text if text.strip() else ""


def leave_page_approval(page):
    """Saca la página de "Aprobada" cuando una región deja de estarlo.

    Al editar una traducción aprobada hay que volver a aprobarla (CA-18.2),
    así que la página tampoco puede seguir aprobada (CA-19.4).
    """
    if page.status != ComicPage.Status.APPROVED:
        return
    pending = page.regions.filter(needs_review=True).exists()
    page.status = (
        ComicPage.Status.NEEDS_REVIEW if pending else ComicPage.Status.PROCESSED
    )
    page.save(update_fields=["status", "updated_at"])


def can_approve(region):
    """Indica si la región se puede aprobar (CA-19.3).

    Hace falta una traducción: una propuesta de la IA o una edición. Una
    edición vacía cuenta, porque es la decisión de dejarla sin traducir
    (ADR-002, T1); una región que nunca se tradujo, no.
    """
    return region.needs_translation and region.translation_status in (
        TextRegion.TranslationStatus.GENERATED,
        TextRegion.TranslationStatus.EDITED,
    )


def refresh_page_approval(page):
    """Pone la página en "Aprobada" si todas sus regiones lo están (CA-19.2).

    Cuentan las regiones con texto que traducir (ADR-002, T5). Si alguna
    deja de estar aprobada, la página sale de "Aprobada" (CA-19.4).
    """
    regions = [region for region in page.regions.all() if region.needs_translation]
    all_approved = bool(regions) and all(
        region.is_translation_approved for region in regions
    )
    if not all_approved:
        leave_page_approval(page)
        return
    if page.status != ComicPage.Status.APPROVED:
        page.status = ComicPage.Status.APPROVED
        page.save(update_fields=["status", "updated_at"])


def approve_translation(region):
    """Aprueba la traducción de la región con su fecha (CA-19.1)."""
    with transaction.atomic():
        region.translation_status = TextRegion.TranslationStatus.APPROVED
        region.approved_at = timezone.now()
        region.save(update_fields=["translation_status", "approved_at"])
        refresh_page_approval(region.page)


def unapprove_translation(region):
    """Retira la aprobación: la región vuelve a "Editada" (CA-19.4)."""
    with transaction.atomic():
        region.translation_status = TextRegion.TranslationStatus.EDITED
        region.approved_at = None
        region.save(update_fields=["translation_status", "approved_at"])
        refresh_page_approval(region.page)


def edit_translation(region, text):
    """Guarda la traducción editada por el usuario y la deja "Editada".

    Vale igual para una propuesta de la IA, para una región sin traducir en
    la que se escribe a mano y para una traducción aprobada, que vuelve a
    necesitar aprobación (CA-18.2). Una traducción vacía se acepta como
    "dejar sin traducir" (ADR-002, T1).
    """
    with transaction.atomic():
        region.translation = clean_translation(text)
        region.translation_status = TextRegion.TranslationStatus.EDITED
        region.translated_at = timezone.now()
        region.approved_at = None
        region.save(
            update_fields=[
                "translation",
                "translation_status",
                "translated_at",
                "approved_at",
            ]
        )
        leave_page_approval(region.page)
