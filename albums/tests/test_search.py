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


class LiveSearchTests(AlbumEditTestCase):
    """HU-50 — La biblioteca está preparada para buscar mientras se escribe.

    El filtrado lo hace siempre el servidor; el JavaScript solo reemplaza el
    bloque de resultados. Estas pruebas fijan el contrato entre los dos: los
    marcadores que el script busca y que el bloque exista en toda respuesta.
    """

    RESULTS_BLOCK = '<div id="album-results" data-live-search-results>'

    def setUp(self):
        """Añade álbumes con títulos variados al propietario."""
        super().setUp()
        self.make_album(self.owner, "Camión Fantasma")
        self.make_album(self.owner, "Salt & Static")
        self.sign_in()

    def search(self, text):
        """Pide la biblioteca con el texto de búsqueda indicado."""
        return self.client.get(reverse("albums:list"), {"q": text})

    def test_the_form_is_marked_for_live_search(self):
        """HU-50 — El campo y el formulario llevan los marcadores del script."""
        response = self.search("")

        self.assertContains(response, "data-live-search\n")
        self.assertContains(response, "data-live-search-input")
        self.assertContains(response, 'aria-controls="album-results"')

    def test_every_response_has_the_results_block(self):
        """HU-50 — Con y sin coincidencias, la respuesta trae el bloque."""
        for text in ("", "yokai", "zzz"):
            with self.subTest(text=text):
                self.assertContains(self.search(text), self.RESULTS_BLOCK, count=1)

    def test_the_results_block_holds_the_cards_and_the_count(self):
        """HU-50 — El contador y las tarjetas viven dentro del bloque."""
        content = self.search("yokai").content.decode()
        block = content.split(self.RESULTS_BLOCK, 1)[1]

        self.assertIn("1 de 3", block)
        self.assertIn("Neon Yokai Bureau", block)
        self.assertNotIn('role="search"', block)

    def test_clear_is_hidden_until_there_is_a_search(self):
        """HU-50 — El botón de limpiar solo se ve cuando hay texto buscado."""
        hidden_clear = r"data-live-search-clear\s+hidden"

        self.assertRegex(self.search("").content.decode(), hidden_clear)
        self.assertNotRegex(self.search("yokai").content.decode(), hidden_clear)
        self.assertContains(self.search("yokai"), 'aria-label="Limpiar búsqueda"')

    def test_live_requests_receive_only_the_results_block(self):
        """HU-50 — La búsqueda automática recibe solo el bloque, ya filtrado."""
        response = self.client.get(
            reverse("albums:list"), {"q": "yokai"}, headers={"X-Live-Search": "1"}
        )

        self.assertTemplateUsed(response, "albums/_album_results.html")
        self.assertNotContains(response, "<html")
        self.assertNotContains(response, 'role="search"')
        self.assertContains(response, "Neon Yokai Bureau")
        self.assertNotContains(response, "Camión Fantasma")

    def test_live_requests_keep_owner_isolation(self):
        """HU-50 — Flujo alternativo: el bloque nunca trae álbumes ajenos."""
        response = self.client.get(
            reverse("albums:list"), {"q": "ajeno"}, headers={"X-Live-Search": "1"}
        )

        self.assertContains(response, "Ningún álbum coincide")

    def test_cards_carry_their_id_for_the_animation(self):
        """HU-50 — Cada tarjeta lleva su identificador para animar el cambio."""
        album = Album.objects.get(title="Neon Yokai Bureau")

        self.assertContains(self.search("yokai"), f'data-album-id="{album.pk}"')

    def test_no_results_offers_to_clear_the_search(self):
        """HU-50 — Sin coincidencias se ofrece limpiar la búsqueda (CA-50.4)."""
        response = self.search("zzz")

        self.assertContains(response, "Limpiar búsqueda</a>")

    def test_without_javascript_the_search_button_remains(self):
        """HU-50 — Flujo alternativo: sin JavaScript sigue el botón "Buscar"."""
        response = self.search("")

        self.assertContains(response, "data-live-search-submit>Buscar</button>")
