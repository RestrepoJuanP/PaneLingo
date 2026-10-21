"""Pruebas de la biblioteca de álbumes (HU-21).

"Mis álbumes" se construyó en el Sprint 1 como apoyo a HU-05, sin una HU
propia. Estas pruebas dan a cada criterio de HU-21 su caso de prueba.
"""

from datetime import timedelta

from django.utils import timezone

from albums.models import Album
from albums.tests.test_views import AlbumViewTestCase


class LibraryTestCase(AlbumViewTestCase):
    """Base: la sesión de la dueña iniciada."""

    def setUp(self):
        """Inicia la sesión de la dueña de los álbumes."""
        super().setUp()
        self.sign_in()

    def library(self):
        """Abre "Mis álbumes"."""
        return self.client.get(self.list_url)


class LibraryCardsTests(LibraryTestCase):
    """CP-21.1 — Ver la biblioteca de álbumes — Happy Path."""

    def test_each_album_has_its_card(self):
        """CP-21.1 — Con 3 álbumes se ven 3 tarjetas."""
        for title in ("Neon Yokai Bureau", "Ember Line", "Salt & Static"):
            self.make_album(self.owner, title)

        response = self.library()

        self.assertEqual(len(response.context["albums"]), 3)
        self.assertContains(response, 'class="album-card"', count=3)

    def test_the_card_shows_the_album_data(self):
        """CP-21.1 — Portada, título, par de idiomas, páginas, edición y estado."""
        self.make_album(self.owner, "Neon Yokai Bureau")

        response = self.library()

        self.assertContains(response, "album-card__cover")
        self.assertContains(response, "Neon Yokai Bureau")
        self.assertContains(response, "JA → ES")
        self.assertContains(response, "0 páginas")
        self.assertContains(response, "Editado hace")
        self.assertContains(response, "Borrador")


class LibraryIsolationTests(LibraryTestCase):
    """CP-21.2 — Solo veo mis álbumes — Flujo alternativo."""

    def test_albums_of_other_accounts_do_not_appear(self):
        """CP-21.2 — El álbum "Ajeno" de otra cuenta no aparece."""
        self.make_album(self.owner, "Propio")
        self.make_album(self.other, "Ajeno")

        response = self.library()

        self.assertContains(response, "Propio")
        self.assertNotContains(response, "Ajeno")


class OpenAlbumTests(LibraryTestCase):
    """CP-21.3 — Abrir un álbum — Happy Path."""

    def test_the_card_leads_to_the_album_detail(self):
        """CP-21.3 — La tarjeta enlaza con el detalle del álbum, con sus páginas."""
        album = self.make_album(self.owner, "Neon Yokai Bureau")

        response = self.library()

        self.assertContains(
            response, f'class="album-card__title" href="{album.get_absolute_url()}"'
        )
        detail = self.client.get(album.get_absolute_url())
        self.assertContains(detail, "Neon Yokai Bureau")
        self.assertContains(detail, "Páginas")


class EmptyLibraryTests(LibraryTestCase):
    """CP-21.4 — Biblioteca vacía — Flujo alternativo."""

    def test_an_empty_state_with_new_album_is_shown(self):
        """CP-21.4 — Sin álbumes, estado vacío y botón "Nuevo álbum"."""
        response = self.library()

        self.assertContains(response, "Todavía no tienes álbumes")
        self.assertContains(response, "Nuevo álbum")
        self.assertNotContains(response, 'class="album-card"')


class LibraryOrderTests(LibraryTestCase):
    """CP-21.5 — Orden de la biblioteca."""

    def test_the_most_recently_edited_album_comes_first(self):
        """CP-21.5 — Del editado más recientemente al más antiguo."""
        oldest = self.make_album(self.owner, "Antiguo")
        middle = self.make_album(self.owner, "Intermedio")
        newest = self.make_album(self.owner, "Reciente")
        now = timezone.now()
        for album, days in ((oldest, 3), (middle, 2), (newest, 1)):
            Album.objects.filter(pk=album.pk).update(
                updated_at=now - timedelta(days=days)
            )

        response = self.library()

        self.assertEqual(list(response.context["albums"]), [newest, middle, oldest])

    def test_editing_an_album_moves_it_to_the_top(self):
        """CP-21.5 — Al editar un álbum antiguo, pasa al principio."""
        older = self.make_album(self.owner, "Antiguo")
        newer = self.make_album(self.owner, "Reciente")
        Album.objects.filter(pk=older.pk).update(
            updated_at=timezone.now() - timedelta(days=5)
        )
        older.refresh_from_db()

        older.title = "Antiguo, retocado"
        older.save()
        response = self.library()

        self.assertEqual(list(response.context["albums"]), [older, newer])
