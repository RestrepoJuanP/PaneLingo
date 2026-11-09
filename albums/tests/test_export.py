"""Pruebas de exportación de traducciones aprobadas a DOCX (HU-27)."""

import os
import shutil
import tempfile
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from docx import Document

from albums.exporting import run_album_export
from albums.models import AlbumExport
from albums.tests.test_translation_review import ReviewTestCase
from albums.translation_review import approve_translation, edit_translation

EXPORT_MEDIA_ROOT = tempfile.mkdtemp(prefix="panelingo-export-media-")


@override_settings(MEDIA_ROOT=EXPORT_MEDIA_ROOT)
class AlbumExportTestCase(ReviewTestCase):
    """Base con traducciones generadas y almacenamiento temporal."""

    def tearDown(self):
        """Elimina los DOCX y las imágenes creadas durante cada prueba."""
        super().tearDown()
        shutil.rmtree(EXPORT_MEDIA_ROOT, ignore_errors=True)

    def approve(self, region):
        """Aprueba una traducción usando el servicio de producción."""
        approve_translation(region)
        region.refresh_from_db()

    def start_export(self, confirm=True, execute=True):
        """Solicita exportar y ejecuta o conserva pendiente la tarea Huey."""
        data = {"format": "docx"}
        if confirm:
            data["confirm"] = "1"
        with self.captureOnCommitCallbacks(execute=execute):
            response = self.client.post(self.album.get_export_url(), data)
        return response

    def document_text(self, export):
        """Extrae el texto visible del DOCX generado."""
        document = Document(export.file.path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)


class ExportDocumentTests(AlbumExportTestCase):
    """CP-27.1 — Exportar traducciones aprobadas a DOCX — Happy path."""

    def test_docx_contains_every_required_region_field(self):
        """CP-27.1 — El DOCX incluye página, orden, tipo y ambos textos."""
        self.approve(self.first)
        self.approve(self.second)

        response = self.start_export()

        export = AlbumExport.objects.get(album=self.album)
        self.assertRedirects(response, self.album.get_export_url())
        self.assertEqual(export.status, AlbumExport.Status.READY)
        self.assertTrue(export.file.name.endswith(".docx"))
        self.assertTrue(os.path.exists(export.file.path))
        content = self.document_text(export)
        self.assertIn(self.album.title, content)
        self.assertIn("Página 1", content)
        self.assertIn("Región 1 · Globo de diálogo", content)
        self.assertIn("Texto de origen: こんにちは", content)
        self.assertIn("Traducción: [ES] こんにちは", content)
        self.assertIn("Región 2 · Globo de diálogo", content)

    def test_export_uses_the_confirmed_snapshot_while_user_keeps_working(self):
        """CP-27.1/27.4 — La tarea usa la instantánea confirmada al iniciar."""
        self.approve(self.first)
        with mock.patch("albums.tasks.export_album_task"):
            self.start_export()
        export = AlbumExport.objects.get(album=self.album)

        edit_translation(self.first, "Cambio posterior")
        run_album_export(export.pk)

        export.refresh_from_db()
        content = self.document_text(export)
        self.assertIn("Traducción: [ES] こんにちは", content)
        self.assertNotIn("Cambio posterior", content)


class UnapprovedRegionsTests(AlbumExportTestCase):
    """CP-27.2 — Advertir y omitir regiones sin aprobar."""

    def test_warning_appears_before_confirming(self):
        """CP-27.2 — La pantalla indica cuántas regiones se omitirán."""
        self.approve(self.first)

        response = self.client.get(self.album.get_export_url())

        self.assertContains(response, "1 región sin aprobar no se incluirá")
        self.assertContains(response, "Confirmar y exportar")

    def test_post_without_confirmation_does_not_start(self):
        """CP-27.2 — El servidor exige confirmar la omisión de pendientes."""
        self.approve(self.first)

        response = self.start_export(confirm=False)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Confirma que deseas continuar sin las regiones pendientes.",
        )
        self.assertFalse(AlbumExport.objects.exists())

    def test_confirmed_export_contains_only_approved_regions(self):
        """CP-27.2 — El DOCX confirmado no incluye la región pendiente."""
        self.approve(self.first)

        self.start_export()

        export = AlbumExport.objects.get(album=self.album)
        self.assertEqual(export.approved_count, 1)
        self.assertEqual(export.skipped_count, 1)
        content = self.document_text(export)
        self.assertIn("Región 1", content)
        self.assertNotIn("Región 2", content)
        self.assertNotIn("[ES] ありがとう", content)


