"""Pruebas de la aprobación de traducciones (HU-19)."""

from django.urls import reverse

from albums.models import ComicPage, TextRegion
from albums.tests.test_processing import PASSWORD
from albums.tests.test_translation_review import ReviewTestCase


class ApprovalTestCase(ReviewTestCase):
    """Base: página traducida con dos regiones "Generadas"."""

    def post_approve(self, region, **data):
        """Pulsa "Aprobar" en la región y vuelve a leerla."""
        response = self.client.post(region.get_approve_url(), data)
        region.refresh_from_db()
        self.page.refresh_from_db()
        return response

    def post_unapprove(self, region):
        """Pulsa "Retirar aprobación" en la región y vuelve a leerla."""
        response = self.client.post(region.get_unapprove_url())
        region.refresh_from_db()
        self.page.refresh_from_db()
        return response


class ApproveRegionTests(ApprovalTestCase):
    """CP-19.1 — Aprobar una región — Happy Path."""

    def test_the_region_is_approved_with_its_date(self):
        """CP-19.1 — La región queda "Aprobada", con la fecha de aprobación."""
        self.post_approve(self.first)

        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.APPROVED
        )
        self.assertIsNotNone(self.first.approved_at)

    def test_the_pending_counter_goes_down(self):
        """CP-19.1 — El contador de pendientes disminuye en 1."""
        self.post_approve(self.first)

        response = self.workspace()

        self.assertContains(response, "<strong>1 traducción</strong>", html=False)
        self.assertContains(response, "1/2 aprobadas")
        self.assertContains(response, "Aprobada el")

    def test_approving_jumps_to_the_next_unapproved_region(self):
        """CP-19.1 — Aprobar pasa a la siguiente región sin aprobar (T2)."""
        response = self.post_approve(self.first)

        self.assertRedirects(
            response,
            f"{self.page.get_absolute_url()}#region-2",
            fetch_redirect_response=False,
        )
        followed = self.client.get(response.url)
        self.assertContains(followed, "Región 1 aprobada.")

    def test_the_written_text_is_saved_when_approving(self):
        """CP-19.1 — Lo escrito en el campo se guarda al aprobar."""
        self.post_approve(self.first, text="¡Hola!")

        self.assertEqual(self.first.translation, "¡Hola!")
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.APPROVED
        )
        self.assertEqual(self.first.machine_translation, "[ES] こんにちは")

    def test_ctrl_enter_is_offered_as_a_shortcut(self):
        """CP-19.1 — "Aprobar" indica el atajo Ctrl+Enter."""
        response = self.workspace()

        self.assertContains(response, "Aprobar y pasar a la siguiente (Ctrl+Enter)")
        self.assertContains(response, "data-approve", count=2)


class PageApprovalTests(ApprovalTestCase):
    """CP-19.2 — La página queda aprobada cuando todas sus regiones lo están."""

    def test_approving_the_last_region_approves_the_page(self):
        """CP-19.2 — Al aprobar la última pendiente, la página pasa a "Aprobada"."""
        self.post_approve(self.first)
        self.assertNotEqual(self.page.status, ComicPage.Status.APPROVED)

        response = self.post_approve(self.second)

        self.assertEqual(self.page.status, ComicPage.Status.APPROVED)
        followed = self.client.get(response.url)
        self.assertContains(followed, "página aprobada")
        self.assertContains(followed, "2/2 aprobadas")

    def test_regions_without_text_do_not_block_the_approval(self):
        """CP-19.2 — Una región vaciada a propósito no impide aprobar la página."""
        self.client.post(self.second.get_correct_url(), {"text": ""})

        self.post_approve(self.first)

        self.assertEqual(self.page.status, ComicPage.Status.APPROVED)

    def test_an_empty_translation_can_be_approved(self):
        """CP-19.2 — "Se deja sin traducir" es una decisión aprobable (T1)."""
        self.edit(self.second, "")

        self.post_approve(self.first)
        self.post_approve(self.second)

        self.assertEqual(self.page.status, ComicPage.Status.APPROVED)


