"""Pruebas para continuar un trabajo guardado (HU-24)."""

from datetime import timedelta

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from albums.models import ComicPage, TextRegion
from albums.tests.test_library_progress import add_pages, add_region, set_status
from albums.tests.test_processing import PASSWORD, ProcessingTestCase


class ResumeWorkTestCase(ProcessingTestCase):
    """Base con utilidades para preparar un último punto trabajado."""

    def make_page_seven_with_work(self):
        """Crea la página siete y deja la región tres como la última editada."""
        set_status(self.page, ComicPage.Status.APPROVED)
        pages = add_pages(
            self.album,
            [ComicPage.Status.APPROVED] * 5 + [ComicPage.Status.PROCESSED],
        )
        page_seven = pages[-1]
        first = add_region(page_seven, 1)
        add_region(page_seven, 2)
        third = add_region(page_seven, 3)
        now = timezone.now()
        TextRegion.objects.filter(pk=first.pk).update(
            is_corrected=True,
            corrected_text="Trabajo anterior",
            corrected_at=now - timedelta(minutes=5),
        )
        TextRegion.objects.filter(pk=third.pk).update(
            translation="Última traducción guardada",
            translation_status=TextRegion.TranslationStatus.EDITED,
            translated_at=now,
        )
        third.refresh_from_db()
        return page_seven, third


class ResumeLastPointTests(ResumeWorkTestCase):
    """CP-24.1 — Retomar desde el último punto guardado — Happy path."""

    def test_continue_opens_the_last_page_and_region(self):
        """CP-24.1 — Continuar apunta a la página siete y la región tres."""
        page, region = self.make_page_seven_with_work()

        response = self.client.get(reverse("albums:list"))

        expected = f"{page.get_absolute_url()}#region-{region.reading_order}"
        self.assertContains(response, 'class="album-card__continue"')
        self.assertContains(response, f'href="{expected}"')
        self.assertContains(response, "Continuar")

    def test_generated_translation_is_not_mistaken_for_manual_work(self):
        """CP-24.1 — Una propuesta automática no reemplaza el último punto manual."""
        page, third = self.make_page_seven_with_work()
        generated = page.regions.get(reading_order=2)
        TextRegion.objects.filter(pk=generated.pk).update(
            translation="Propuesta automática",
            translation_status=TextRegion.TranslationStatus.GENERATED,
            translated_at=timezone.now() + timedelta(minutes=1),
        )

        response = self.client.get(reverse("albums:list"))

        expected = f"{page.get_absolute_url()}#region-{third.reading_order}"
        self.assertContains(response, f'href="{expected}"')


class ResumeAcrossSessionsTests(ResumeWorkTestCase):
    """CP-24.2 — Recuperar el trabajo en otra sesión o dispositivo."""

    def test_another_session_recovers_text_status_and_resume_link(self):
        """CP-24.2 — Una sesión nueva encuentra los mismos datos y destino."""
        page, region = self.make_page_seven_with_work()
        other_session = Client()
        self.assertTrue(other_session.login(email=self.owner.email, password=PASSWORD))

        library = other_session.get(reverse("albums:list"))
        workspace = other_session.get(page.get_absolute_url())

        expected = f"{page.get_absolute_url()}#region-{region.reading_order}"
        self.assertContains(library, f'href="{expected}"')
        self.assertContains(workspace, "Última traducción guardada")
        self.assertContains(workspace, "Editada")


class ResumeFallbackTests(ResumeWorkTestCase):
    """CP-24.3 y CP-24.4 — Destinos alternativos seguros."""

    def test_album_without_previous_work_opens_first_unapproved_page(self):
        """CP-24.3 — Sin ediciones, Continuar abre la primera no aprobada."""
        response = self.client.get(reverse("albums:list"))

        self.assertContains(
            response,
            f'href="{self.page.get_absolute_url()}"',
        )
        self.assertContains(response, 'class="album-card__continue"')

    def test_deleted_last_page_falls_back_without_errors(self):
        """CP-24.4 — Si el último punto desaparece, abre la primera pendiente."""
        set_status(self.page, ComicPage.Status.PENDING)
        page, _region = self.make_page_seven_with_work()
        set_status(self.page, ComicPage.Status.PENDING)
        page.delete()

        response = self.client.get(reverse("albums:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'class="album-card__continue" href="{self.page.get_absolute_url()}"',
        )

    def test_empty_and_completed_albums_do_not_offer_continue(self):
        """CP-24.3 — El botón solo aparece cuando existe trabajo pendiente."""
        empty = self.make_album(self.owner, "ja")
        empty.title = "Álbum vacío"
        empty.save(update_fields=["title", "updated_at"])
        set_status(self.page, ComicPage.Status.APPROVED)

        response = self.client.get(reverse("albums:list"))

        self.assertNotContains(response, 'class="album-card__continue"')


class ResumeAccessTests(ResumeWorkTestCase):
    """CP-24 — El punto para continuar respeta el propietario."""

    def test_foreign_work_is_not_listed_and_its_page_returns_not_found(self):
        """CP-24.2 — Otra cuenta no puede ver ni abrir el punto guardado."""
        region = add_region(self.foreign_page, 1)
        TextRegion.objects.filter(pk=region.pk).update(
            is_corrected=True,
            corrected_text="Privado",
            corrected_at=timezone.now(),
        )

        response = self.client.get(reverse("albums:list"))
        foreign = self.client.get(self.foreign_page.get_absolute_url())

        self.assertNotContains(response, self.foreign_page.get_absolute_url())
        self.assertEqual(foreign.status_code, 404)
