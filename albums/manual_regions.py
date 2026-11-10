"""Creación de regiones dibujadas por el traductor (HU-85)."""

import io

from django.conf import settings
from django.db import transaction
from django.db.models import F
from PIL import Image

from albums.models import ComicPage, TextRegion
from albums.ocr import get_provider
from albums.ocr.base import DetectedRegion
from albums.ocr.layout import (
    arrange_regions,
    is_balloon,
    is_right_to_left,
    sort_in_reading_order,
)
from albums.ocr.review import text_needs_review
from albums.processing import read_image_bytes

# Azure Read exige imágenes de al menos 50 px por lado. El proveedor simulado
# también recibe este recorte para que desarrollo y producción sigan el mismo
# flujo, aunque sus resultados no dependan de ese mínimo.
OCR_MIN_CROP_SIZE = 50
TEMPORARY_ORDER_OFFSET = 1_000_000


def crop_bytes(image, box):
    """Recorta la caja y la amplía sobre blanco si el OCR exige más tamaño."""
    crop = image.crop((box.x, box.y, box.right, box.bottom)).convert("RGB")
    canvas_width = max(crop.width, OCR_MIN_CROP_SIZE)
    canvas_height = max(crop.height, OCR_MIN_CROP_SIZE)
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    canvas.paste(crop, (0, 0))
    output = io.BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue(), canvas.size


def recognized_text(detected, crop_size, language_code):
    """Une el texto del recorte en el orden de lectura y promedia su confianza."""
    ordered = arrange_regions(detected, *crop_size, language_code)
    text = "\n".join(region.text.strip() for region in ordered if region.text.strip())
    confidences = [
        region.confidence for region in ordered if region.confidence is not None
    ]
    confidence = sum(confidences) / len(confidences) if confidences else None
    return text, confidence


def detect_manual_region(page, x, y, width, height):
    """Ejecuta OCR sobre la caja elegida y construye una región sin guardar."""
    image_bytes = read_image_bytes(page)
    box = DetectedRegion(x=x, y=y, width=width, height=height)
    language_code = page.album.source_language.code
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.load()
        detected_kind = (
            TextRegion.Kind.BALLOON
            if is_balloon(image, box)
            else TextRegion.Kind.NARRATION
        )
        prepared, crop_size = crop_bytes(image, box)

    detected = get_provider().detect(prepared)
    text, confidence = recognized_text(detected, crop_size, language_code)
    return TextRegion(
        page=page,
        reading_order=1,
        kind=detected_kind,
        x=x,
        y=y,
        width=width,
        height=height,
        source_text=text,
        confidence=confidence,
        needs_review=text_needs_review(
            text,
            confidence,
            language_code,
            settings.OCR_REVIEW_THRESHOLD,
        ),
        is_manual=True,
    )


def ordered_regions(existing, new_region, language_code):
    """Devuelve regiones existentes y nueva en el orden visual de lectura."""
    entries = []
    for region in [*existing, new_region]:
        box = DetectedRegion(
            x=region.x,
            y=region.y,
            width=region.width,
            height=region.height,
        )
        entries.append((box, region))
    by_box = {id(box): region for box, region in entries}
    boxes = sort_in_reading_order(
        [box for box, _region in entries],
        is_right_to_left(language_code),
    )
    return [by_box[id(box)] for box in boxes]


def save_manual_region(page, new_region):
    """Guarda la región y renumera todas sin violar el índice único."""
    with transaction.atomic():
        locked_page = ComicPage.objects.select_for_update().get(pk=page.pk)
        existing = list(
            TextRegion.objects.select_for_update()
            .filter(page=locked_page)
            .order_by("reading_order")
        )
        ordered = ordered_regions(
            existing,
            new_region,
            locked_page.album.source_language.code,
        )
        locked_page.regions.update(
            reading_order=F("reading_order") + TEMPORARY_ORDER_OFFSET
        )
        new_region.page = locked_page
        locked_page.clear_typeset_approval()
        for position, region in enumerate(ordered, start=1):
            region.reading_order = position
            if region.pk is None:
                region.save()
            else:
                region.save(update_fields=["reading_order"])

        if locked_page.status == ComicPage.Status.APPROVED:
            has_review_work = locked_page.regions.filter(
                needs_review=True,
                skip_translation=False,
            ).exists()
            locked_page.status = (
                ComicPage.Status.NEEDS_REVIEW
                if has_review_work
                else ComicPage.Status.PROCESSED
            )
            locked_page.save(update_fields=["status", "updated_at"])
    return new_region


def add_manual_region(page, x, y, width, height):
    """Detecta, guarda y devuelve una región añadida manualmente."""
    from albums.cleaning import clean_region_incrementally

    region = detect_manual_region(page, x, y, width, height)
    saved = save_manual_region(page, region)
    clean_region_incrementally(saved)
    return saved
