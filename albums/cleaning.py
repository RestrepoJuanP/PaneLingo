"""Limpieza determinista del texto original de una página (HU-88)."""

import io
import logging
from collections import Counter

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image

from albums.models import ComicPage, TextRegion

logger = logging.getLogger(__name__)

RING_WIDTH = 3
REGION_PADDING = 2
COLOR_TOLERANCE = 24
UNIFORM_RATIO = 0.85
UNEXPECTED_ERROR_MESSAGE = "No se pudo limpiar la página. Inténtalo de nuevo."
STALE_MESSAGE = "La limpieza tardó demasiado y se interrumpió."


def start_cleaning(page):
    """Marca la página como limpiándose y encola el trabajo con Huey."""
    from albums.tasks import clean_page_task

    if page.is_cleaning or not page.was_processed or not page.regions.exists():
        return False
    page.cleaning_state = ComicPage.CleaningState.CLEANING
    page.cleaning_started_at = timezone.now()
    page.cleaning_error = ""
    page.save(
        update_fields=[
            "cleaning_state",
            "cleaning_started_at",
            "cleaning_error",
        ]
    )
    page_id = page.pk
    transaction.on_commit(lambda: clean_page_task(page_id))
    return True


def expanded_box(region, image_size):
    """Amplía dos píxeles una región y la recorta a los límites de la imagen."""
    image_width, image_height = image_size
    return (
        max(0, region.x - REGION_PADDING),
        max(0, region.y - REGION_PADDING),
        min(image_width, region.x + region.width + REGION_PADDING),
        min(image_height, region.y + region.height + REGION_PADDING),
    )


def ring_boxes(box, image_size):
    """Devuelve las cuatro franjas de tres píxeles alrededor de una caja."""
    left, top, right, bottom = box
    image_width, image_height = image_size
    outer_left = max(0, left - RING_WIDTH)
    outer_top = max(0, top - RING_WIDTH)
    outer_right = min(image_width, right + RING_WIDTH)
    outer_bottom = min(image_height, bottom + RING_WIDTH)
    return (
        (outer_left, outer_top, outer_right, top),
        (outer_left, bottom, outer_right, outer_bottom),
        (outer_left, top, left, bottom),
        (right, top, outer_right, bottom),
    )


def sampled_ring_pixels(image, box):
    """Extrae los colores del anillo exterior, sin incluir la región."""
    pixels = []
    for left, top, right, bottom in ring_boxes(box, image.size):
        if right <= left or bottom <= top:
            continue
        pixels.extend(image.crop((left, top, right, bottom)).getdata())
    return pixels


def color_distance_squared(first, second):
    """Calcula la distancia RGB al cuadrado, evitando una raíz innecesaria."""
    return sum((first[channel] - second[channel]) ** 2 for channel in range(3))


def uniform_background(image, box):
    """Devuelve el color dominante si al menos el 85 % del anillo es similar."""
    pixels = sampled_ring_pixels(image, box)
    if not pixels:
        return None
    dominant, _count = Counter(pixels).most_common(1)[0]
    tolerance_squared = COLOR_TOLERANCE**2
    similar = sum(
        color_distance_squared(pixel, dominant) < tolerance_squared for pixel in pixels
    )
    if similar / len(pixels) < UNIFORM_RATIO:
        return None
    return dominant


def apply_region_cleaning(original, cleaned, region):
    """Limpia una región sobre la copia y devuelve su nuevo estado."""
    box = expanded_box(region, original.size)
    if region.skip_translation:
        cleaned.paste(original.crop(box), box[:2])
        return TextRegion.CleaningStatus.KEPT
    background = uniform_background(original, box)
    if background is None:
        return TextRegion.CleaningStatus.MANUAL
    cleaned.paste(background, box)
    return TextRegion.CleaningStatus.FILLED


