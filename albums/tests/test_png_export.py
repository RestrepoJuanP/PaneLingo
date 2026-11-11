"""Pruebas de la exportación de páginas traducidas como PNG (HU-90)."""

import io
import os
import tempfile
import zipfile
from unittest import mock

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image, ImageChops

from albums.cleaning import build_cleaned_image, replace_cleaned_image
from albums.exporting import UNEXPECTED_ERROR_MESSAGE
from albums.models import AlbumExport, ComicPage, TextRegion
from albums.services import create_pages_from_upload
from albums.tests.test_typesetting_editor import (
    INK,
    PAGE_SIZE,
    WHITE,
    TypesettingTestCase,
    png_bytes,
)
from albums.typesetting import render_page, render_plan

QUARTER_GRAY_16 = 16384
QUARTER_GRAY_8 = 63


class PngExportTestCase(TypesettingTestCase):
    """Base: un álbum cuya página 1 está limpia y con traducciones aprobadas."""

    def start_png(self, confirm=True, execute=True):
        """Pide la exportación PNG y ejecuta la tarea encolada."""
        data = {"format": "png_zip"}
        if confirm:
            data["confirm_png"] = "1"
        with self.captureOnCommitCallbacks(execute=execute) as callbacks:
            response = self.client.post(self.album.get_export_url(), data)
        self.callbacks = callbacks
        return response

    def latest_export(self):
        """Última exportación del álbum, recién leída."""
        return AlbumExport.objects.filter(album=self.album).latest("created_at")

    def archive(self, export):
        """Abre el ZIP de una exportación y devuelve {nombre: imagen}."""
        with export.file.open("rb") as handle:
            content = handle.read()
        images = {}
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for name in archive.namelist():
                with Image.open(io.BytesIO(archive.read(name))) as image:
                    image.load()
                    images[name] = image.copy()
        return images

    def replace_original(self, page, image):
        """Sustituye la imagen original de la página por la indicada."""
        content = png_bytes(image)
        with page.image.open("wb") as image_file:
            image_file.write(content)
        page.width, page.height = image.size
        page.file_size = len(content)
        page.save(update_fields=["width", "height", "file_size"])

    def export_page_image(self):
        """Exporta el álbum y devuelve la imagen de la página 1."""
        self.start_png()
        return self.archive(self.latest_export())["pagina-001.png"]


class FormatChoiceTests(PngExportTestCase):
    """CP-90.1 — El diálogo ofrece DOCX y PNG; el DOCX funciona igual."""

    def test_the_dialog_offers_both_formats_as_native_radios(self):
        """CP-90.1 — Dos radios nativos con los nombres del criterio."""
        response = self.client.get(self.album.get_export_url())
        self.assertContains(response, 'type="radio"', count=2)
        self.assertContains(response, 'value="docx"')
        self.assertContains(response, 'value="png_zip"')
        self.assertContains(response, "Documento de texto (DOCX)")
        self.assertContains(response, "Páginas traducidas (PNG en un ZIP)")

    def test_docx_still_works_the_same(self):
        """CP-90.1 — El DOCX se sigue generando como antes."""
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                self.album.get_export_url(), {"format": "docx", "confirm": "1"}
            )
        export = self.latest_export()
        self.assertEqual(export.format, AlbumExport.Format.DOCX)
        self.assertEqual(export.status, AlbumExport.Status.READY)
        self.assertTrue(export.file.name.endswith(".docx"))

    def test_png_needs_something_to_draw(self):
        """Sin traducciones aprobadas en una página limpia no hay PNG."""
        ComicPage.objects.filter(pk=self.page.pk).update(cleaned_image="")
        response = self.client.get(self.album.get_export_url())
        self.assertRegex(response.content.decode(), r'value="png_zip"[^>]*\sdisabled')
        self.assertContains(response, "Aprueba al menos una traducción en una página")
        response = self.start_png()
        self.assertFalse(AlbumExport.objects.filter(album=self.album).exists())
        followed = self.client.get(response.url)
        self.assertContains(followed, "Aprueba al menos una traducción en una página")

    def test_history_shows_the_format_of_each_export(self):
        """El historial muestra el formato de cada exportación."""
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                self.album.get_export_url(), {"format": "docx", "confirm": "1"}
            )
        self.start_png()
        response = self.client.get(self.album.get_export_url())
        self.assertContains(response, "· DOCX")
        self.assertContains(response, "· PNG en ZIP")
        self.assertContains(response, "1 página")