class NoTranslationTests(ApprovalTestCase):
    """CP-19.3 — No se aprueba una región sin traducción — Flujo alternativo."""

    def setUp(self):
        """Deja la región 2 sin traducir."""
        super().setUp()
        TextRegion.objects.filter(pk=self.second.pk).update(
            translation="",
            machine_translation="",
            translation_status=TextRegion.TranslationStatus.UNTRANSLATED,
        )

    def test_approve_is_disabled_with_its_reason(self):
        """CP-19.3 — "Aprobar" no está disponible y se explica el motivo."""
        response = self.workspace()

        self.assertContains(response, "data-approve-pending")
        self.assertContains(response, 'aria-describedby="approve-hint-2"')
        self.assertContains(response, "Para aprobarla necesita una traducción")

    def test_the_server_refuses_it_too(self):
        """CP-19.3 — Aunque se envíe, la región sin traducción no se aprueba."""
        response = self.post_approve(self.second)

        self.assertEqual(
            self.second.translation_status, TextRegion.TranslationStatus.UNTRANSLATED
        )
        followed = self.client.get(response.url)
        self.assertContains(followed, "todavía no tiene traducción que aprobar")

    def test_writing_a_translation_and_approving_works(self):
        """CP-19.3 — Escrita una traducción, ya se puede aprobar."""
        self.post_approve(self.second, text="Gracias.")

        self.assertEqual(self.second.translation, "Gracias.")
        self.assertEqual(
            self.second.translation_status, TextRegion.TranslationStatus.APPROVED
        )


class WithdrawApprovalTests(ApprovalTestCase):
    """CP-19.4 — Retirar una aprobación — Flujo alternativo."""

    def setUp(self):
        """Aprueba las dos regiones: la página queda "Aprobada"."""
        super().setUp()
        self.post_approve(self.first)
        self.post_approve(self.second)

    def test_the_region_goes_back_to_edited(self):
        """CP-19.4 — La región vuelve a "Editada" y pierde la fecha."""
        response = self.post_unapprove(self.first)

        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.EDITED
        )
        self.assertIsNone(self.first.approved_at)
        followed = self.client.get(response.url)
        self.assertContains(followed, "Se retiró la aprobación de la región 1.")

    def test_the_page_stops_being_approved(self):
        """CP-19.4 — La página deja de estar "Aprobada"."""
        self.post_unapprove(self.first)

        self.assertEqual(self.page.status, ComicPage.Status.PROCESSED)

    def test_an_approved_region_offers_to_withdraw(self):
        """CP-19.4 — La región aprobada ofrece "Retirar aprobación"."""
        response = self.workspace()

        self.assertContains(response, "Retirar aprobación", count=2)
        self.assertNotContains(response, "data-approve")


class ApprovalPersistsTests(ApprovalTestCase):
    """CP-19.5 — La aprobación se conserva."""

    def test_the_approval_survives_logging_out(self):
        """CP-19.5 — Tras cerrar sesión y volver, sigue "Aprobada"."""
        self.post_approve(self.first)
        self.client.logout()

        self.client.login(email=self.owner.email, password=PASSWORD)
        response = self.workspace()

        self.first.refresh_from_db()
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.APPROVED
        )
        self.assertContains(response, "Aprobada el")


class ApprovalAccessTests(ApprovalTestCase):
    """Aislamiento: no se aprueba ni se retira en una región ajena."""

    def test_foreign_regions_are_not_found(self):
        """Aprobar o retirar en una región de otra cuenta responde 404."""
        foreign = TextRegion.objects.create(
            page=self.foreign_page,
            reading_order=1,
            x=0,
            y=0,
            width=10,
            height=10,
            source_text="よそ",
            translation="ajena",
            translation_status=TextRegion.TranslationStatus.GENERATED,
        )

        for name in ("albums:region_approve", "albums:region_unapprove"):
            with self.subTest(name=name):
                response = self.client.post(reverse(name, args=[foreign.pk]))
                self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(
            foreign.translation_status, TextRegion.TranslationStatus.GENERATED
        )
