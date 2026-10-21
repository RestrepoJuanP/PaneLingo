"""Revisión y edición de las traducciones de una página (HU-17 y HU-18).

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
