"""Pruebas de la traducción asistida por IA de una página (HU-16, ADR-002).

Ninguna prueba llama a Gemini: el proveedor se sustituye por el simulado, y
Huey corre en modo inmediato salvo donde se comprueba que la tarea se encola.
"""

from unittest import mock

from django.urls import reverse

from albums.models import ComicPage, TextRegion
from albums.tests.test_processing import ProcessingTestCase
from albums.translating import STALE_MESSAGE
from albums.translation.fake import FakeTranslationProvider


def use_translator(provider):
    """Sustituye el proveedor de traducción configurado por el indicado."""
    return mock.patch("albums.translating.get_translator", return_value=provider)


class TranslationTestCase(ProcessingTestCase):
    """Base: la página del álbum japonés ya procesada, con dos regiones."""

    def setUp(self):
        """Procesa la página con el OCR simulado: 「こんにちは」 y 「ありがとう」."""
        super().setUp()
        self.process()
        self.first, self.second = self.page.regions.order_by("reading_order")

    def translate(self, page=None, provider=None):
        """Pide traducir la página y ejecuta la tarea al confirmar."""
        page = page or self.page
        provider = provider or FakeTranslationProvider()
        with use_translator(provider), self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("albums:page_translate", args=[page.pk])
            )
        page.refresh_from_db()
        return response

    def retranslate(self, region, provider=None):
        """Pide volver a traducir una sola región."""
        provider = provider or FakeTranslationProvider()
        with use_translator(provider), self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(region.get_retranslate_url())
        region.refresh_from_db()
        return response

    def reload_regions(self):
        """Vuelve a leer las dos regiones de la base de datos."""
        self.first.refresh_from_db()
        self.second.refresh_from_db()


class TranslatePageTests(TranslationTestCase):
    """CP-16.1 — Traducir una página — Happy Path."""

    def test_each_region_gets_a_generated_proposal(self):
        """CP-16.1 — Cada región recibe su propuesta y queda "Generada"."""
        response = self.translate()

        self.reload_regions()
        self.assertRedirects(response, self.page.get_absolute_url())
        self.assertEqual(self.first.translation, "[ES] こんにちは")
        self.assertEqual(self.second.translation, "[ES] ありがとう")
        for region in (self.first, self.second):
            self.assertEqual(
                region.translation_status, TextRegion.TranslationStatus.GENERATED
            )
            self.assertEqual(region.machine_translation, region.translation)
            self.assertIsNotNone(region.translated_at)
        self.assertEqual(self.page.translation_state, ComicPage.TranslationState.IDLE)

    def test_the_workspace_shows_the_translation(self):
        """CP-16.1 — El bloque muestra la traducción con su estado."""
        self.translate()

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "ES · traducción")
        self.assertContains(response, "[ES] こんにちは")
        self.assertContains(response, "Generada")
        self.assertContains(response, "Traducir de nuevo")

    @mock.patch("albums.tasks.translate_page_task")
    def test_the_app_stays_usable_while_translating(self, task):
        """CP-16.1 — La traducción se encola y la página queda "Traduciendo"."""
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("albums:page_translate", args=[self.page.pk])
            )

        self.page.refresh_from_db()
        task.assert_called_once_with(self.page.pk, None)
        self.assertEqual(
            self.page.translation_state, ComicPage.TranslationState.TRANSLATING
        )
        followed = self.client.get(response.url)
        self.assertContains(followed, "Puedes seguir usando PaneLingo")
        self.assertContains(followed, "data-processing-poll")
        status = self.client.get(self.page.get_status_url()).json()
        self.assertTrue(status["is_translating"])

    @mock.patch("albums.tasks.translate_page_task")
    def test_a_second_click_does_not_queue_twice(self, task):
        """CP-16.1 — Pulsar dos veces no lanza dos traducciones."""
        url = reverse("albums:page_translate", args=[self.page.pk])
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url)
            self.client.post(url)

        task.assert_called_once()


