"""Pruebas de la revisión y edición de traducciones (HU-17 y HU-18).

Se fusionan en la misma pantalla, el espacio de trabajo (ADR-002, T3).
"""

from unittest import mock

from django.urls import reverse

from albums.models import ComicPage, TextRegion
from albums.tests.test_translation import TranslationTestCase


class ReviewTestCase(TranslationTestCase):
    """Base: la página procesada y traducida con el proveedor simulado."""

    def setUp(self):
        """Traduce la página: dos regiones "Generadas"."""
        super().setUp()
        self.translate()
        self.reload_regions()

    def edit(self, region, text):
        """Guarda una traducción editada y vuelve a leer la región."""
        response = self.client.post(region.get_translation_url(), {"text": text})
        region.refresh_from_db()
        return response

    def approve(self, region):
        """Deja la región aprobada (HU-19 añadirá el botón)."""
        region.translation_status = TextRegion.TranslationStatus.APPROVED
        region.save(update_fields=["translation_status"])

    def workspace(self, **params):
        """Abre el espacio de trabajo con los parámetros indicados."""
        return self.client.get(self.page.get_absolute_url(), params)


class CompareTests(ReviewTestCase):
    """CP-17.1 — Comparar el origen con la traducción — Happy Path."""

    def test_source_and_translation_are_side_by_side(self):
        """CP-17.1 — Cada bloque muestra el origen y su traducción juntos."""
        response = self.workspace()

        self.assertContains(response, "JA · texto de origen")
        self.assertContains(response, "ES · traducción")
        self.assertContains(response, ">こんにちは</textarea>", html=False)
        self.assertContains(response, ">[ES] こんにちは</textarea>", html=False)

    def test_each_block_is_linked_to_its_region_on_the_image(self):
        """CP-17.1 — El bloque enlaza con su región, que se resalta en la imagen."""
        response = self.workspace()

        self.assertContains(response, 'href="#region-box-1" data-region="1"')
        self.assertContains(response, 'id="region-box-1"')


class StepThroughTests(ReviewTestCase):
    """CP-17.2 — Recorrer las traducciones."""

    def test_previous_and_next_are_offered_with_their_shortcuts(self):
        """CP-17.2 — Hay "Anterior" y "Siguiente", con Alt+↑ y Alt+↓."""
        response = self.workspace()

        self.assertContains(response, 'data-region-step="1"')
        self.assertContains(response, 'data-region-step="-1"')
        self.assertContains(response, "Región siguiente (Alt+↓)")

    def test_the_blocks_follow_the_reading_order(self):
        """CP-17.2 — Los bloques se recorren en orden de lectura."""
        content = self.workspace().content.decode()

        self.assertLess(
            content.index('data-region-item="1"'), content.index('data-region-item="2"')
        )


class PendingApprovalTests(ReviewTestCase):
    """CP-17.3 — Identificar lo que falta por aprobar."""

    def test_each_block_shows_its_status(self):
        """CP-17.3 — Cada región muestra "Generada", "Editada" o "Aprobada"."""
        self.edit(self.first, "Hola.")
        self.approve(self.second)

        response = self.workspace()

        self.assertContains(response, "Editada")
        self.assertContains(response, "Aprobada")

    def test_the_counter_shows_how_many_are_left(self):
        """CP-17.3 — Se ve cuántas regiones faltan por aprobar."""
        self.approve(self.second)

        response = self.workspace()

        self.assertContains(response, "<strong>1 traducción</strong>", html=False)
        self.assertContains(response, "sin aprobar de 2")

    def test_the_filter_shows_only_unapproved_regions(self):
        """CP-17.3 — "Sin aprobar" deja solo las regiones sin aprobar."""
        self.approve(self.second)

        response = self.workspace(filtro="sin-aprobar")

        self.assertContains(response, "Sin aprobar (1)")
        self.assertContains(response, 'data-region-item="1"')
        self.assertNotContains(response, 'data-region-item="2"')

    def test_with_everything_approved_the_counter_says_so(self):
        """CP-17.3 — Con todo aprobado, el contador lo dice."""
        self.approve(self.first)
        self.approve(self.second)

        response = self.workspace()

        self.assertContains(response, "Todas las traducciones están aprobadas.")


class ReviewChangesNothingTests(ReviewTestCase):
    """CP-17.4 — Revisar no cambia nada por sí solo."""

    def test_browsing_and_filtering_change_no_text_or_status(self):
        """CP-17.4 — Recorrer y filtrar no cambia textos ni estados."""
        before = list(
            TextRegion.objects.values_list("translation", "translation_status")
        )

        self.workspace()
        self.workspace(filtro="sin-aprobar")
        self.workspace(filtro="revisar")

        after = list(
            TextRegion.objects.values_list("translation", "translation_status")
        )
        self.assertEqual(before, after)


