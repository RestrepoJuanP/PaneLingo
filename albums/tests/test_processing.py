"""Pruebas del procesamiento de páginas: detectar regiones de texto (HU-12).

El proveedor externo siempre está simulado (FakeOcrProvider), y Huey corre en
modo inmediato salvo en las pruebas que comprueban que la tarea se encola sin
ejecutarse, que sustituyen la tarea por un doble.
"""

import io
import shutil
import tempfile
from datetime import timedelta
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from huey.contrib.djhuey import HUEY
from PIL import Image

from accounts.models import User
from albums.models import Album, ComicPage, Language, TextRegion
from albums.ocr.base import DetectedRegion
from albums.ocr.fake import FakeOcrProvider
from albums.processing import UNEXPECTED_ERROR_MESSAGE, run_detection
from albums.services import create_pages_from_upload

PASSWORD = "TraduccionSegura42"

MEDIA_ROOT = tempfile.mkdtemp(prefix="panelingo-processing-media-")

# Dos globos en la misma fila de una página de 400 x 560: uno a la izquierda
# y otro a la derecha, separados lo bastante para no fundirse en uno. Sirven
# para comprobar el orden de lectura.
LEFT_BALLOON = DetectedRegion(x=40, y=40, width=120, height=80, text="izquierda")
RIGHT_BALLOON = DetectedRegion(x=260, y=50, width=120, height=80, text="derecha")


def make_white_page(name="pagina.png"):
    """Devuelve una página blanca de 400 x 560, como la de un globo de diálogo."""
    buffer = io.BytesIO()
    Image.new("RGB", (400, 560), "white").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def use_provider(provider):
    """Sustituye el proveedor configurado por el indicado."""
    return mock.patch("albums.processing.get_provider", return_value=provider)


@override_settings(MEDIA_ROOT=MEDIA_ROOT, OCR_PROVIDER="fake")
class ProcessingTestCase(TestCase):
    """Base común: dos cuentas, un álbum japonés con una página y otro ajeno."""

    @classmethod
    def setUpClass(cls):
        """Ejecuta las tareas de Huey dentro de la petición, sin trabajador."""
        super().setUpClass()
        cls.previous_immediate = HUEY.immediate
        HUEY.immediate = True

    @classmethod
    def tearDownClass(cls):
        """Devuelve Huey a su modo original."""
        HUEY.immediate = cls.previous_immediate
        super().tearDownClass()

    def setUp(self):
        """Crea las cuentas, los álbumes y una página en cada uno."""
        self.owner = User.objects.create_user(
            email="mira@estudio.test",
            password=PASSWORD,
            display_name="Mira Okonkwo",
        )
        self.other = User.objects.create_user(
            email="ajena@estudio.test",
            password=PASSWORD,
            display_name="Cuenta ajena",
        )
        self.album = self.make_album(self.owner, "ja")
        self.page = self.make_page(self.album)
        self.foreign_page = self.make_page(self.make_album(self.other, "ja"))
        self.client.login(email=self.owner.email, password=PASSWORD)

    def tearDown(self):
        """Borra los archivos que la prueba haya dejado en media/."""
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def make_album(self, owner, source_code):
        """Crea un álbum con el idioma de origen indicado y destino español."""
        return Album.objects.create(
            owner=owner,
            title="Neon Yokai Bureau",
            source_language=Language.objects.get(code=source_code),
            target_language=Language.objects.get(code="es"),
        )

    def make_page(self, album):
        """Carga una página blanca en el álbum y la devuelve."""
        created, _rejected = create_pages_from_upload(album, [make_white_page()])
        return created[0]

    def process(self, page=None, **data):
        """Pide procesar una página y ejecuta lo que se encole al confirmar."""
        page = page or self.page
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(page.get_process_url(), data=data)
        page.refresh_from_db()
        return response