class PageContextTests(TranslationTestCase):
    """CP-16.2 — Se envía el contexto de la página, no frases sueltas."""

    def test_all_regions_travel_in_reading_order_with_their_kind(self):
        """CP-16.2 — El servicio recibe todas las regiones, en orden y con tipo."""
        provider = FakeTranslationProvider()

        self.translate(provider=provider)

        request = provider.last_request
        self.assertEqual(request.source_language, "Japonés")
        self.assertEqual(request.target_language, "Español")
        self.assertEqual([region.number for region in request.regions], [1, 2])
        self.assertEqual(
            [region.text for region in request.regions], ["こんにちは", "ありがとう"]
        )
        self.assertEqual(request.regions[0].kind, "Globo de diálogo")

    def test_the_corrected_text_is_the_one_translated(self):
        """CP-16.2 — Se traduce el texto corregido en HU-15 (CA-15.2)."""
        self.client.post(self.first.get_correct_url(), {"text": "こんばんは"})
        provider = FakeTranslationProvider()

        self.translate(provider=provider)

        self.first.refresh_from_db()
        self.assertEqual(provider.last_request.regions[0].text, "こんばんは")
        self.assertEqual(self.first.translation, "[ES] こんばんは")

    def test_a_region_without_text_is_not_sent(self):
        """CP-16.2 — Una región vaciada a propósito no viaja ni se traduce."""
        self.client.post(self.first.get_correct_url(), {"text": ""})
        provider = FakeTranslationProvider()

        self.translate(provider=provider)

        self.first.refresh_from_db()
        self.assertEqual(
            [region.number for region in provider.last_request.regions], [2]
        )
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.UNTRANSLATED
        )


class ApprovedTranslationTests(TranslationTestCase):
    """CP-16.3 — No se pisan las traducciones aprobadas."""

    def setUp(self):
        """Traduce la página y aprueba la región 2."""
        super().setUp()
        self.translate()
        self.second.refresh_from_db()
        self.second.translation = "Gracias."
        self.second.translation_status = TextRegion.TranslationStatus.APPROVED
        self.second.save()

    def test_translating_again_keeps_the_approved_region(self):
        """CP-16.3 — La región aprobada conserva su traducción."""
        provider = FakeTranslationProvider()

        self.translate(provider=provider)

        self.reload_regions()
        self.assertEqual(self.second.translation, "Gracias.")
        self.assertEqual(
            self.second.translation_status, TextRegion.TranslationStatus.APPROVED
        )
        self.assertEqual(provider.last_request.numbers_to_translate, [1])

    def test_the_approved_region_still_travels_as_context(self):
        """CP-16.3 — La aprobada viaja como contexto, sin pedir su traducción."""
        provider = FakeTranslationProvider()

        self.translate(provider=provider)

        approved = provider.last_request.regions[1]
        self.assertEqual(approved.number, 2)
        self.assertFalse(approved.translate)

    def test_an_approved_region_cannot_be_retranslated(self):
        """CP-16.3 — "Reintentar con IA" no toca una región aprobada."""
        self.retranslate(self.second)

        self.assertEqual(self.second.translation, "Gracias.")


class RetryRegionTests(TranslationTestCase):
    """CP-16.1 — "Reintentar con IA" en una sola región (Retry AI del mockup)."""

    def test_only_that_region_changes(self):
        """CP-16.1 — Solo cambia la región pedida, con la página como contexto."""
        self.translate()
        self.first.refresh_from_db()
        self.first.translation = "Hola."
        self.first.save()
        provider = FakeTranslationProvider()

        self.retranslate(self.second, provider)

        self.first.refresh_from_db()
        self.assertEqual(self.first.translation, "Hola.")
        self.assertEqual(self.second.translation, "[ES] ありがとう")
        self.assertEqual(provider.last_request.numbers_to_translate, [2])
        self.assertEqual(len(provider.last_request.regions), 2)


