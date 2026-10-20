"""Pruebas de la búsqueda de álbumes por título (HU-50)."""

from django.urls import reverse

from albums.models import Album
from albums.tests.test_edit import AlbumEditTestCase


class AlbumSearchTests(AlbumEditTestCase):
    """Búsqueda en la biblioteca, limitada al título y al propietario."""

    def setUp(self):
        """Añade álbumes con títulos variados al propietario."""
        super().setUp()
        self.make_album(self.owner, "Camión Fantasma")
        self.make_album(self.owner, "Salt & Static")
        self.sign_in()

    def search(self, text):
        """Pide la biblioteca con el texto de búsqueda indicado."""
        return self.client.get(reverse("albums:list"), {"q": text})

    def titles(self, response):
        """Títulos de los álbumes devueltos."""
        return [album.title for album in response.context["albums"]]

    def test_partial_match_ignores_case(self):
        """HU-50 — Coincidencia parcial sin distinguir mayúsculas."""
        self.assertEqual(self.titles(self.search("YOKAI")), ["Neon Yokai Bureau"])

    def test_match_ignores_accents_in_both_directions(self):
        """HU-50 — Las tildes no cuentan al buscar."""
        self.assertEqual(self.titles(self.search("camion")), ["Camión Fantasma"])
        self.assertEqual(self.titles(self.search("CAMIÓN")), ["Camión Fantasma"])

    def test_no_results_shows_a_specific_empty_state(self):
        """HU-50 — Sin coincidencias se muestra un estado vacío propio."""
        response = self.search("zzz")

        self.assertEqual(self.titles(response), [])
        self.assertContains(response, "Ningún álbum coincide")
        self.assertNotContains(response, "Todavía no tienes álbumes")

    def test_empty_or_blank_query_lists_everything(self):
        """HU-50 — Una búsqueda vacía o de espacios devuelve todos."""
        self.assertEqual(len(self.titles(self.search(""))), 3)
        self.assertEqual(len(self.titles(self.search("   "))), 3)

    def test_other_accounts_albums_never_appear(self):
        """HU-50 — La búsqueda no revela álbumes de otra cuenta."""
        self.assertEqual(self.titles(self.search("ajeno")), [])

    def test_search_only_matches_the_title(self):
        """HU-50 — No busca por idioma ni por estado."""
        self.assertEqual(self.titles(self.search("Japonés")), [])
        self.assertEqual(self.titles(self.search("draft")), [])

    def test_search_text_is_escaped_in_the_page(self):
        """HU-50 — El texto buscado se escapa al mostrarse."""
        response = self.search("<script>alert(1)</script>")

        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_user_without_albums_sees_no_search_bar(self):
        """HU-50 — Sin álbumes no se muestra la barra de búsqueda."""
        Album.objects.filter(owner=self.owner).delete()

        response = self.client.get(reverse("albums:list"))

        self.assertNotContains(response, 'role="search"')
        self.assertContains(response, "Todavía no tienes álbumes")