class ArchiveContentTests(PngExportTestCase):
    """CP-90.2 — ZIP con el nombre correcto y las páginas en orden."""

    def test_zip_name_type_and_page_order_with_a_gap(self):
        """CP-90.2 — Páginas 1, 2 y 4: pagina-001, 002 y 004 en ese orden."""
        self.make_page(self.album)
        third = self.make_page(self.album)
        self.make_page(self.album)
        third.delete()
        self.start_png()
        export = self.latest_export()
        self.assertEqual(export.status, AlbumExport.Status.READY)
        with export.file.open("rb") as handle:
            names = zipfile.ZipFile(io.BytesIO(handle.read())).namelist()
        self.assertEqual(names, ["pagina-001.png", "pagina-002.png", "pagina-004.png"])

        response = self.client.get(export.get_download_url())
        date = timezone.localtime(export.finished_at).date().isoformat()
        self.assertEqual(response.headers["Content-Type"], "application/zip")
        self.assertIn(
            f"neon-yokai-bureau_espanol_{date}_png.zip",
            response.headers["Content-Disposition"],
        )
        self.assertTrue(export.file.name.endswith(".zip"))


class PreparingPngExportTests(PngExportTestCase):
    """CP-90.2 — La espera del PNG reutiliza la de HU-27."""

    @mock.patch("albums.tasks.export_album_task")
    def test_png_export_waits_as_preparing_and_is_queued_once(self, task):
        """CP-90.2 — La espera del PNG reutiliza la de HU-27."""
        first_response = self.start_png()
        second_response = self.start_png()

        export = AlbumExport.objects.get(album=self.album)
        self.assertEqual(export.format, AlbumExport.Format.PNG_ZIP)
        self.assertEqual(export.status, AlbumExport.Status.PREPARING)
        task.assert_called_once_with(export.pk)
        self.assertRedirects(first_response, self.album.get_export_url())
        self.assertRedirects(second_response, self.album.get_export_url())
        status_page = self.client.get(self.album.get_export_url())
        self.assertContains(status_page, "Preparando exportación…")
        self.assertContains(status_page, "data-export-status-poll")
        status = self.client.get(export.get_status_url()).json()
        self.assertEqual(status["status"], AlbumExport.Status.PREPARING)
        self.assertFalse(status["is_terminal"])


class ImageFidelityTests(PngExportTestCase):
    """CP-90.3 — Resolución, modo de color y fidelidad con el editor."""

    def test_same_resolution_rgb_and_identical_to_render_page(self):
        """CP-90.3 — Misma resolución y píxeles iguales a render_page."""
        exported = self.export_page_image()
        self.assertEqual(exported.size, PAGE_SIZE)
        self.assertEqual(exported.mode, "RGB")
        expected = render_page(self.page)
        self.assertIsNone(ImageChops.difference(exported, expected).getbbox())

    def test_a_grayscale_original_exports_in_l(self):
        """CP-90.3 — Una original en escala de grises sale en modo L."""
        self.replace_original(self.page, Image.new("L", PAGE_SIZE, 255))
        self.assertEqual(self.export_page_image().mode, "L")

    def test_an_rgba_original_exports_in_rgb_without_alpha(self):
        """CP-90.3 — Una original RGBA sale en RGB, sin canal alfa."""
        self.replace_original(self.page, Image.new("RGBA", PAGE_SIZE, (255,) * 4))
        self.assertEqual(self.export_page_image().mode, "RGB")

    def test_a_gray_palette_exports_in_l_and_a_color_one_in_rgb(self):
        """CP-90.3 — Paleta con solo grises → L; con colores → RGB."""
        gray = Image.new("L", PAGE_SIZE, 200).convert("P")
        self.replace_original(self.page, gray)
        self.assertEqual(self.export_page_image().mode, "L")
        color = Image.new("RGB", PAGE_SIZE, (200, 30, 30)).convert("P")
        self.replace_original(self.page, color)
        self.assertEqual(self.export_page_image().mode, "RGB")

    def test_a_sixteen_bit_gray_page_is_scaled_not_whitened(self):
        """CP-90.3 — Un PNG gris de 16 bits no sale blanco: se escala a 8 bits."""
        sixteen = Image.new("I;16", PAGE_SIZE, QUARTER_GRAY_16)
        self.replace_original(self.page, sixteen)
        cleaned, _statuses = build_cleaned_image(self.page)
        replace_cleaned_image(self.page, cleaned)
        exported = self.export_page_image()
        self.assertEqual(exported.mode, "L")
        corner = exported.getpixel((2, PAGE_SIZE[1] - 2))
        self.assertAlmostEqual(corner, QUARTER_GRAY_8, delta=1)

    def test_a_sixteen_bit_thumbnail_is_not_white(self):
        """El mismo escalado vale para la miniatura de la rejilla."""
        sixteen = Image.new("I;16", (60, 80), QUARTER_GRAY_16)
        upload = SimpleUploadedFile("gris16.png", png_bytes(sixteen), "image/png")
        created, _rejected = create_pages_from_upload(self.album, [upload])
        with created[0].thumbnail.open("rb") as handle, Image.open(handle) as thumb:
            red, _green, _blue = thumb.convert("RGB").getpixel((5, 5))
        self.assertAlmostEqual(red, QUARTER_GRAY_8, delta=4)


