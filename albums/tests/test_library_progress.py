"""Pruebas del progreso calculado: estado derivado, filtros y resúmenes.

Cubren lo que alimenta la biblioteca, el detalle del álbum y la barra lateral
del mockup (HU-22, HU-26): todas las cifras salen de páginas y regiones.
"""

from datetime import timedelta
from unittest import mock

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


def add_pages(album, statuses):
    """Añade páginas ligeras con los estados indicados para probar resúmenes."""
    first_number = album.pages.count() + 1
    pages = [
        ComicPage(
            album=album,
            page_number=first_number + offset,
            image=f"pages/tests/{album.pk}-{first_number + offset}.png",
            original_filename=f"pagina-{first_number + offset}.png",
            width=400,
            height=560,
            file_size=100,
            status=status,
        )
        for offset, status in enumerate(statuses)
    ]
    return ComicPage.objects.bulk_create(pages)


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
        self.assertContains(response, "progress__fill")


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


class AlbumApprovalProgressTests(ProcessingTestCase):
    """HU-25 — El progreso del álbum se mide por páginas aprobadas."""

    def make_twenty_four_pages(self):
        """Prepara 24 páginas, ocho aprobadas, como en los antecedentes."""
        set_status(self.page, ComicPage.Status.APPROVED)
        add_pages(
            self.album,
            [ComicPage.Status.APPROVED] * 7 + [ComicPage.Status.PROCESSED] * 16,
        )

    def test_library_and_detail_show_approved_page_progress(self):
        """CP-25.1 — Biblioteca y detalle muestran 8 de 24 y 33 %."""
        self.make_twenty_four_pages()

        library = self.client.get(reverse("albums:list"))
        detail = self.client.get(self.album.get_absolute_url())
        expected = "8 de 24 páginas aprobadas (33 %)"

        self.assertContains(library, expected)
        self.assertContains(detail, expected)
        self.assertContains(library, 'role="progressbar"')
        self.assertContains(library, 'aria-valuenow="33"')
        self.assertContains(library, f'aria-valuetext="{expected}"')
        self.assertContains(detail, f'aria-valuetext="{expected}"')

    def test_progress_changes_when_one_more_page_is_approved(self):
        """CP-25.2 — Una aprobación cambia el progreso de 33 % a 38 %."""
        self.make_twenty_four_pages()
        page = self.album.pages.filter(status=ComicPage.Status.PROCESSED).first()

        set_status(page, ComicPage.Status.APPROVED)
        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "9 de 24 páginas aprobadas (38 %)")
        self.assertContains(response, 'aria-valuenow="38"')

    def test_detail_breaks_pages_down_into_four_states(self):
        """CP-25.3 — El detalle desglosa los cuatro grupos solicitados."""
        set_status(self.page, ComicPage.Status.FAILED)
        add_pages(
            self.album,
            [
                ComicPage.Status.PENDING,
                ComicPage.Status.PROCESSING,
                ComicPage.Status.PROCESSED,
                ComicPage.Status.NEEDS_REVIEW,
                ComicPage.Status.APPROVED,
            ],
        )

        response = self.client.get(self.album.get_absolute_url())
        breakdown = response.context["page_progress"]

        self.assertEqual(breakdown["pending_count"], 2)
        self.assertEqual(breakdown["processing_count"], 1)
        self.assertEqual(breakdown["review_count"], 2)
        self.assertEqual(breakdown["approved_count"], 1)
        self.assertContains(response, "Pendientes")
        self.assertContains(response, "En proceso")
        self.assertContains(response, "En revisión")
        self.assertContains(response, "Aprobadas")

    def test_album_without_pages_says_so_instead_of_showing_zero_percent(self):
        """CP-25.4 — Un álbum vacío muestra “Sin páginas”, no “0 %”."""
        empty = self.make_album(self.owner, "ko")
        empty.title = "Álbum vacío"
        empty.save(update_fields=["title"])

        detail = self.client.get(empty.get_absolute_url())
        library = self.client.get(reverse("albums:list"), {"q": "Álbum vacío"})

        self.assertContains(detail, "Sin páginas")
        self.assertNotContains(detail, "0 %")
        self.assertContains(library, "Sin páginas")
        self.assertNotContains(library, "0 %")


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
        """CP-22.4 — "Por revisar" muestra solo esa página y el recuento."""
        response = self.client.get(
            self.album.get_absolute_url(), {"estado": "por-revisar"}
        )

        shown = [card["page"] for card in response.context["page_cards"]]
        self.assertEqual(shown, [self.review])
        self.assertContains(response, "1 de 3 mostradas")

    def test_the_progress_card_splits_the_pages(self):
        """CP-22.4 — La tarjeta de progreso reparte las páginas por estado."""
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

    def test_each_page_shows_its_status_as_text(self):
        """CP-22.1 — Cada página muestra un chip con texto y color."""
        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "Pendiente")
        self.assertContains(response, "Revisar")
        self.assertContains(response, "Procesada")
        self.assertContains(response, "badge--neutral")
        self.assertContains(response, "badge--warning")
        self.assertContains(response, "badge--success")


