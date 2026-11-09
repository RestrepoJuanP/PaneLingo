"""Gestión reversible y exclusión de regiones de texto (HU-86)."""

import hashlib
import json

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime

from albums.models import ComicPage, TextRegion
from albums.translation_review import refresh_page_approval

DELETED_REGION_SESSION_KEY = "deleted_text_region"
TEMPORARY_ORDER_OFFSET = 1_000_000
REGION_VALUE_FIELDS = (
    "kind",
    "x",
    "y",
    "width",
    "height",
    "source_text",
    "confidence",
    "needs_review",
    "is_manual",
    "skip_translation",
    "corrected_text",
    "is_corrected",
    "machine_translation",
    "translation",
    "translation_status",
)
REGION_DATE_FIELDS = (
    "corrected_at",
    "translated_at",
    "approved_at",
    "created_at",
)


def serialize_region(region):
    """Convierte una región completa en datos seguros para la sesión."""
    values = {field: getattr(region, field) for field in REGION_VALUE_FIELDS}
    values.update(
        {
            field: value.isoformat() if (value := getattr(region, field)) else None
            for field in REGION_DATE_FIELDS
        }
    )
    return {
        "original_pk": region.pk,
        "page_id": region.page_id,
        "reading_order": region.reading_order,
        "values": values,
    }


def page_signature(page):
    """Resume el estado de la página para invalidar un deshacer obsoleto."""
    page.refresh_from_db(fields=["status", "translation_state", "updated_at"])
    regions = [
        serialize_region(region)
        for region in page.regions.order_by("reading_order", "pk")
    ]
    state = {
        "status": page.status,
        "translation_state": page.translation_state,
        "updated_at": page.updated_at.isoformat(),
        "regions": regions,
    }
    payload = json.dumps(
        state, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def renumber_regions(page):
    """Asigna un orden consecutivo sin violar la restricción única."""
    regions = list(
        TextRegion.objects.select_for_update()
        .filter(page=page)
        .order_by("reading_order", "pk")
    )
    TextRegion.objects.filter(page=page).update(
        reading_order=F("reading_order") + TEMPORARY_ORDER_OFFSET
    )
    for position, region in enumerate(regions, start=1):
        region.reading_order = position
        region.save(update_fields=["reading_order"])


def delete_region(request, region):
    """Elimina, renumera y guarda una instantánea restaurable en sesión."""
    with transaction.atomic():
        page = ComicPage.objects.select_for_update().get(pk=region.page_id)
        locked_region = TextRegion.objects.select_for_update().get(pk=region.pk)
        snapshot = serialize_region(locked_region)
        locked_region.delete()
        renumber_regions(page)
        refresh_page_approval(page)

    snapshot["page_signature"] = page_signature(page)
    request.session[DELETED_REGION_SESSION_KEY] = snapshot
    return page, snapshot


def restored_values(snapshot):
    """Convierte fechas ISO de la sesión en valores aceptados por el modelo."""
    values = dict(snapshot["values"])
    for field in REGION_DATE_FIELDS:
        values[field] = parse_datetime(values[field]) if values[field] else None
    return values


def insert_restored_region(page, snapshot):
    """Recrea la región en su posición y desplaza las siguientes."""
    existing = list(
        TextRegion.objects.select_for_update()
        .filter(page=page)
        .order_by("reading_order", "pk")
    )
    TextRegion.objects.filter(page=page).update(
        reading_order=F("reading_order") + TEMPORARY_ORDER_OFFSET
    )
    position = min(max(snapshot["reading_order"], 1), len(existing) + 1)
    values = restored_values(snapshot)
    created_at = values.pop("created_at")
    restored = TextRegion.objects.create(
        pk=snapshot["original_pk"],
        page=page,
        reading_order=position,
        **values,
    )
    if created_at:
        TextRegion.objects.filter(pk=restored.pk).update(created_at=created_at)
        restored.created_at = created_at

    ordered = existing[: position - 1] + [restored] + existing[position - 1 :]
    for reading_order, region in enumerate(ordered, start=1):
        if region.pk == restored.pk:
            continue
        region.reading_order = reading_order
        region.save(update_fields=["reading_order"])
    return restored


def restore_deleted_region(request, deleted_pk, user):
    """Restaura la última región eliminada si la página no cambió después."""
    snapshot = request.session.get(DELETED_REGION_SESSION_KEY)
    if not snapshot or snapshot.get("original_pk") != deleted_pk:
        return None, None

    page = get_object_or_404(
        ComicPage.objects.select_related("album"),
        pk=snapshot["page_id"],
        album__owner=user,
    )
    with transaction.atomic():
        page = ComicPage.objects.select_for_update().get(pk=page.pk)
        if snapshot.get("page_signature") != page_signature(page):
            request.session.pop(DELETED_REGION_SESSION_KEY, None)
            return page, None
        restored = insert_restored_region(page, snapshot)
        refresh_page_approval(page)
    request.session.pop(DELETED_REGION_SESSION_KEY, None)
    return page, restored


def set_translation_skipped(region, is_skipped):
    """Alterna «No traducir» y deja la región sin traducción previa."""
    with transaction.atomic():
        region.skip_translation = is_skipped
        region.machine_translation = ""
        region.translation = ""
        region.translation_status = TextRegion.TranslationStatus.UNTRANSLATED
        region.translated_at = None
        region.approved_at = None
        region.save(
            update_fields=[
                "skip_translation",
                "machine_translation",
                "translation",
                "translation_status",
                "translated_at",
                "approved_at",
            ]
        )
        refresh_page_approval(region.page)
