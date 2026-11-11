"""Preparación y descarga de exportaciones (HU-27, HU-28 y HU-90).

Dos formatos en el mismo flujo: el guion DOCX con las traducciones
aprobadas y las páginas traducidas como PNG en un ZIP. Ambos congelan una
instantánea al pedirse, se generan en Huey y se descargan por la misma vista
protegida. El PNG se dibuja con render_plan de albums/typesetting.py, el
único dibujante de la página (ADR-003).
"""

import io
import logging
import os
import tempfile
import zipfile

from django.core.files import File
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from docx import Document
from PIL import Image

from albums.imaging import export_mode
from albums.models import AlbumExport, ComicPage, TextRegion
from albums.typesetting import page_render_plan, render_plan

logger = logging.getLogger(__name__)

UNEXPECTED_ERROR_MESSAGE = "No se pudo preparar la exportación. Inténtalo de nuevo."


def export_download_name(export):
    """Construye un nombre seguro con álbum, idioma de destino y fecha."""
    album_name = slugify(export.album.title) or f"album-{export.album_id}"
    language_name = (
        slugify(export.album.target_language.name)
        or export.album.target_language.code.lower()
    )
    exported_at = export.finished_at or export.created_at
    local_date = timezone.localtime(exported_at).date().isoformat()
    if export.format == AlbumExport.Format.PNG_ZIP:
        return f"{album_name}_{language_name}_{local_date}_png.zip"
    return f"{album_name}_{language_name}_{local_date}.docx"


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