class ProcessPageTests(ProcessingTestCase):
    """CP-12.1 — Procesar una página — Happy Path."""

    @mock.patch("albums.tasks.process_page_task")
    def test_the_page_moves_to_processing_and_the_task_is_queued(self, task):
        """CP-12.1 — Al pulsar "Procesar página" pasa a "Procesando" y se encola."""
        response = self.process()

        self.assertEqual(self.page.status, ComicPage.Status.PROCESSING)
        self.assertIsNotNone(self.page.processing_started_at)
        task.assert_called_once_with(self.page.pk)
        self.assertRedirects(response, self.page.get_absolute_url())

    @mock.patch("albums.tasks.process_page_task")
    def test_the_app_stays_usable_while_processing(self, task):
        """CP-12.1 — La respuesta llega sin esperar a la detección."""
        response = self.process()
        followed = self.client.get(response.url)

        self.assertContains(followed, "Puedes seguir usando PaneLingo")
        self.assertContains(followed, "Procesando…")
        self.assertEqual(
            self.client.get(self.album.get_absolute_url()).status_code, 200
        )
        self.assertFalse(self.page.regions.exists())

    def test_finished_detection_leaves_the_page_processed(self):
        """CP-12.1 — Al terminar, la página queda "Procesada" con sus regiones."""
        response = self.process()

        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)
        self.assertEqual(self.page.regions.count(), 2)
        self.assertIsNone(self.page.processing_started_at)
        self.assertContains(
            self.client.get(response.url), "2 regiones · orden de lectura"
        )

    def test_each_region_keeps_its_position_and_kind(self):
        """CP-12.1 — Cada región guarda su posición y su tipo."""
        with use_provider(FakeOcrProvider(regions=[RIGHT_BALLOON])):
            self.process()

        region = self.page.regions.get()
        self.assertEqual(
            (region.x, region.y, region.width, region.height), (260, 50, 120, 80)
        )
        self.assertEqual(region.kind, TextRegion.Kind.BALLOON)

    @mock.patch("albums.tasks.process_page_task")
    def test_a_page_already_processing_is_not_queued_twice(self, task):
        """CP-12.1 — Flujo alternativo: pulsar dos veces no lanza dos detecciones."""
        self.process()
        response = self.process()

        task.assert_called_once()
        self.assertContains(
            self.client.get(response.url), "Esta página ya se está procesando."
        )

    def test_the_album_grid_links_to_each_page(self):
        """CP-12.1 — La página se abre desde la rejilla del álbum."""
        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, f'href="{self.page.get_absolute_url()}"')


class LiveRefreshTests(ProcessingTestCase):
    """CP-12.1 — El resultado aparece sin recargar la página a mano."""

    @mock.patch("albums.tasks.process_page_task")
    def test_a_processing_page_polls_its_status(self, task):
        """CP-12.1 — Mientras procesa, la vista consulta su estado sola."""
        self.process()

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(
            response, f'data-processing-poll="{self.page.get_status_url()}"'
        )

    def test_a_finished_page_stops_polling(self):
        """CP-12.1 — Flujo alternativo: una página terminada ya no consulta."""
        self.process()

        response = self.client.get(self.page.get_absolute_url())

        self.assertNotContains(response, "data-processing-poll")

    @mock.patch("albums.tasks.process_page_task")
    def test_the_status_reports_processing(self, task):
        """CP-12.1 — El estado indica que la detección sigue en curso."""
        self.process()

        state = self.client.get(self.page.get_status_url()).json()

        self.assertEqual(
            state,
            {
                "status": "processing",
                "is_processing": True,
                "is_translating": False,
                "region_count": 0,
            },
        )

    def test_the_status_reports_the_finished_result(self):
        """CP-12.1 — Al terminar, el estado indica cuántas regiones hay."""
        self.process()

        state = self.client.get(self.page.get_status_url()).json()

        self.assertEqual(
            state,
            {
                "status": "processed",
                "is_processing": False,
                "is_translating": False,
                "region_count": 2,
            },
        )

    def test_the_status_of_a_foreign_page_is_not_found(self):
        """CP-12.6 — El estado de una página ajena responde 404."""
        response = self.client.get(self.foreign_page.get_status_url())

        self.assertEqual(response.status_code, 404)