class TranslationFailureTests(TranslationTestCase):
    """CP-16.4 — Falla el servicio de IA — Flujo alternativo."""

    def test_the_error_is_shown_with_retry(self):
        """CP-16.4 — Se muestra el error con la opción "Reintentar"."""
        provider = FakeTranslationProvider(
            error="El servicio de traducción no está disponible."
        )

        response = self.translate(provider=provider)

        self.assertTrue(self.page.translation_failed)
        followed = self.client.get(response.url)
        self.assertContains(followed, "El servicio de traducción no está disponible.")
        self.assertContains(followed, "Reintentar")

    def test_existing_translations_are_not_lost(self):
        """CP-16.4 — Las traducciones que ya existían se conservan."""
        self.translate()
        provider = FakeTranslationProvider(error="Fallo simulado.")

        self.translate(provider=provider)

        self.reload_regions()
        self.assertEqual(self.first.translation, "[ES] こんにちは")
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.GENERATED
        )

    def test_retrying_after_a_failure_translates(self):
        """CP-16.4 — Reintentar con el servicio ya disponible traduce la página."""
        self.translate(provider=FakeTranslationProvider(error="Fallo simulado."))

        self.translate()

        self.first.refresh_from_db()
        self.assertFalse(self.page.translation_failed)
        self.assertEqual(self.first.translation, "[ES] こんにちは")

    def test_an_incomplete_answer_keeps_the_missing_region_untranslated(self):
        """CP-16.4 — Si la IA omite una región, esa queda "Sin traducir"."""
        self.translate(provider=FakeTranslationProvider(skip={2}))

        self.reload_regions()
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.GENERATED
        )
        self.assertEqual(
            self.second.translation_status, TextRegion.TranslationStatus.UNTRANSLATED
        )

    @mock.patch("albums.tasks.translate_page_task")
    def test_a_stuck_translation_ends_in_error(self, task):
        """CP-16.4 — Una traducción colgada pasa a error al abrir la página."""
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("albums:page_translate", args=[self.page.pk]))
        ComicPage.objects.filter(pk=self.page.pk).update(
            translation_started_at=self.page.created_at.replace(year=2000)
        )

        response = self.client.get(self.page.get_absolute_url())

        self.page.refresh_from_db()
        self.assertTrue(self.page.translation_failed)
        self.assertContains(response, STALE_MESSAGE)

    def test_an_unexpected_error_does_not_block_the_page(self):
        """CP-16.4 — Un fallo inesperado deja la página con error, no colgada."""
        provider = mock.Mock()
        provider.translate.side_effect = RuntimeError("fallo")

        self.translate(provider=provider)

        self.assertTrue(self.page.translation_failed)


class NothingToTranslateTests(ProcessingTestCase):
    """CP-16.5 — Página sin texto de origen — Flujo alternativo."""

    def test_an_unprocessed_page_cannot_be_translated(self):
        """CP-16.5 — Sin regiones no se ofrece traducir y el POST no encola."""
        with mock.patch("albums.tasks.translate_page_task") as task:
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(reverse("albums:page_translate", args=[self.page.pk]))

        task.assert_not_called()
        self.page.refresh_from_db()
        self.assertEqual(self.page.translation_state, ComicPage.TranslationState.IDLE)

    def test_a_page_without_text_explains_why(self):
        """CP-16.5 — Página procesada sin texto: botón deshabilitado con motivo."""
        ComicPage.objects.filter(pk=self.page.pk).update(
            status=ComicPage.Status.PROCESSED
        )

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "esta página no tiene texto que traducir")
        self.assertNotContains(response, self.page.get_translate_url())

    def test_regions_left_empty_on_purpose_disable_the_button(self):
        """CP-16.5 — Si todas las regiones están vacías, no hay nada que traducir."""
        self.process()
        for region in self.page.regions.all():
            self.client.post(region.get_correct_url(), {"text": ""})

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "no hay texto pendiente de traducir")


class NoStyleSelectorTests(TranslationTestCase):
    """CP-16.6 — Sin selector de estilo de traducción."""

    def test_translating_asks_for_no_style(self):
        """CP-16.6 — Se traduce sin pedir un tipo o estilo de traducción."""
        response = self.client.get(self.page.get_absolute_url())

        self.assertNotContains(response, "<select")
        self.assertNotContains(response, 'name="style"')
        self.translate()
        self.first.refresh_from_db()
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.GENERATED
        )


class TranslationAccessTests(TranslationTestCase):
    """Aislamiento: una página o región ajena no se puede traducir."""

    def test_a_foreign_page_is_not_found(self):
        """Traducir una página de otra cuenta responde 404."""
        response = self.client.post(
            reverse("albums:page_translate", args=[self.foreign_page.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_a_foreign_region_is_not_found(self):
        """Volver a traducir una región de otra cuenta responde 404."""
        foreign = TextRegion.objects.create(
            page=self.foreign_page,
            reading_order=1,
            x=0,
            y=0,
            width=10,
            height=10,
            source_text="よそ",
        )

        response = self.client.post(foreign.get_retranslate_url())

        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.translation, "")


class ReprocessWarningTests(TranslationTestCase):
    """ADR-002, T6: volver a procesar avisa de las traducciones que se pierden."""

    def test_the_confirmation_mentions_the_translations(self):
        """El aviso de volver a procesar cuenta las traducciones."""
        self.translate()

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "También se borrarán 2 traducciones.")
