"""Pruebas de archivar álbumes (HU-69)."""

from django.urls import reverse

from albums.models import Album, ComicPage
from albums.tests.test_library_progress import add_region, set_status
from albums.tests.test_processing import ProcessingTestCase


class ArchiveTestCase(ProcessingTestCase):
    """Base: el álbum de la prueba, con una página, y la biblioteca."""

    def archive(self, album=None, **data):
        """Archiva el álbum y vuelve a leerlo."""
        album = album or self.album
        response = self.client.post(album.get_archive_url(), data)
        album.refresh_from_db()
        return response

    def unarchive(self, album=None, **data):
        """Desarchiva el álbum y vuelve a leerlo."""
        album = album or self.album
        response = self.client.post(album.get_unarchive_url(), data)
        album.refresh_from_db()
        return response

    def library(self, **params):
        """Abre "Mis álbumes" con los parámetros indicados."""
        return self.client.get(reverse("albums:list"), params)


class ArchiveAlbumTests(ArchiveTestCase):
    """CP-69.1 — Archivar un álbum — Happy Path."""

    def test_the_album_is_archived_without_confirmation(self):
        """CP-69.1 — Un solo POST lo archiva y vuelve a la biblioteca."""
        response = self.archive()

        self.assertTrue(self.album.is_archived)
        self.assertRedirects(response, reverse("albums:list"))

    def test_the_notice_offers_to_undo(self):
        """CP-69.1 — El aviso dice "archivado" y trae "Deshacer"."""
        response = self.archive()

        followed = self.client.get(response.url)
        self.assertContains(followed, "Álbum «Neon Yokai Bureau» archivado.")
        self.assertContains(followed, "Deshacer")
        self.assertContains(followed, self.album.get_unarchive_url())

    def test_archiving_does_not_count_as_editing(self):
        """CP-69.1 — Archivar no cambia la fecha de edición del álbum."""
        edited = self.album.updated_at

        self.archive()

        self.assertEqual(self.album.updated_at, edited)

    def test_the_card_and_the_detail_offer_to_archive(self):
        """CP-69.1 — "Archivar" está en el menú "···" y en el detalle."""
        library = self.library()
        detail = self.client.get(self.album.get_absolute_url())

        self.assertContains(library, self.album.get_archive_url())
        self.assertContains(detail, self.album.get_archive_url())

    def test_it_returns_to_the_page_it_came_from(self):
        """CP-69.1 — Vuelve a la biblioteca con el mismo filtro."""
        response = self.archive(next="/?estado=en-progreso")

        self.assertRedirects(
            response, "/?estado=en-progreso", fetch_redirect_response=False
        )

    def test_it_never_redirects_to_another_site(self):
        """CP-69.1 — Una dirección de otro dominio se ignora."""
        response = self.archive(next="https://ejemplo.test/")

        self.assertRedirects(response, reverse("albums:list"))


class HiddenFromLibraryTests(ArchiveTestCase):
    """CP-69.2 — Los archivados no aparecen en la biblioteca."""

    def setUp(self):
        """Un álbum activo ("Ember Line") y el de la prueba, archivado."""
        super().setUp()
        self.active = self.make_album(self.owner, "ja")
        Album.objects.filter(pk=self.active.pk).update(title="Ember Line")
        self.archive()

    def test_the_library_and_its_filters_hide_it(self):
        """CP-69.2 — No aparece en "Todos" ni en los filtros por estado."""
        for estado in ("todos", "en-progreso", "por-revisar"):
            with self.subTest(estado=estado):
                response = self.library(estado=estado)
                self.assertNotIn(self.album, response.context["albums"])

    def test_the_search_hides_it(self):
        """CP-69.2 — Buscar por su título no lo encuentra."""
        response = self.library(q="neon")

        self.assertEqual(response.context["albums"], [])

    def test_the_archived_filter_shows_it(self):
        """CP-69.2 — "Archivados (1)" lo muestra."""
        response = self.library()
        archived = self.library(estado="archivados")

        self.assertContains(response, "Archivados")
        filters = {
            item["slug"]: item["count"] for item in response.context["status_filters"]
        }
        self.assertEqual(filters["archivados"], 1)
        self.assertEqual(archived.context["albums"], [self.album])
        self.assertContains(archived, "Archivado hace")

    def test_with_everything_archived_the_library_says_so(self):
        """CP-69.2 — Con todo archivado se explica y se ofrece verlos."""
        self.archive(self.active)

        response = self.library()

        self.assertContains(response, "Todos tus álbumes están archivados")
        self.assertContains(response, "?estado=archivados")