class RegionDisplayTests(ProcessingTestCase):
    """CP-12.2 — Ver las regiones detectadas."""

    def regions_in_page(self):
        """Devuelve las regiones de la página en el orden en que se numeraron."""
        return list(self.page.regions.order_by("reading_order"))

    def test_regions_are_highlighted_and_numbered(self):
        """CP-12.2 — Cada región se resalta sobre la imagen con su número."""
        self.process()

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, 'class="region-box region-box--balloon"', count=2)
        self.assertContains(
            response, 'aria-label="Región 1: globo de diálogo. Texto: こんにちは"'
        )
        self.assertContains(
            response, 'aria-label="Región 2: globo de diálogo. Texto: ありがとう"'
        )
        self.assertContains(response, 'href="#region-1"')
        self.assertContains(response, 'id="region-1"')

    def test_overlay_positions_use_a_dot_as_decimal_separator(self):
        """CP-12.2 — La posición es CSS válido aunque la interfaz use coma."""
        with use_provider(FakeOcrProvider(regions=[LEFT_BALLOON])):
            self.process()

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(
            response, "left: 10.000%; top: 7.143%; width: 30.000%; height: 14.286%;"
        )

    def test_japanese_pages_are_numbered_right_to_left(self):
        """CP-12.2 — En japonés la región de la derecha es la número 1."""
        with use_provider(FakeOcrProvider(regions=[LEFT_BALLOON, RIGHT_BALLOON])):
            self.process()

        first, second = self.regions_in_page()
        self.assertEqual(first.x, RIGHT_BALLOON.x)
        self.assertEqual(second.x, LEFT_BALLOON.x)

    def test_korean_pages_are_numbered_left_to_right(self):
        """CP-12.2 — Flujo alternativo: en coreano la de la izquierda es la 1."""
        self.album.source_language = Language.objects.get(code="ko")
        self.album.save()

        with use_provider(FakeOcrProvider(regions=[RIGHT_BALLOON, LEFT_BALLOON])):
            self.process()

        first, second = self.regions_in_page()
        self.assertEqual(first.x, LEFT_BALLOON.x)
        self.assertEqual(second.x, RIGHT_BALLOON.x)

    def test_an_unprocessed_page_says_so(self):
        """CP-12.2 — Flujo alternativo: una página sin procesar no muestra regiones."""
        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "Esta página aún no se ha procesado.")
        self.assertContains(response, "Procesar página")
        self.assertNotContains(response, "region-box--")


class PageWithoutTextTests(ProcessingTestCase):
    """CP-12.3 — Una página sin texto — Flujo alternativo."""

    def test_the_page_is_processed_with_zero_regions(self):
        """CP-12.3 — La página pasa a "Procesada" con 0 regiones."""
        with use_provider(FakeOcrProvider(regions=[])):
            response = self.process()

        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)
        self.assertEqual(self.page.regions.count(), 0)
        self.assertContains(
            self.client.get(response.url), "No se detectó texto en esta página."
        )