class EditTranslationTests(ReviewTestCase):
    """CP-18.1 — Editar y guardar una traducción — Happy Path."""

    def test_the_edited_text_is_saved_as_edited(self):
        """CP-18.1 — Se guarda el texto editado y la región queda "Editada"."""
        response = self.edit(self.first, "¡Hola! ¿Cómo estás?")

        self.assertRedirects(
            response,
            f"{self.page.get_absolute_url()}#region-1",
            fetch_redirect_response=False,
        )
        self.assertEqual(self.first.translation, "¡Hola! ¿Cómo estás?")
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.EDITED
        )

    def test_the_ai_proposal_is_kept_and_can_be_seen(self):
        """CP-18.1 — La propuesta de la IA se conserva y se puede consultar."""
        self.edit(self.first, "¡Hola!")

        response = self.workspace()

        self.assertEqual(self.first.machine_translation, "[ES] こんにちは")
        self.assertContains(response, "Ver propuesta de la IA")
        self.assertContains(response, "[ES] こんにちは</p>", html=False)

    def test_a_confirmation_is_shown(self):
        """CP-18.1 — Se confirma que la traducción quedó guardada."""
        response = self.edit(self.first, "¡Hola!")

        followed = self.client.get(response.url)
        self.assertContains(followed, "Se guardó la traducción de la región 1.")

    def test_a_translation_can_be_written_by_hand(self):
        """CP-18.1 — En una región sin traducir se puede escribir la propia."""
        TextRegion.objects.filter(pk=self.first.pk).update(
            translation="",
            machine_translation="",
            translation_status=TextRegion.TranslationStatus.UNTRANSLATED,
        )

        self.edit(self.first, "Buenas tardes.")

        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.EDITED
        )
        self.assertEqual(self.first.machine_translation, "")

    def test_unsaved_edits_trigger_the_leave_warning(self):
        """CP-18.1 — Una traducción sin guardar avisa al salir (como CA-15.4)."""
        response = self.workspace()

        self.assertContains(response, 'class="block-card__translation"')
        self.assertContains(response, "data-region-edit", count=4)

    def test_nothing_is_saved_while_the_page_is_translating(self):
        """CP-18.1 — Mientras la IA traduce no se guarda: podría pisarse."""
        ComicPage.objects.filter(pk=self.page.pk).update(
            translation_state=ComicPage.TranslationState.TRANSLATING,
            translation_started_at=self.page.updated_at,
        )

        with mock.patch("albums.models.ComicPage.is_translation_stale", new=False):
            response = self.edit(self.first, "¡Hola!")

        self.assertEqual(self.first.translation, "[ES] こんにちは")
        followed = self.client.get(response.url)
        self.assertContains(followed, "La página se está traduciendo.")


class EditApprovedTests(ReviewTestCase):
    """CP-18.2 — Editar una traducción ya aprobada."""

    def test_an_edited_approved_region_needs_approval_again(self):
        """CP-18.2 — La región aprobada vuelve a "Editada"."""
        self.approve(self.second)

        self.edit(self.second, "Muchas gracias.")

        self.assertEqual(
            self.second.translation_status, TextRegion.TranslationStatus.EDITED
        )
        self.assertIsNone(self.second.approved_at)

    def test_the_page_stops_being_approved(self):
        """CP-18.2 — Si la página estaba aprobada, deja de estarlo."""
        self.approve(self.first)
        self.approve(self.second)
        ComicPage.objects.filter(pk=self.page.pk).update(
            status=ComicPage.Status.APPROVED
        )

        self.edit(self.second, "Muchas gracias.")

        self.page.refresh_from_db()
        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)


class FormattingTests(ReviewTestCase):
    """CP-18.3 — Se respeta el formato del texto."""

    def test_line_breaks_and_spanish_signs_are_kept_exactly(self):
        """CP-18.3 — Saltos de línea, ¿ ¡ y puntos suspensivos, tal cual."""
        text = "¿Qué haces?\n¡Baja ya!…\n¡¿En serio?!"

        self.edit(self.first, text.replace("\n", "\r\n"))

        self.assertEqual(self.first.translation, text)
        response = self.workspace()
        self.assertContains(response, f">{text}</textarea>", html=False)


class EmptyTranslationTests(ReviewTestCase):
    """CP-18.4 — Traducción vacía — Flujo alternativo (ADR-002, T1)."""

    def test_an_empty_translation_is_accepted_as_left_untranslated(self):
        """CP-18.4 — Se acepta y la región se deja sin traducir."""
        response = self.edit(self.first, "   \n ")

        self.assertEqual(self.first.translation, "")
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.EDITED
        )
        followed = self.client.get(response.url)
        self.assertContains(followed, "La región 1 se deja sin traducir.")
        self.assertContains(followed, 'placeholder="Se deja sin traducir."')


class ReviewAccessTests(ReviewTestCase):
    """Aislamiento: la traducción de otra cuenta no se puede editar."""

    def test_a_foreign_region_is_not_found(self):
        """Editar la traducción de una región ajena responde 404."""
        foreign = TextRegion.objects.create(
            page=self.foreign_page,
            reading_order=1,
            x=0,
            y=0,
            width=10,
            height=10,
            source_text="よそ",
        )

        response = self.client.post(
            reverse("albums:region_translation_edit", args=[foreign.pk]),
            {"text": "cambio"},
        )

        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.translation, "")
