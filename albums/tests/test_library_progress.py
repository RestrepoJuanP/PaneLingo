"""Pruebas del progreso calculado: estado derivado, filtros y resúmenes.

Cubren lo que alimenta la biblioteca, el detalle del álbum y la barra lateral
del mockup (HU-22, HU-26): todas las cifras salen de páginas y regiones.
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from albums.insights import (
    AlbumProgress,
    derive_status,
    library_for,
    page_card,
    pages_with_progress,
    resume_page,
    time_greeting,
    with_progress,
)
from albums.models import Album, ComicPage, TextRegion
from albums.tests.test_processing import ProcessingTestCase


def add_region(page, order, needs_review=False):
    """Crea una región en la página, dudosa o no."""
    return TextRegion.objects.create(
        page=page,
        reading_order=order,
        x=0,
        y=0,
        width=10,
        height=10,
        source_text="テキスト",
        confidence=0.4 if needs_review else 0.95,
        needs_review=needs_review,
    )


def set_status(page, status):
    """Cambia el estado de una página sin pasar por el procesamiento."""
    ComicPage.objects.filter(pk=page.pk).update(status=status)
    page.refresh_from_db()


class DerivedStatusTests(ProcessingTestCase):
    """CA-26.1 — El estado del álbum se deriva de sus páginas."""

    def progress(self):
        """Progreso del álbum de la prueba."""
        return AlbumProgress.of(
            with_progress(Album.objects.filter(pk=self.album.pk)).get()
        )

    def test_status_follows_the_pages(self):
        """CA-26.1 — Borrador, en progreso, en revisión y completado."""
        self.assertEqual(derive_status(0, 0, 0).key, "draft")
        self.assertEqual(self.progress().status.key, "in_progress")

        set_status(self.page, ComicPage.Status.NEEDS_REVIEW)
        add_region(self.page, 1, needs_review=True)
        self.assertEqual(self.progress().status.key, "in_review")

        set_status(self.page, ComicPage.Status.APPROVED)
        self.assertEqual(self.progress().status.key, "completed")

    def test_processed_but_not_approved_is_in_review(self):
        """CA-26.1 — Todo procesado, pero sin aprobar: en revisión."""
        set_status(self.page, ComicPage.Status.PROCESSED)
        second = self.make_page(self.album)
        set_status(second, ComicPage.Status.APPROVED)

        self.assertEqual(self.progress().status.key, "in_review")

        set_status(self.page, ComicPage.Status.APPROVED)
        self.assertEqual(self.progress().status.key, "completed")

    def test_the_percentages_count_regions(self):
        """CA-26.1 — Listas y por revisar se cuentan por regiones."""
        set_status(self.page, ComicPage.Status.NEEDS_REVIEW)
        add_region(self.page, 1)
        add_region(self.page, 2)
        add_region(self.page, 3, needs_review=True)
        add_region(self.page, 4, needs_review=True)

        progress = self.progress()

        self.assertEqual(progress.percent_ready, 50)
        self.assertEqual(progress.percent_review, 50)
        self.assertEqual(progress.page_done, 1)

    def test_the_library_never_includes_foreign_albums(self):
        """Aislamiento: library_for solo devuelve álbumes propios."""
        self.assertEqual(list(library_for(self.owner)), [self.album])


class LibraryFilterTests(ProcessingTestCase):
    """CA-26.2 — La biblioteca filtra por estado y lo combina con la búsqueda."""

    def setUp(self):
        """Un álbum en progreso (el de la base) y otro completado."""
        super().setUp()
        self.done = self.make_album(self.owner, "ja")
        self.done.title = "Ember Line"
        self.done.save()
        set_status(self.make_page(self.done), ComicPage.Status.APPROVED)

    def test_the_filter_shows_only_that_status(self):
        """CA-26.2 — "Completados" deja solo el álbum completado."""
        response = self.client.get(reverse("albums:list"), {"estado": "completados"})

        self.assertEqual(response.context["albums"], [self.done])
        self.assertContains(response, "1 de 2")

    def test_each_filter_shows_its_count(self):
        """CA-26.2 — Cada filtro muestra cuántos álbumes tiene."""
        response = self.client.get(reverse("albums:list"))

        counts = {
            item["slug"]: item["count"] for item in response.context["status_filters"]
        }
        self.assertEqual(counts["todos"], 2)
        self.assertEqual(counts["en-progreso"], 1)
        self.assertEqual(counts["completados"], 1)
        self.assertEqual(counts["borradores"], 0)

    def test_the_filter_combines_with_the_search(self):
        """CA-26.2 — Filtro y búsqueda se aplican a la vez."""
        response = self.client.get(
            reverse("albums:list"), {"estado": "completados", "q": "neon"}
        )

        self.assertEqual(response.context["albums"], [])
        self.assertContains(response, "Ningún álbum coincide con tu búsqueda")

    def test_an_unknown_filter_shows_everything(self):
        """Flujo alternativo: un filtro desconocido equivale a "Todos"."""
        response = self.client.get(reverse("albums:list"), {"estado": "inventado"})

        self.assertEqual(len(response.context["albums"]), 2)

    def test_the_card_shows_status_and_progress(self):
        """CA-26.1 — La tarjeta lleva el chip de estado y la barra de progreso."""
        response = self.client.get(reverse("albums:list"))

        self.assertContains(response, "Completado")
        self.assertContains(response, "En progreso")
        self.assertContains(response, "split-progress__ready")


class LibrarySummaryTests(ProcessingTestCase):
    """Cabecera de la biblioteca: saludo, estadísticas y página por seguir."""

    def test_the_summary_uses_real_data(self):
        """Las estadísticas y la banda salen de las páginas del usuario."""
        set_status(self.page, ComicPage.Status.NEEDS_REVIEW)
        add_region(self.page, 1, needs_review=True)

        response = self.client.get(reverse("albums:list"))

        self.assertContains(response, "Continuar donde lo dejaste")
        self.assertContains(response, f'href="{self.page.get_absolute_url()}"')
        labels = [stat["label"] for stat in response.context["stats"]]
        self.assertIn("Regiones por revisar", labels)

    def test_the_resume_page_is_never_foreign(self):
        """Aislamiento: la página por seguir es siempre propia."""
        self.assertEqual(resume_page(self.owner), self.page)
        self.assertEqual(resume_page(self.other), self.foreign_page)

    def test_the_greeting_follows_the_hour(self):
        """El saludo cambia con la hora local."""
        morning = timezone.localtime().replace(hour=9)
        evening = timezone.localtime().replace(hour=21)

        self.assertEqual(time_greeting(morning), "Buenos días")
        self.assertEqual(time_greeting(evening), "Buenas noches")


class PageFilterTests(ProcessingTestCase):
    """CA-22.4 — El detalle del álbum filtra sus páginas por estado."""

    def setUp(self):
        """Tres páginas: una sin procesar, una por revisar y una lista."""
        super().setUp()
        self.review = self.make_page(self.album)
        set_status(self.review, ComicPage.Status.NEEDS_REVIEW)
        self.ready = self.make_page(self.album)
        set_status(self.ready, ComicPage.Status.PROCESSED)

    def test_the_filter_shows_only_those_pages(self):
        """CA-22.4 — "Por revisar" muestra solo esa página y el recuento."""
        response = self.client.get(
            self.album.get_absolute_url(), {"estado": "por-revisar"}
        )

        shown = [card["page"] for card in response.context["page_cards"]]
        self.assertEqual(shown, [self.review])
        self.assertContains(response, "1 de 3 mostradas")

    def test_the_progress_card_splits_the_pages(self):
        """CA-22.4 — La tarjeta de progreso reparte las páginas por estado."""
        response = self.client.get(self.album.get_absolute_url())

        progress = response.context["page_progress"]
        self.assertEqual(
            (progress["ready"], progress["review"], progress["pending"]), (1, 1, 1)
        )
        self.assertContains(response, "Progreso de las páginas")

    def test_a_processed_page_without_text_is_full(self):
        """Una página procesada sin regiones tiene la barra completa."""
        cards = {
            card["page"]: card
            for card in map(page_card, pages_with_progress(self.album))
        }

        self.assertEqual(cards[self.ready]["percent"], 100)
        self.assertEqual(cards[self.page]["percent"], 0)


class SidebarTests(ProcessingTestCase):
    """La barra lateral muestra datos reales y solo con sesión iniciada."""

    def test_the_sidebar_counts_regions_to_review(self):
        """El distintivo de revisión cuenta las regiones propias por revisar."""
        add_region(self.page, 1, needs_review=True)
        add_region(self.foreign_page, 1, needs_review=True)

        response = self.client.get(reverse("albums:list"))

        self.assertEqual(response.context["sidebar"]["review_total"], 1)
        self.assertContains(response, "Páginas procesadas este mes")

    def test_the_quota_counts_this_month_only(self):
        """La cuota cuenta solo las páginas procesadas este mes."""
        set_status(self.page, ComicPage.Status.PROCESSED)
        old = self.make_page(self.album)
        set_status(old, ComicPage.Status.PROCESSED)
        ComicPage.objects.filter(pk=old.pk).update(
            updated_at=timezone.now() - timedelta(days=40)
        )

        response = self.client.get(reverse("albums:list"))

        self.assertEqual(response.context["sidebar"]["quota"]["used"], 1)

    def test_without_a_session_there_is_no_sidebar_data(self):
        """Sin sesión no se calcula nada de la barra lateral."""
        self.client.logout()

        response = self.client.get(reverse("accounts:login"))

        self.assertNotIn("sidebar", response.context)