class DetectionFailureTests(ProcessingTestCase):
    """CP-12.4 — Falla el servicio de detección — Flujo alternativo."""

    def test_the_page_moves_to_error_with_a_retry_option(self):
        """CP-12.4 — Pasa a "Error" y se ofrece "Reintentar"."""
        with use_provider(FakeOcrProvider(error="El servicio no está disponible.")):
            response = self.process()

        self.assertEqual(self.page.status, ComicPage.Status.FAILED)
        self.assertEqual(self.page.processing_error, "El servicio no está disponible.")
        followed = self.client.get(response.url)
        self.assertContains(followed, "El servicio no está disponible.")
        self.assertContains(followed, "Reintentar")
        self.assertContains(followed, '<span class="badge badge--danger">')
        self.assertContains(followed, "No se pudo procesar esta página.")

    def test_the_album_grid_shows_the_error(self):
        """CP-12.4 — La rejilla del álbum muestra el chip "Error"."""
        with use_provider(FakeOcrProvider(error="Caído")):
            self.process()

        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "badge--danger")
        self.assertContains(response, "Error")

    def test_existing_regions_survive_a_failed_reprocess(self):
        """CP-12.4 — No se pierden los datos que la página ya tenía."""
        self.process()
        before = list(self.page.regions.values_list("x", "y", "width", "height"))

        with use_provider(FakeOcrProvider(error="Caído")):
            self.process(confirm="1")

        after = list(self.page.regions.values_list("x", "y", "width", "height"))
        self.assertEqual(after, before)
        self.assertEqual(self.page.status, ComicPage.Status.FAILED)
        self.assertContains(
            self.client.get(self.page.get_absolute_url()),
            "Se conservan las regiones de la última detección.",
        )

    def test_retrying_after_a_failure_clears_the_error(self):
        """CP-12.4 — Reintentar con el servicio repuesto termina bien."""
        with use_provider(FakeOcrProvider(error="Caído")):
            self.process()

        self.process()

        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)
        self.assertEqual(self.page.processing_error, "")

    def test_an_unexpected_error_does_not_leave_the_page_stuck(self):
        """CP-12.4 — Un fallo imprevisto también deja la página en "Error"."""
        broken = mock.Mock()
        broken.detect.side_effect = RuntimeError("fallo de programación")

        with use_provider(broken), self.assertLogs("albums.processing", "ERROR"):
            self.process()

        self.assertEqual(self.page.status, ComicPage.Status.FAILED)
        self.assertEqual(self.page.processing_error, UNEXPECTED_ERROR_MESSAGE)

    def test_a_stuck_page_can_be_retried(self):
        """CP-12.4 — Si el trabajador se cayó, la página no queda bloqueada."""
        self.page.status = ComicPage.Status.PROCESSING
        self.page.processing_started_at = timezone.now() - timedelta(hours=1)
        self.page.save()

        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, "El procesamiento tardó demasiado")
        self.assertContains(response, "Reintentar")
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, ComicPage.Status.FAILED)

        self.process()
        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)

    def test_a_late_result_does_not_overwrite_an_expired_page(self):
        """CP-12.4 — Si el trabajador termina tras caducar, no pisa el error."""
        self.page.status = ComicPage.Status.PROCESSING
        self.page.processing_started_at = timezone.now() - timedelta(hours=1)
        self.page.save()
        self.client.get(self.page.get_status_url())

        run_detection(self.page.pk)

        self.page.refresh_from_db()
        self.assertEqual(self.page.status, ComicPage.Status.FAILED)
        self.assertFalse(self.page.regions.exists())

    def test_a_task_for_a_deleted_page_does_nothing(self):
        """CP-12.4 — Si la página se borró mientras esperaba, la tarea no falla."""
        page_id = self.page.pk
        self.page.delete()

        run_detection(page_id)

        self.assertFalse(ComicPage.objects.filter(pk=page_id).exists())


class ReprocessTests(ProcessingTestCase):
    """CP-12.5 — Volver a procesar una página ya procesada."""

    def setUp(self):
        """Deja la página procesada con dos regiones."""
        super().setUp()
        self.process()
        self.original_ids = set(self.page.regions.values_list("pk", flat=True))

    def test_reprocessing_without_confirmation_changes_nothing(self):
        """CP-12.5 — Sin confirmar, se pide confirmación y no se toca nada."""
        response = self.process()

        self.assertRedirects(response, self.page.get_process_url())
        self.assertEqual(
            set(self.page.regions.values_list("pk", flat=True)), self.original_ids
        )
        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)

    def test_the_confirmation_page_explains_the_replacement(self):
        """CP-12.5 — La confirmación avisa de que se reemplazarán las regiones."""
        response = self.client.get(self.page.get_process_url())

        self.assertContains(response, "¿Volver a procesar esta página?")
        self.assertContains(response, "Se reemplazarán sus regiones de texto")
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)

    def test_the_detail_offers_the_confirmation_modal(self):
        """CP-12.5 — El detalle ofrece "Volver a procesar" con modal de confirmación."""
        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, 'data-modal-open="reprocesar-pagina"')
        self.assertContains(response, "¿Volver a procesar esta página?")

    def test_confirming_replaces_the_regions(self):
        """CP-12.5 — Al confirmar, las regiones se reemplazan."""
        with use_provider(FakeOcrProvider(regions=[LEFT_BALLOON])):
            self.process(confirm="1")

        self.assertEqual(self.page.regions.count(), 1)
        self.assertFalse(self.page.regions.filter(pk__in=self.original_ids).exists())


