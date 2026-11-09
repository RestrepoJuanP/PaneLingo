"""Pruebas de las regiones añadidas por el traductor (HU-85)."""

from io import BytesIO
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import override_settings
from PIL import Image

from albums.models import ComicPage, TextRegion
from albums.ocr.base import DetectedRegion, OcrProviderError
from albums.ocr.fake import FakeOcrProvider
from albums.tests.test_processing import MEDIA_ROOT, ProcessingTestCase


def use_provider(provider):
    """Sustituye el OCR usado por el servicio de regiones manuales."""
    return mock.patch("albums.manual_regions.get_provider", return_value=provider)


@override_settings(MEDIA_ROOT=MEDIA_ROOT, OCR_PROVIDER="fake")
class ManualRegionTests(ProcessingTestCase):
    """CP-85.1 a CP-85.7 — Añadir una región omitida por el OCR."""

    reliable_text = DetectedRegion(
        x=4,
        y=4,
        width=70,
        height=30,
        text="手書きの文字",
        confidence=0.96,
    )

    def set_processed(self, page=None, status=ComicPage.Status.PROCESSED):
        """Deja la página lista para aceptar regiones manuales."""
        page = page or self.page
        page.status = status
        page.save(update_fields=["status"])

    def add_region(self, page=None, provider=None, follow=False, **overrides):
        """Envía una caja válida usando el proveedor indicado."""
        page = page or self.page
        provider = provider or FakeOcrProvider(regions=[self.reliable_text])
        data = {"x": 170, "y": 40, "width": 80, "height": 80}
        data.update(overrides)
        with use_provider(provider):
            return self.client.post(page.get_region_add_url(), data, follow=follow)

    def make_existing_region(self, reading_order, x):
        """Crea una región existente en la misma fila que la nueva."""
        return TextRegion.objects.create(
            page=self.page,
            reading_order=reading_order,
            kind=TextRegion.Kind.BALLOON,
            x=x,
            y=40,
            width=80,
            height=80,
            source_text="既存",
            confidence=0.95,
        )

    def test_drawn_region_is_read_marked_and_inserted_in_reading_order(self):
        """CP-85.1 — OCR, tipo, marca manual y orden japonés quedan guardados."""
        self.set_processed()
        right = self.make_existing_region(1, 270)
        left = self.make_existing_region(2, 40)

        response = self.add_region()

        self.assertEqual(response.status_code, 302)
        region = TextRegion.objects.get(is_manual=True)
        self.assertEqual(region.source_text, "手書きの文字")
        self.assertEqual(region.confidence, 0.96)
        self.assertEqual(region.kind, TextRegion.Kind.BALLOON)
        self.assertFalse(region.needs_review)
        right.refresh_from_db()
        left.refresh_from_db()
        self.assertEqual(
            [right.reading_order, region.reading_order, left.reading_order],
            [1, 2, 3],
        )

    def test_empty_ocr_result_creates_an_editable_region_with_the_warning(self):
        """CP-85.2 — Sin texto se crea la región y se pide escribirlo a mano."""
        self.set_processed()

        response = self.add_region(provider=FakeOcrProvider(regions=[]), follow=True)

        region = TextRegion.objects.get()
        self.assertTrue(region.is_manual)
        self.assertEqual(region.source_text, "")
        self.assertTrue(region.needs_review)
        self.assertContains(
            response,
            "No se reconoció texto en esta zona: escríbelo a mano.",
        )
        self.assertContains(response, "autofocus")

    def test_too_small_and_outside_boxes_are_rejected_by_the_server(self):
        """CP-85.3 — El servidor rechaza cajas pequeñas o fuera de la imagen."""
        self.set_processed()

        small = self.add_region(width=10, height=10)
        outside = self.add_region(x=350, y=500, width=80, height=80)

        self.assertEqual(small.status_code, 422)
        self.assertContains(
            small,
            "La región debe medir al menos 16 píxeles.",
            status_code=422,
        )
        self.assertEqual(outside.status_code, 422)
        self.assertContains(
            outside,
            "La región debe quedar completamente dentro de la imagen.",
            status_code=422,
        )
        self.assertFalse(TextRegion.objects.exists())

    def test_pointer_mode_can_be_cancelled_and_reports_a_small_box(self):
        """CP-85.4 — El modo de dibujo se cancela con Escape o el botón."""
        self.set_processed()

        response = self.client.get(self.page.get_absolute_url())
        script = (Path(settings.BASE_DIR) / "static" / "js" / "app.js").read_text(
            encoding="utf-8"
        )

        self.assertContains(response, "data-manual-region-toggle")
        self.assertContains(response, "data-manual-region-cancel")
        self.assertIn('event.key === "Escape"', script)
        self.assertIn('"La región es demasiado pequeña."', script)
        self.assertIn("pointerdown", script)

    def test_new_region_reopens_an_approved_page_and_uses_existing_workflow(self):
        """CP-85.5 — La región nueva se corrige, traduce y aprueba normalmente."""
        self.set_processed(status=ComicPage.Status.APPROVED)

        self.add_region()
        region = TextRegion.objects.get()
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)

        self.client.post(region.get_correct_url(), {"text": "手書き"})
        self.client.post(region.get_translation_url(), {"text": "Texto manuscrito"})
        self.client.post(region.get_approve_url(), {"text": "Texto manuscrito"})

        region.refresh_from_db()
        self.page.refresh_from_db()
        self.assertEqual(region.final_text, "手書き")
        self.assertTrue(region.is_translation_approved)
        self.assertEqual(self.page.status, ComicPage.Status.APPROVED)

    def test_coordinate_form_is_labelled_and_creates_the_same_region(self):
        """CP-85.6 — El formulario permite añadir la región sin usar el ratón."""
        self.set_processed()

        form_page = self.client.get(self.page.get_absolute_url())
        response = self.add_region(x=30, y=100, width=120, height=90)

        self.assertContains(form_page, 'for="id_x"')
        self.assertContains(form_page, 'for="id_y"')
        self.assertContains(form_page, 'for="id_width"')
        self.assertContains(form_page, 'for="id_height"')
        self.assertEqual(response.status_code, 302)
        region = TextRegion.objects.get()
        self.assertEqual(
            (region.x, region.y, region.width, region.height),
            (30, 100, 120, 90),
        )

    def test_foreign_page_returns_not_found_and_creates_nothing(self):
        """CP-85.7 — Una página ajena responde 404 y no crea una región."""
        self.set_processed(self.foreign_page)

        response = self.add_region(page=self.foreign_page)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(TextRegion.objects.exists())

    def test_provider_failure_keeps_the_page_unchanged_and_can_be_retried(self):
        """CP-85.2 — Un fallo de OCR conserva la caja en el formulario."""
        self.set_processed()
        provider = FakeOcrProvider(error="Servicio no disponible")

        response = self.add_region(provider=provider)

        self.assertEqual(response.status_code, 502)
        self.assertContains(
            response,
            "No se pudo leer esta zona. Inténtalo de nuevo.",
            status_code=502,
        )
        self.assertContains(response, 'value="170"', status_code=502)
        self.assertFalse(TextRegion.objects.exists())

    def test_unprocessed_page_refuses_the_action(self):
        """CP-85.1 — Solo una página procesada acepta regiones manuales."""
        response = self.add_region()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(TextRegion.objects.exists())

    def test_get_does_not_create_a_region(self):
        """CP-85.7 — Abrir la ruta de acción responde 405 y no escribe."""
        self.set_processed()

        response = self.client.get(self.page.get_region_add_url())

        self.assertEqual(response.status_code, 405)
        self.assertFalse(TextRegion.objects.exists())

    def test_ocr_crop_is_padded_to_the_provider_minimum(self):
        """CP-85.1 — Un recorte pequeño se amplía antes de enviarlo al OCR."""
        self.set_processed()
        provider = mock.Mock()
        provider.detect.return_value = [self.reliable_text]

        self.add_region(provider=provider, width=20, height=20)

        sent_bytes = provider.detect.call_args.args[0]
        with Image.open(BytesIO(sent_bytes)) as image:
            self.assertEqual(image.size, (50, 50))


class ManualRegionDefaultTests(ProcessingTestCase):
    """HU-85 — Las regiones detectadas siguen siendo no manuales por defecto."""

    def test_existing_processing_creates_non_manual_regions(self):
        """CP-85.1 — El OCR de página completa no marca regiones manuales."""
        region = TextRegion.objects.create(
            page=self.page,
            reading_order=1,
            x=10,
            y=10,
            width=40,
            height=40,
        )
        self.assertFalse(region.is_manual)


class ManualRegionProviderErrorTests(ProcessingTestCase):
    """HU-85 — El contrato del proveedor conserva su excepción conocida."""

    def test_configured_provider_error_is_not_replaced_by_an_unknown_failure(self):
        """CP-85.2 — El servicio propaga el fallo esperado para la vista."""
        self.page.status = ComicPage.Status.PROCESSED
        self.page.save(update_fields=["status"])
        provider = mock.Mock()
        provider.detect.side_effect = OcrProviderError("sin red")

        with use_provider(provider):
            response = self.client.post(
                self.page.get_region_add_url(),
                {"x": 20, "y": 20, "width": 100, "height": 100},
            )

        self.assertEqual(response.status_code, 502)