class UntypesetPagesTests(PngExportTestCase):
    """CP-90.4 — Aviso de páginas sin maquetar y maquetación guardada."""

    def test_the_warning_counts_only_pages_with_text_to_typeset(self):
        """CP-90.4 — Cuenta la página sin maquetar; no las que no tienen texto."""
        self.mark_typeset(self.page)
        pending = self.make_page(self.album)
        self.make_ready_page(pending)
        self.make_page(self.album)
        only_skipped = self.make_page(self.album)
        self.make_ready_page(only_skipped)
        only_skipped.regions.update(skip_translation=True)
        response = self.client.get(self.album.get_export_url())
        self.assertContains(
            response,
            "1 página no está maquetada: se exportará con la maquetación que se ve "
            "en el editor.",
        )
        self.assertNotContains(response, "páginas no están maquetadas")

    def test_confirmation_is_required_before_exporting(self):
        """CP-90.4 — Con avisos, el servidor exige confirmarlos."""
        response = self.start_png(confirm=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revisa los avisos de las páginas traducidas")
        self.assertFalse(AlbumExport.objects.filter(album=self.album).exists())

    def test_an_untypeset_page_uses_its_saved_layout(self):
        """CP-90.4 — Se exporta con la maquetación guardada, no otra automática."""
        new_box = (20, 420, 200, 80)
        self.post_layout(
            self.first,
            dict(zip(("x", "y", "width", "height"), map(str, new_box), strict=True)),
        )
        self.page.refresh_from_db()
        self.assertFalse(self.page.is_typeset)
        exported = self.export_page_image()
        left, top, width, height = new_box
        moved = exported.crop((left, top, left + width, top + height))
        self.assertIsNotNone(ImageChops.invert(moved.convert("L")).getbbox())
        old_left, old_top, old_width, old_height = self.BOXES[1]
        old_area = exported.crop(
            (old_left, old_top, old_left + old_width, old_top + old_height)
        )
        self.assertEqual(old_area.getcolors(), [(old_width * old_height, WHITE)])

    def test_manual_cleaning_is_warned(self):
        """Aviso de regiones en "Limpieza manual" antes de exportar."""
        TextRegion.objects.filter(pk=self.first.pk).update(
            cleaning_status=TextRegion.CleaningStatus.MANUAL
        )
        response = self.client.get(self.album.get_export_url())
        self.assertContains(response, "1 región necesita limpieza manual")


class BlankAndKeptTextTests(PngExportTestCase):
    """CP-90.5 — Página en blanco, "No traducir" y página sin limpiar."""

    def test_a_blank_page_is_identical_to_the_original(self):
        """CP-90.5 — Una página sin texto sale igual que la original."""
        blank = self.make_page(self.album)
        self.start_png()
        exported = self.archive(self.latest_export())["pagina-002.png"]
        with blank.image.open("rb") as handle, Image.open(handle) as original:
            expected = original.convert("RGB")
        self.assertEqual(exported.size, expected.size)
        self.assertIsNone(ImageChops.difference(exported, expected).getbbox())

    def test_a_skipped_region_keeps_its_original_text(self):
        """CP-90.5 — Una región "No traducir" conserva su texto original."""
        TextRegion.objects.filter(pk=self.second.pk).update(skip_translation=True)
        exported = self.export_page_image()
        x, y, width, height = self.BOXES[2]
        self.assertEqual(exported.getpixel((x + width // 2, y + height // 2)), INK)

    def test_an_uncleaned_page_is_exported_untranslated_and_warned(self):
        """Página traducida sin imagen limpia: sale como la original y se avisa."""
        other = self.make_page(self.album)
        self.make_ready_page(other)
        ComicPage.objects.filter(pk=other.pk).update(cleaned_image="")
        response = self.client.get(self.album.get_export_url())
        self.assertContains(response, "1 página no está limpia: se exportará sin")
        self.start_png()
        exported = self.archive(self.latest_export())["pagina-002.png"]
        with other.image.open("rb") as handle, Image.open(handle) as original:
            expected = original.convert("RGB")
        self.assertIsNone(ImageChops.difference(exported, expected).getbbox())


class FailureTests(PngExportTestCase):
    """CP-90.6 — Un fallo no deja ningún ZIP a medias."""

    def test_a_failure_mid_task_leaves_an_error_and_no_file(self):
        """CP-90.6 — Error con su mensaje, sin archivo y sin temporal."""
        self.make_page(self.album)
        created = []
        real_mkstemp = tempfile.mkstemp

        def recording_mkstemp(*args, **kwargs):
            """Crea el temporal real y apunta su ruta."""
            descriptor, path = real_mkstemp(*args, **kwargs)
            created.append(path)
            return descriptor, path

        calls = []

        def failing_render(plan, storage):
            """Dibuja la primera página y falla en la segunda."""
            calls.append(plan["page_number"])
            if len(calls) == 2:
                raise RuntimeError("fallo")
            return render_plan(plan, storage)

        with (
            mock.patch("albums.exporting.tempfile.mkstemp", recording_mkstemp),
            mock.patch("albums.exporting.render_plan", failing_render),
        ):
            self.start_png()
        export = self.latest_export()
        self.assertEqual(export.status, AlbumExport.Status.FAILED)
        self.assertEqual(export.error, UNEXPECTED_ERROR_MESSAGE)
        self.assertFalse(export.file)
        self.assertEqual(len(created), 1)
        self.assertFalse(os.path.exists(created[0]))
        response = self.client.get(self.album.get_export_url())
        self.assertContains(response, "No se pudo preparar la exportación.")
        self.assertNotContains(response, 'href="/exportaciones/')

    def test_a_cleaned_image_changed_after_the_snapshot_fails(self):
        """CP-90.6 — La imagen limpia cambió durante la tarea: error y sin ZIP."""
        self.start_png(execute=False)
        replace_cleaned_image(self.page, Image.new("RGB", PAGE_SIZE, WHITE))
        for callback in self.callbacks:
            callback()
        export = self.latest_export()
        self.assertEqual(export.status, AlbumExport.Status.FAILED)
        self.assertEqual(export.error, UNEXPECTED_ERROR_MESSAGE)
        self.assertFalse(export.file)

    def test_a_missing_original_fails(self):
        """CP-90.6 — La original desapareció durante la tarea: error y sin ZIP."""
        self.start_png(execute=False)
        self.page.image.storage.delete(self.page.image.name)
        for callback in self.callbacks:
            callback()
        export = self.latest_export()
        self.assertEqual(export.status, AlbumExport.Status.FAILED)
        self.assertFalse(export.file)


class ForeignAlbumTests(PngExportTestCase):
    """CP-90.7 — Álbum y ZIP de otra cuenta → 404."""

    def test_foreign_export_and_download_answer_not_found(self):
        """CP-90.7 — Exportar o descargar el PNG de otra cuenta → 404."""
        foreign_album = self.foreign_page.album
        response = self.client.post(
            foreign_album.get_export_url(),
            {"format": "png_zip", "confirm_png": "1"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(AlbumExport.objects.filter(album=foreign_album).exists())

        export = AlbumExport.objects.create(
            album=foreign_album,
            format=AlbumExport.Format.PNG_ZIP,
            status=AlbumExport.Status.READY,
            snapshot={"pages": []},
        )
        export.file.save("foreign.zip", ContentFile(b"zip privado"))
        response = self.client.get(
            reverse("albums:export_download", kwargs={"pk": export.pk})
        )
        self.assertEqual(response.status_code, 404)