class OwnershipTests(ProcessingTestCase):
    """CP-12.6 — Solo se procesan páginas propias — Flujo alternativo."""

    def test_a_foreign_page_cannot_be_seen(self):
        """CP-12.6 — La vista de una página ajena responde 404."""
        response = self.client.get(self.foreign_page.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_a_foreign_page_cannot_be_processed(self):
        """CP-12.6 — Procesar una página ajena responde 404 y no la toca."""
        self.assertEqual(
            self.client.get(self.foreign_page.get_process_url()).status_code, 404
        )

        response = self.process(self.foreign_page, confirm="1")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.foreign_page.status, ComicPage.Status.PENDING)
        self.assertFalse(self.foreign_page.regions.exists())

    def test_anonymous_visitors_are_sent_to_login(self):
        """CP-12.6 — Sin sesión no se puede procesar ninguna página."""
        self.client.logout()

        response = self.client.post(self.page.get_process_url())

        self.assertEqual(response.status_code, 302)
        self.assertIn("/cuentas/ingresar/", response.url)
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, ComicPage.Status.PENDING)


class OcrTextTests(ProcessingTestCase):
    """HU-13 — Extraer el texto de las regiones con OCR."""

    def regions(self):
        """Devuelve las regiones guardadas, en orden de lectura."""
        return list(self.page.regions.order_by("reading_order"))

    def test_each_region_keeps_its_text_and_confidence(self):
        """CP-13.1 — Cada región guarda su texto y su confianza."""
        self.process()

        first, second = self.regions()
        self.assertEqual(first.source_text, "こんにちは")
        self.assertAlmostEqual(first.confidence, 0.97)
        self.assertEqual(first.confidence_percent, 97)
        self.assertEqual(second.source_text, "ありがとう")
        self.assertFalse(first.needs_review)

    def test_the_text_is_shown_in_the_source_language(self):
        """CP-13.1 — El texto se muestra en la página con su idioma."""
        self.process()

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, 'lang="ja"')
        self.assertContains(response, "こんにちは")
        self.assertContains(response, "97 % alta")

    def test_a_reliable_page_is_left_processed(self):
        """CP-13.3 — Sin regiones dudosas, la página queda "Procesada"."""
        self.process()

        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)

    def test_low_confidence_marks_the_region_and_the_page(self):
        """CP-13.3 — Una región dudosa deja la página en "Necesita revisión"."""
        doubtful = DetectedRegion(260, 50, 120, 80, "たぶん", 0.42)
        reliable = DetectedRegion(40, 40, 120, 80, "たしかに", 0.98)

        with use_provider(FakeOcrProvider(regions=[doubtful, reliable])):
            self.process()

        first, second = self.regions()
        self.assertTrue(first.needs_review)
        self.assertFalse(second.needs_review)
        self.assertEqual(self.page.status, ComicPage.Status.NEEDS_REVIEW)
        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, "1 necesita revisión.")
        self.assertContains(response, '<span class="badge badge--warning">')

    def test_text_in_another_script_needs_review(self):
        """CP-13.2 — En un álbum japonés, un texto solo en latín se revisa."""
        latin = DetectedRegion(260, 50, 120, 80, "Hello", 0.99)

        with use_provider(FakeOcrProvider(regions=[latin])):
            self.process()

        self.assertTrue(self.regions()[0].needs_review)
        self.assertEqual(self.page.status, ComicPage.Status.NEEDS_REVIEW)

    def test_a_region_without_text_keeps_the_rest(self):
        """CP-13.5 — Si falla el OCR de una región, el resto conserva su texto."""
        empty = DetectedRegion(260, 50, 120, 80, "", None)
        reliable = DetectedRegion(40, 40, 120, 80, "たしかに", 0.98)

        with use_provider(FakeOcrProvider(regions=[empty, reliable])):
            self.process()

        first, second = self.regions()
        self.assertEqual(first.source_text, "")
        self.assertTrue(first.needs_review)
        self.assertEqual(second.source_text, "たしかに")
        self.assertContains(
            self.client.get(self.page.get_absolute_url()), "Sin texto reconocido"
        )

    def test_the_text_survives_signing_out(self):
        """CP-13.1 — El texto queda guardado aunque se cierre sesión."""
        self.process()
        self.client.logout()
        self.client.login(email=self.owner.email, password=PASSWORD)

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "ありがとう")