class PageStatusLiveTests(ProcessingTestCase):
    """CP-22.3 — El estado cambia en pantalla sin recargar a mano."""

    @mock.patch("albums.tasks.process_page_task")
    def test_a_processing_card_polls_and_has_a_live_region(self, task):
        """CP-22.3 — La tarjeta consulta el estado y anuncia el cambio."""
        self.process()

        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(
            response, f'data-page-status-poll="{self.page.get_status_url()}"'
        )
        self.assertContains(response, 'data-page-status-value="processing"')
        self.assertContains(response, 'data-page-number="1"')
        self.assertContains(response, 'aria-live="polite"')
        self.assertContains(response, "data-page-status-live")
        self.assertContains(response, "data-page-status-badge")
        self.assertContains(response, "data-page-status-bar")

    def test_a_finished_card_does_not_keep_polling(self):
        """CP-22.3 — Una página terminada deja de consultar su estado."""
        self.process()

        response = self.client.get(self.album.get_absolute_url())

        self.assertNotContains(response, "data-page-status-poll")


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


class ApprovedReviewAccountingTests(ProcessingTestCase):
    """BUG-072 — Una traducción aprobada ya no cuenta por revisar."""

    def setUp(self):
        """Crea una región dudosa cuya traducción ya fue aprobada."""
        super().setUp()
        self.region = add_region(self.page, 1, needs_review=True)
        self.region.translation = "Texto aprobado"
        self.region.translation_status = TextRegion.TranslationStatus.APPROVED
        self.region.save(update_fields=["translation", "translation_status"])

    def test_library_detail_and_sidebar_exclude_the_approved_region(self):
        """CP-26.1 / BUG-072 — Los resúmenes no inflan el trabajo pendiente."""
        progress = AlbumProgress.of(
            with_progress(Album.objects.filter(pk=self.album.pk)).get()
        )
        page = pages_with_progress(self.album).get(pk=self.page.pk)
        library = self.client.get(reverse("albums:list"))

        review_stat = next(
            stat
            for stat in library.context["stats"]
            if stat["label"] == "Regiones por revisar"
        )
        self.assertEqual(progress.region_review, 0)
        self.assertEqual(page.region_review, 0)
        self.assertEqual(page_card(page)["percent"], 100)
        self.assertEqual(library.context["sidebar"]["review_total"], 0)
        self.assertEqual(review_stat["value"], 0)

    def test_workspace_hides_the_review_warning_and_filter_result(self):
        """CP-19.2 / BUG-072 — La página no contradice la aprobación."""
        workspace = self.client.get(self.page.get_absolute_url())
        filtered = self.client.get(
            self.page.get_absolute_url(),
            {"filtro": "revisar"},
        )

        self.assertEqual(workspace.context["review_count"], 0)
        self.assertNotContains(workspace, "necesita revisión")
        self.assertEqual(filtered.context["visible_regions"], [])