def image_as_png(image):
    """Codifica una imagen RGB como PNG sin pérdida."""
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def replace_cleaned_image(page, image, statuses=None):
    """Guarda una nueva capa limpia y elimina la versión reemplazada."""
    old_name = page.cleaned_image.name if page.cleaned_image else ""
    storage = page.cleaned_image.storage
    page.cleaned_image.save(
        "cleaned.png",
        ContentFile(image_as_png(image)),
        save=False,
    )
    with transaction.atomic():
        page.cleaning_state = ComicPage.CleaningState.IDLE
        page.cleaning_started_at = None
        page.cleaning_error = ""
        page.save(
            update_fields=[
                "cleaned_image",
                "cleaning_state",
                "cleaning_started_at",
                "cleaning_error",
            ]
        )
        if statuses:
            regions = list(
                TextRegion.objects.select_for_update().filter(pk__in=statuses)
            )
            for region in regions:
                region.cleaning_status = statuses[region.pk]
            TextRegion.objects.bulk_update(regions, ["cleaning_status"])
    if old_name and old_name != page.cleaned_image.name:
        try:
            storage.delete(old_name)
        except OSError:
            logger.warning("No se pudo borrar la capa limpia anterior.", exc_info=True)


def build_cleaned_image(page):
    """Construye en memoria la capa limpia y los estados de sus regiones."""
    with page.image.open("rb") as image_file, Image.open(image_file) as source:
        original = source.convert("RGB")
    cleaned = original.copy()
    statuses = {}
    for region in page.regions.order_by("reading_order", "pk"):
        statuses[region.pk] = apply_region_cleaning(original, cleaned, region)
    return cleaned, statuses


def mark_cleaning_failed(page, message=UNEXPECTED_ERROR_MESSAGE):
    """Registra un fallo sin tocar la imagen original ni una capa previa."""
    page.cleaning_state = ComicPage.CleaningState.FAILED
    page.cleaning_started_at = None
    page.cleaning_error = message[:255]
    page.save(
        update_fields=[
            "cleaning_state",
            "cleaning_started_at",
            "cleaning_error",
        ]
    )


def expire_cleaning_if_stale(page):
    """Convierte una limpieza bloqueada por el trabajador en un fallo visible."""
    if page.is_cleaning_stale:
        mark_cleaning_failed(page, STALE_MESSAGE)


def run_page_cleaning(page_id):
    """Ejecuta la limpieza completa desde el trabajador de Huey."""
    page = (
        ComicPage.objects.select_related("album__owner")
        .filter(pk=page_id, cleaning_state=ComicPage.CleaningState.CLEANING)
        .first()
    )
    if page is None:
        return
    try:
        cleaned, statuses = build_cleaned_image(page)
        replace_cleaned_image(page, cleaned, statuses)
    except Exception:
        logger.exception("Fallo inesperado al limpiar la página %s.", page_id)
        mark_cleaning_failed(page)


def load_original_and_cleaned(page):
    """Abre como RGB la imagen original y la capa limpia existente."""
    with page.image.open("rb") as original_file, Image.open(original_file) as source:
        original = source.convert("RGB")
    with (
        page.cleaned_image.open("rb") as cleaned_file,
        Image.open(cleaned_file) as source,
    ):
        cleaned = source.convert("RGB")
    return original, cleaned


def clean_region_incrementally(region):
    """Actualiza solo una región de una capa limpia ya generada."""
    page = region.page
    if not page.cleaned_image:
        return
    original, cleaned = load_original_and_cleaned(page)
    status = apply_region_cleaning(original, cleaned, region)
    replace_cleaned_image(page, cleaned, {region.pk: status})
    region.cleaning_status = status


def restore_region_cleaning(region):
    """Copia de vuelta la zona original y deja la región sin limpiar."""
    page = region.page
    if not page.cleaned_image:
        region.cleaning_status = TextRegion.CleaningStatus.PENDING
        region.save(update_fields=["cleaning_status"])
        return
    original, cleaned = load_original_and_cleaned(page)
    box = expanded_box(region, original.size)
    cleaned.paste(original.crop(box), box[:2])
    replace_cleaned_image(
        page,
        cleaned,
        {region.pk: TextRegion.CleaningStatus.PENDING},
    )
    region.cleaning_status = TextRegion.CleaningStatus.PENDING
