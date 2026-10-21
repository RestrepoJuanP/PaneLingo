"""Pruebas de la corrección del texto detectado (HU-15)."""

from albums.models import ComicPage, TextRegion
from albums.ocr.base import DetectedRegion
from albums.ocr.fake import FakeOcrProvider
from albums.tests.test_processing import ProcessingTestCase, use_provider

# En japonés el de la derecha es el n.º 1: dudoso; el n.º 2 es fiable.
DOUBTFUL = DetectedRegion(260, 50, 120, 80, "たぶん", 0.42)
RELIABLE = DetectedRegion(40, 40, 120, 80, "たしかに", 0.98)


class CorrectionTestCase(ProcessingTestCase):
    """Base: la página procesada con una región dudosa y otra fiable."""

    def setUp(self):
        """Procesa la página con las dos regiones."""
        super().setUp()
        with use_provider(FakeOcrProvider(regions=[DOUBTFUL, RELIABLE])):
            self.process()
        self.first, self.second = self.page.regions.order_by("reading_order")

    def correct(self, region, **data):
        """Envía la corrección de una región y devuelve la respuesta."""
        response = self.client.post(region.get_correct_url(), data=data)
        region.refresh_from_db()
        self.page.refresh_from_db()
        return response


class CorrectRegionTests(CorrectionTestCase):
    """CP-15.1 — Corregir el texto de una región — Happy Path."""

    def test_the_corrected_text_is_kept(self):
        """CP-15.1 — La región conserva el texto corregido."""
        response = self.correct(self.first, text="たぶんね\r\nほんとうに")

        self.assertEqual(self.first.corrected_text, "たぶんね\nほんとうに")
        self.assertTrue(self.first.is_corrected)
        self.assertIsNotNone(self.first.corrected_at)
        self.assertRedirects(
            response,
            f"{self.page.get_absolute_url()}#region-1",
            fetch_redirect_response=False,
        )

    def test_the_region_is_marked_as_reviewed(self):
        """CP-15.1 — Queda "revisada por el usuario" y deja de pedir revisión."""
        self.correct(self.first, text="たぶんね")

        self.assertFalse(self.first.needs_review)
        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)
        content = self.client.get(self.page.get_absolute_url()).content.decode()
        self.assertIn("Corregida", content)

    def test_the_ocr_text_is_preserved(self):
        """CP-15.1 — El texto original del OCR se conserva y se muestra."""
        self.correct(self.first, text="たぶんね")

        self.assertEqual(self.first.source_text, "たぶん")
        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, "Texto del OCR:")
        self.assertContains(response, "Restaurar texto del OCR")

    def test_correcting_one_region_leaves_the_others(self):
        """CP-15.1 — Corregir una región no toca las demás."""
        self.correct(self.first, text="たぶんね")

        self.second.refresh_from_db()
        self.assertFalse(self.second.is_corrected)
        self.assertEqual(self.second.final_text, "たしかに")

    def test_the_page_offers_the_edit_form(self):
        """CP-15.1 — Cada región tiene su campo de corrección con etiqueta."""
        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, 'for="region-text-1"')
        self.assertContains(response, 'id="region-text-1"')
        self.assertContains(response, self.first.get_correct_url())
        self.assertContains(response, "Corregir texto")


class TranslationTextTests(CorrectionTestCase):
    """CP-15.2 — La traducción usa el texto corregido."""

    def test_the_final_text_is_the_corrected_one(self):
        """CP-15.2 — El texto que vale para traducir es el corregido."""
        self.correct(self.first, text="たぶんね")

        self.assertEqual(self.first.final_text, "たぶんね")
        self.assertEqual(self.second.final_text, "たしかに")


class RestoreTests(CorrectionTestCase):
    """CP-15.3 — Deshacer una corrección."""

    def test_restoring_returns_to_the_ocr_text(self):
        """CP-15.3 — "Restaurar" vuelve al texto detectado originalmente."""
        self.correct(self.first, text="たぶんね")

        self.correct(self.first, restore="1")

        self.assertFalse(self.first.is_corrected)
        self.assertEqual(self.first.final_text, "たぶん")
        self.assertEqual(self.first.corrected_text, "")

    def test_restoring_brings_back_the_review_mark(self):
        """CP-15.3 — Si el texto del OCR era dudoso, vuelve a pedir revisión."""
        self.correct(self.first, text="たぶんね")

        self.correct(self.first, restore="1")

        self.assertTrue(self.first.needs_review)
        self.assertEqual(self.page.status, ComicPage.Status.NEEDS_REVIEW)


class UnsavedChangesTests(CorrectionTestCase):
    """CP-15.4 — Salir con cambios sin guardar — Flujo alternativo."""

    def test_the_workspace_watches_the_edit_forms(self):
        """CP-15.4 — Los formularios llevan la marca que vigila el aviso."""
        content = self.client.get(self.page.get_absolute_url()).content.decode()

        self.assertIn("data-region-workspace", content)
        self.assertEqual(content.count("data-region-edit"), 2)

    def test_reprocessing_warns_about_manual_corrections(self):
        """CP-15.4 — Volver a procesar avisa de que se perderán las correcciones."""
        self.correct(self.first, text="たぶんね")

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "Se perderán 1 corrección que hiciste a mano.")


class EmptyRegionTests(CorrectionTestCase):
    """CP-15.5 — Dejar vacía una región — Flujo alternativo."""

    def test_an_empty_region_has_nothing_to_translate(self):
        """CP-15.5 — Se acepta como "sin texto que traducir" y no se borra."""
        self.correct(self.first, text="   ")

        self.assertTrue(TextRegion.objects.filter(pk=self.first.pk).exists())
        self.assertTrue(self.first.has_nothing_to_translate)
        self.assertEqual(self.first.final_text, "")
        self.assertFalse(self.first.needs_review)
        response = self.client.get(self.page.get_absolute_url(), follow=True)
        self.assertContains(response, "Sin texto que traducir")


class CorrectionAccessTests(CorrectionTestCase):
    """CP-15 — Una región ajena no se puede corregir."""

    def test_a_foreign_region_is_not_found(self):
        """Recurso de otra cuenta → 404 y la región no cambia."""
        foreign = TextRegion.objects.create(
            page=self.foreign_page,
            reading_order=1,
            x=0,
            y=0,
            width=10,
            height=10,
            source_text="よそ",
        )

        response = self.client.post(foreign.get_correct_url(), {"text": "cambio"})

        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertFalse(foreign.is_corrected)

    def test_get_is_not_allowed(self):
        """Un GET no corrige nada: responde 405."""
        response = self.client.get(self.first.get_correct_url())

        self.assertEqual(response.status_code, 405)