def start_album_export(album, export_format=AlbumExport.Format.DOCX):
    """Crea la instantánea y encola la exportación; evita duplicar una."""
    from albums.tasks import export_album_task

    preparing = album.exports.filter(status=AlbumExport.Status.PREPARING).first()
    if preparing:
        return preparing, False

    if export_format == AlbumExport.Format.PNG_ZIP:
        snapshot, skipped_count = build_png_snapshot(album)
        approved_count = sum(len(page["draw"]) for page in snapshot["pages"])
    else:
        snapshot, skipped_count = build_export_snapshot(album)
        approved_count = len(snapshot["regions"])
    if not approved_count:
        return None, False

    export = AlbumExport.objects.create(
        album=album,
        format=export_format,
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
        if export.is_png:
            save_png_archive(export)
        else:
            document_bytes = build_export_document(export.snapshot)
            export.file.save("export.docx", ContentFile(document_bytes), save=False)
        export.status = AlbumExport.Status.READY
        export.error = ""
        export.finished_at = timezone.now()
        export.save(update_fields=["file", "status", "error", "finished_at"])
    except Exception:
        logger.exception("Fallo inesperado al exportar el álbum %s.", export.album_id)
        mark_export_failed(export)


# --- Páginas traducidas en PNG (HU-90) ----------------------------------------


class ExportSourceChangedError(Exception):
    """Una imagen de la instantánea cambió o desapareció durante la tarea."""


def pluralized(count, singular, plural):
    """Elige la forma singular o plural de un aviso según el recuento."""
    return singular if count == 1 else plural.format(count=count)


def png_export_counts(album):
    """Recuentos para los avisos de la exportación PNG (CA-90.4).

    No cuentan como pendientes las páginas sin regiones que traducir: no
    tienen nada que maquetar. Una página sin imagen limpia se cuenta aparte,
    porque se exporta sin traducir.
    """
    counts = {"untypeset": 0, "uncleaned": 0, "manual": 0, "drawable": 0}
    pages = album.pages.prefetch_related("regions").order_by("page_number")
    for page in pages:
        regions = [region for region in page.regions.all() if region.needs_translation]
        if not regions:
            continue
        if not page.has_cleaned_image:
            counts["uncleaned"] += 1
            continue
        counts["untypeset"] += 0 if page.is_typeset else 1
        counts["manual"] += sum(
            region.cleaning_status == TextRegion.CleaningStatus.MANUAL
            for region in regions
        )
        counts["drawable"] += sum(
            region.is_translation_approved and bool(region.translation.strip())
            for region in regions
        )
    return counts


def png_export_warnings(counts):
    """Avisos que se muestran antes de confirmar la exportación PNG."""
    warnings = []
    if counts["untypeset"]:
        warnings.append(
            pluralized(
                counts["untypeset"],
                "1 página no está maquetada: se exportará con la maquetación "
                "que se ve en el editor.",
                "{count} páginas no están maquetadas: se exportarán con la "
                "maquetación que se ve en el editor.",
            )
            + " Las regiones sin traducción aprobada conservarán el texto "
            "original."
        )
    if counts["uncleaned"]:
        warnings.append(
            pluralized(
                counts["uncleaned"],
                "1 página no está limpia: se exportará sin traducir.",
                "{count} páginas no están limpias: se exportarán sin traducir.",
            )
            + " Límpiala en el espacio de trabajo para incluir sus traducciones."
        )
    if counts["manual"]:
        warnings.append(
            pluralized(
                counts["manual"],
                "1 región necesita limpieza manual: su texto original seguirá "
                "visible bajo la traducción.",
                "{count} regiones necesitan limpieza manual: su texto original "
                "seguirá visible bajo la traducción.",
            )
        )
    return warnings


def build_png_snapshot(album):
    """Congela, página a página, lo que la tarea va a dibujar (ADR-003, P5).

    Cada página guarda su número, los nombres en disco de la imagen
    original y de la limpia, y para cada región la maquetación de
    layout_for_region o la caja que conserva el original.
    """
    pages = list(album.pages.order_by("page_number"))
    skipped_count = sum(
        1
        for region in TextRegion.objects.filter(page__album=album)
        if region.needs_translation and not region.is_translation_approved
    )
    snapshot = {
        "album_title": album.title,
        "target_language": album.target_language.name,
        "pages": [page_render_plan(page) for page in pages],
    }
    return snapshot, skipped_count


def png_name(page_number):
    """Nombre de la página dentro del ZIP, con su número real (P3)."""
    return f"pagina-{page_number:03d}.png"


def check_page_source(plan):
    """Falla si la página o sus imágenes cambiaron tras la instantánea."""
    unchanged = ComicPage.objects.filter(
        pk=plan["page_id"],
        image=plan["image"],
        cleaned_image=plan["cleaned_image"],
    ).exists()
    if not unchanged:
        raise ExportSourceChangedError(plan["page_id"])


def output_mode(storage, name):
    """Modo del PNG según la imagen original: "L" en gris, "RGB" si no."""
    with storage.open(name, "rb") as image_file, Image.open(image_file) as source:
        return export_mode(source)


def page_png_bytes(plan, storage):
    """Dibuja una página congelada y la codifica como PNG sin alfa."""
    check_page_source(plan)
    try:
        mode = output_mode(storage, plan["image"])
        canvas = render_plan(plan, storage)
    except OSError as error:
        raise ExportSourceChangedError(plan["page_id"]) from error
    image = canvas.convert(mode) if mode != canvas.mode else canvas
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    image.close()
    canvas.close()
    return output.getvalue()


def write_png_archive(snapshot, path, storage):
    """Escribe el ZIP página a página, sin tener dos imágenes abiertas."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for plan in snapshot["pages"]:
            archive.writestr(
                png_name(plan["page_number"]), page_png_bytes(plan, storage)
            )


def save_png_archive(export):
    """Genera el ZIP en un temporal y solo lo guarda si todo salió bien.

    Si algo falla, la excepción llega a run_album_export, que deja la
    exportación en error con el mensaje de CA-90.6 y sin archivo; el
    temporal se borra siempre.
    """
    storage = ComicPage._meta.get_field("image").storage
    descriptor, path = tempfile.mkstemp(suffix=".zip")
    os.close(descriptor)
    try:
        write_png_archive(export.snapshot, path, storage)
        with open(path, "rb") as archive_file:
            export.file.save("export.zip", File(archive_file), save=False)
    finally:
        os.remove(path)
