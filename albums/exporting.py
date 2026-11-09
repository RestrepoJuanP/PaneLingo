"""Preparación asíncrona de exportaciones DOCX aprobadas (HU-27)."""

import io
import logging

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from docx import Document

from albums.models import AlbumExport, TextRegion

logger = logging.getLogger(__name__)

UNEXPECTED_ERROR_MESSAGE = "No se pudo preparar la exportación. Inténtalo de nuevo."


def build_export_snapshot(album):
    """Congela los metadatos y traducciones aprobadas del álbum."""
    regions = TextRegion.objects.filter(page__album=album).select_related("page")
    approved = []
    skipped_count = 0
    for region in regions.order_by("page__page_number", "reading_order"):
        if not region.needs_translation:
            continue
        if not region.is_translation_approved:
            skipped_count += 1
            continue
        approved.append(
            {
                "page_number": region.page.page_number,
                "reading_order": region.reading_order,
                "kind": region.get_kind_display(),
                "source_text": region.final_text,
                "translation": region.translation,
            }
        )
    snapshot = {
        "album_title": album.title,
        "source_language": album.source_language.name,
        "source_code": album.source_language.code.upper(),
        "target_language": album.target_language.name,
        "target_code": album.target_language.code.upper(),
        "regions": approved,
    }
    return snapshot, skipped_count


def build_export_document(snapshot):
    """Genera en memoria el DOCX estructurado de una instantánea aprobada."""
    document = Document()
    document.core_properties.title = snapshot["album_title"]
    document.core_properties.subject = "Traducciones aprobadas de PaneLingo"
    document.core_properties.author = "PaneLingo"

    document.add_heading(snapshot["album_title"], level=0)
    document.add_paragraph(
        f'{snapshot["source_language"]} ({snapshot["source_code"]}) → '
        f'{snapshot["target_language"]} ({snapshot["target_code"]})'
    )
    document.add_paragraph("Traducciones aprobadas exportadas desde PaneLingo.")

    current_page = None
    for region in snapshot["regions"]:
        if region["page_number"] != current_page:
            current_page = region["page_number"]
            document.add_heading(f"Página {current_page}", level=1)
        document.add_heading(
            f'Región {region["reading_order"]} · {region["kind"]}',
            level=2,
        )
        source = document.add_paragraph()
        source.add_run("Texto de origen: ").bold = True
        source.add_run(region["source_text"])
        translation = document.add_paragraph()
        translation.add_run("Traducción: ").bold = True
        translation.add_run(region["translation"])

    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def start_album_export(album):
    """Crea la instantánea y encola su DOCX; evita duplicar una preparación."""
    from albums.tasks import export_album_task

    preparing = album.exports.filter(status=AlbumExport.Status.PREPARING).first()
    if preparing:
        return preparing, False

    snapshot, skipped_count = build_export_snapshot(album)
    approved_count = len(snapshot["regions"])
    if not approved_count:
        return None, False

    export = AlbumExport.objects.create(
        album=album,
        snapshot=snapshot,
        approved_count=approved_count,
        skipped_count=skipped_count,
    )
    export_id = export.pk
    transaction.on_commit(lambda: export_album_task(export_id))
    return export, True


def mark_export_failed(export, message=UNEXPECTED_ERROR_MESSAGE):
    """Finaliza una exportación con error y un mensaje seguro para la interfaz."""
    export.status = AlbumExport.Status.FAILED
    export.error = message[:255]
    export.finished_at = timezone.now()
    export.save(update_fields=["status", "error", "finished_at"])


def run_album_export(export_id):
    """Construye y guarda el DOCX si la exportación sigue preparándose."""
    export = (
        AlbumExport.objects.select_related("album")
        .filter(pk=export_id, status=AlbumExport.Status.PREPARING)
        .first()
    )
    if export is None:
        return

    try:
        document_bytes = build_export_document(export.snapshot)
        export.file.save("export.docx", ContentFile(document_bytes), save=False)
        export.status = AlbumExport.Status.READY
        export.error = ""
        export.finished_at = timezone.now()
        export.save(update_fields=["file", "status", "error", "finished_at"])
    except Exception:
        logger.exception("Fallo inesperado al exportar el álbum %s.", export.album_id)
        mark_export_failed(export)