class UnarchiveTests(ArchiveTestCase):
    """CP-69.3 — Desarchivar — Flujo alternativo."""

    def test_it_comes_back_with_its_derived_status(self):
        """CP-69.3 — Vuelve a la biblioteca con su estado de siempre."""
        set_status(self.page, ComicPage.Status.NEEDS_REVIEW)
        self.archive()

        response = self.unarchive(next=reverse("albums:list"))

        self.assertFalse(self.album.is_archived)
        followed = self.client.get(response.url)
        self.assertIn(self.album, followed.context["albums"])
        self.assertContains(followed, "En revisión")
        self.assertContains(followed, "devuelto a la biblioteca")

    def test_undo_from_the_notice_works(self):
        """CP-69.3 — "Deshacer" del aviso desarchiva el álbum."""
        self.archive()

        self.unarchive()

        self.assertFalse(self.album.is_archived)


class ArchivedDetailTests(ArchiveTestCase):
    """CP-69.4 — Un álbum archivado sigue accesible."""

    def test_the_detail_opens_with_a_notice(self):
        """CP-69.4 — El detalle avisa y ofrece "Desarchivar"."""
        self.archive()

        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "Este álbum está archivado.")
        self.assertContains(response, self.album.get_unarchive_url())
        self.assertNotContains(response, self.album.get_archive_url())

    def test_its_pages_can_still_be_opened(self):
        """CP-69.4 — Sus páginas se siguen abriendo."""
        self.archive()

        response = self.client.get(self.page.get_absolute_url())

        self.assertEqual(response.status_code, 200)


class SummariesTests(ArchiveTestCase):
    """CP-69.5 — Los archivados no cuentan en los resúmenes."""

    def setUp(self):
        """Una región por revisar en el álbum, que luego se archiva."""
        super().setUp()
        set_status(self.page, ComicPage.Status.NEEDS_REVIEW)
        add_region(self.page, 1, needs_review=True)

    def test_stats_sidebar_and_resume_ignore_archived_albums(self):
        """CP-69.5 — Ni estadísticas, ni barra lateral, ni "Continuar"."""
        before = self.library()
        self.assertEqual(before.context["sidebar"]["review_total"], 1)
        self.assertContains(before, "Continuar donde lo dejaste")

        self.archive()
        after = self.library()

        self.assertEqual(after.context["sidebar"]["review_total"], 0)
        self.assertIsNone(after.context["resume"])
        stats = {stat["label"]: stat["value"] for stat in after.context["stats"]}
        self.assertEqual(stats["Regiones por revisar"], 0)
        self.assertEqual(stats["Páginas procesadas esta semana"], 0)


class ArchiveAccessTests(ArchiveTestCase):
    """CP-69.6 — Solo álbumes propios — Flujo alternativo."""

    def test_foreign_albums_are_not_found(self):
        """CP-69.6 — Archivar o desarchivar un álbum ajeno responde 404."""
        foreign = self.foreign_page.album

        for name in ("albums:archive", "albums:unarchive"):
            with self.subTest(name=name):
                response = self.client.post(reverse(name, args=[foreign.pk]))
                self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertFalse(foreign.is_archived)