class NothingApprovedTests(AlbumExportTestCase):
    """CP-27.3 — No hay nada aprobado — Flujo alternativo."""

    def test_export_is_disabled_and_explains_why(self):
        """CP-27.3 — Sin aprobaciones no se ofrece una acción habilitada."""
        response = self.client.get(self.album.get_export_url())

        self.assertContains(response, "Aprueba al menos una traducción")
        self.assertContains(response, "disabled")

    def test_navigation_opens_the_current_album_export_screen(self):
        """CP-27.3 — La navegación de revisión lleva a un álbum propio."""
        response = self.client.get(reverse("albums:list"))

        self.assertContains(response, f'href="{self.album.get_export_url()}"')

    def test_forged_post_does_not_create_an_empty_export(self):
        """CP-27.3 — Un POST manipulado tampoco genera un archivo vacío."""
        response = self.start_export()

        self.assertRedirects(
            response,
            self.album.get_export_url(),
            fetch_redirect_response=False,
        )
        self.assertFalse(AlbumExport.objects.exists())
        followed = self.client.get(response.url)
        self.assertContains(followed, "No hay traducciones aprobadas")

    def test_unknown_format_is_rejected(self):
        """CP-27.3 — Un formato fuera del alcance no genera otro archivo."""
        self.approve(self.first)

        response = self.client.post(
            self.album.get_export_url(),
            {"format": "png", "confirm": "1"},
            follow=True,
        )

        self.assertContains(response, "El formato solicitado no está disponible")
        self.assertFalse(AlbumExport.objects.exists())


class BackgroundExportTests(AlbumExportTestCase):
    """CP-27.4 — Preparar la exportación en segundo plano."""

    @mock.patch("albums.tasks.export_album_task")
    def test_request_queues_once_and_the_user_can_keep_working(self, task):
        """CP-27.4 — Se muestra Preparando y el resto de la app responde."""
        self.approve(self.first)

        first_response = self.start_export()
        second_response = self.start_export()

        export = AlbumExport.objects.get(album=self.album)
        task.assert_called_once_with(export.pk)
        self.assertRedirects(first_response, self.album.get_export_url())
        self.assertRedirects(second_response, self.album.get_export_url())
        status_page = self.client.get(self.album.get_export_url())
        workspace = self.client.get(self.page.get_absolute_url())
        self.assertContains(status_page, "Preparando exportación…")
        self.assertContains(status_page, "data-export-status-poll")
        self.assertEqual(workspace.status_code, 200)

    def test_status_endpoint_reports_completion(self):
        """CP-27.4 — El sondeo privado informa que el archivo está listo."""
        self.approve(self.first)
        self.start_export()
        export = AlbumExport.objects.get(album=self.album)

        response = self.client.get(export.get_status_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], AlbumExport.Status.READY)
        self.assertTrue(response.json()["is_terminal"])

    def test_unexpected_failure_leaves_a_retryable_error(self):
        """CP-27.4 — Un fallo no deja la exportación eternamente preparando."""
        self.approve(self.first)
        with mock.patch("albums.tasks.export_album_task"):
            self.start_export()
        export = AlbumExport.objects.get(album=self.album)

        with mock.patch(
            "albums.exporting.build_export_document",
            side_effect=RuntimeError("fallo"),
        ):
            run_album_export(export.pk)

        export.refresh_from_db()
        self.assertEqual(export.status, AlbumExport.Status.FAILED)
        self.assertFalse(export.file)
        response = self.client.get(self.album.get_export_url())
        self.assertContains(response, "No se pudo preparar")
        self.assertContains(response, export.error)


class ExportAccessAndCleanupTests(AlbumExportTestCase):
    """Aislamiento y almacenamiento privado de las exportaciones."""

    def test_foreign_export_screen_and_status_return_not_found(self):
        """HU-27 — Una cuenta ajena recibe 404 y no conoce el estado."""
        foreign_album = self.foreign_page.album
        foreign_export = AlbumExport.objects.create(
            album=foreign_album,
            snapshot={"regions": []},
        )

        screen = self.client.get(foreign_album.get_export_url())
        status = self.client.get(foreign_export.get_status_url())

        self.assertEqual(screen.status_code, 404)
        self.assertEqual(status.status_code, 404)

    def test_ready_file_is_not_exposed_as_a_public_media_link(self):
        """HU-27/DT-02 — La pantalla no publica la dirección del archivo."""
        self.approve(self.first)
        self.start_export()
        export = AlbumExport.objects.get(album=self.album)

        response = self.client.get(self.album.get_export_url())

        self.assertNotContains(response, export.file.url)

    def test_deleting_album_removes_its_export_file(self):
        """HU-27 — Al borrar el álbum no queda un DOCX huérfano."""
        self.approve(self.first)
        self.start_export()
        export = AlbumExport.objects.get(album=self.album)
        path = export.file.path
        self.assertTrue(os.path.exists(path))

        self.album.delete()

        self.assertFalse(os.path.exists(path))
