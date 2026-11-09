"""Pruebas de descarga privada de exportaciones terminadas (HU-28)."""

import os

from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from albums.models import AlbumExport
from albums.tests.test_export import EXPORT_MEDIA_ROOT, AlbumExportTestCase
from albums.translation_review import edit_translation


@override_settings(MEDIA_ROOT=EXPORT_MEDIA_ROOT)
class ExportDownloadTestCase(AlbumExportTestCase):
    """Base que prepara exportaciones en el almacenamiento temporal."""

    def ready_export(self):
        """Crea y devuelve una exportación DOCX terminada del álbum propio."""
        self.approve(self.first)
        self.start_export()
        return AlbumExport.objects.get(album=self.album)


class FinishedExportDownloadTests(ExportDownloadTestCase):
    """CP-28.1 — Descargar una exportación terminada — Happy path."""

    def test_download_delivers_the_exact_saved_file(self):
        """CP-28.1 — La respuesta contiene exactamente el DOCX exportado."""
        export = self.ready_export()
        with export.file.open("rb") as stored_file:
            expected_content = stored_file.read()

        response = self.client.get(export.get_download_url())

        downloaded_content = b"".join(response.streaming_content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(downloaded_content, expected_content)
        self.assertEqual(
            response.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document",
        )

    def test_filename_includes_album_language_and_date(self):
        """CP-28.1 — El nombre incluye álbum, idioma de destino y fecha."""
        export = self.ready_export()
        expected_date = timezone.localtime(export.finished_at).date().isoformat()

        response = self.client.get(export.get_download_url())

        disposition = response.headers["Content-Disposition"]
        self.assertIn("attachment", disposition)
        self.assertIn("neon-yokai-bureau", disposition)
        self.assertIn("espanol", disposition)
        self.assertIn(expected_date, disposition)
        self.assertIn(".docx", disposition)

    def test_every_finished_export_remains_available_in_history(self):
        """CP-28.1 — El historial conserva cada exportación sin caducidad."""
        first_export = self.ready_export()
        edit_translation(self.first, "Segunda versión aprobada")
        self.approve(self.first)
        self.start_export()
        second_export = AlbumExport.objects.filter(album=self.album).first()

        response = self.client.get(self.album.get_export_url())

        self.assertNotEqual(first_export.pk, second_export.pk)
        self.assertContains(response, first_export.get_download_url())
        self.assertContains(response, second_export.get_download_url())


class UnavailableExportTests(ExportDownloadTestCase):
    """CP-28.2/28.4 — No hay archivo terminado para descargar."""

    def test_without_finished_exports_no_download_is_offered(self):
        """CP-28.2 — Sin exportaciones terminadas no aparece la opción."""
        response = self.client.get(self.album.get_export_url())

        self.assertNotContains(response, 'href="/exportaciones/')

    def test_nonexistent_download_returns_not_found(self):
        """CP-28.2 — Una dirección inexistente responde 404."""
        url = reverse("albums:export_download", kwargs={"pk": 999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_preparing_export_has_no_link_and_cannot_be_downloaded(self):
        """CP-28.4 — Preparando no muestra ni entrega el archivo."""
        export = AlbumExport.objects.create(
            album=self.album,
            snapshot={"regions": []},
        )

        screen = self.client.get(self.album.get_export_url())
        download = self.client.get(export.get_download_url())

        self.assertNotContains(screen, export.get_download_url())
        self.assertEqual(download.status_code, 404)

    def test_missing_ready_file_returns_not_found(self):
        """CP-28.2 — Un registro listo sin archivo físico responde 404."""
        export = self.ready_export()
        os.remove(export.file.path)

        response = self.client.get(export.get_download_url())

        self.assertEqual(response.status_code, 404)


class ExportDownloadAccessTests(ExportDownloadTestCase):
    """CP-28.3 — Solo el propietario puede descargar."""

    def create_foreign_export(self):
        """Crea un archivo listo que pertenece a la otra cuenta de prueba."""
        export = AlbumExport.objects.create(
            album=self.foreign_page.album,
            status=AlbumExport.Status.READY,
            snapshot={"regions": []},
            finished_at=timezone.now(),
        )
        export.file.save("foreign.docx", ContentFile(b"contenido privado"))
        return export

    def test_another_account_receives_not_found(self):
        """CP-28.3 — Una cuenta ajena recibe 404 y ningún contenido."""
        export = self.create_foreign_export()

        response = self.client.get(export.get_download_url())

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "contenido privado", status_code=404)

    def test_anonymous_visitor_receives_not_found_instead_of_login(self):
        """CP-28.3 — Sin sesión también se responde 404, no redirección."""
        export = self.create_foreign_export()
        self.client.logout()

        response = self.client.get(export.get_download_url())

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Location", response.headers)
