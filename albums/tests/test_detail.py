"""Pruebas del detalle de álbum (HU-08)."""

from html.parser import HTMLParser

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from albums.models import Album, Language

PASSWORD = "TraduccionSegura42"


class NestedAnchorDetector(HTMLParser):
    """Detecta enlaces anidados dentro de otros enlaces.

    Un <a> dentro de otro <a> es HTML inválido. El navegador lo repara
    partiendo el marcado de forma impredecible, y el resultado es que la
    acción interior deja de ser activable de manera fiable con teclado.
    """

    def __init__(self):
        """Inicializa el contador de profundidad y el registro de hallazgos."""
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.nested_found = False

    def handle_starttag(self, tag, attrs):
        """Cuenta la apertura de cada enlace y anota si hay anidamiento."""
        if tag != "a":
            return
        if self.depth > 0:
            self.nested_found = True
        self.depth += 1

    def handle_endtag(self, tag):
        """Cierra el enlace actual."""
        if tag == "a" and self.depth > 0:
            self.depth -= 1


class AlbumDetailTestCase(TestCase):
    """Base común: dos cuentas y un álbum de cada una."""

    def setUp(self):
        """Crea las cuentas, los idiomas y los dos álbumes."""
        self.owner = User.objects.create_user(
            email="mira@estudio.test",
            password=PASSWORD,
            display_name="Mira Okonkwo",
        )
        self.other = User.objects.create_user(
            email="ajena@estudio.test",
            password=PASSWORD,
            display_name="Cuenta ajena",
        )
        self.japanese = Language.objects.get(code="ja")
        self.spanish = Language.objects.get(code="es")
        self.album = self.make_album(self.owner, "Neon Yokai Bureau")
        self.foreign_album = self.make_album(self.other, "Álbum ajeno")

    def make_album(self, owner, title):
        """Crea un álbum a nombre de la cuenta indicada."""
        return Album.objects.create(
            owner=owner,
            title=title,
            source_language=self.japanese,
            target_language=self.spanish,
        )

    def sign_in(self, user=None):
        """Inicia la sesión del usuario indicado."""
        self.client.login(email=(user or self.owner).email, password=PASSWORD)


class AlbumDetailContentTests(AlbumDetailTestCase):
    """El detalle muestra la información real del álbum."""

    def test_the_header_shows_the_album_information(self):
        """CA-08.1 — El encabezado muestra título, idiomas y estado."""
        self.sign_in()

        response = self.client.get(self.album.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "albums/album_detail.html")
        self.assertContains(response, "Neon Yokai Bureau")
        self.assertContains(response, "JA → ES")
        self.assertContains(response, "Borrador")
        self.assertContains(response, "0 páginas")

    def test_the_pages_area_shows_its_empty_state(self):
        """Sin páginas cargadas se muestra el estado vacío del área."""
        self.sign_in()

        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "Este álbum aún no tiene páginas")

    def test_the_out_of_scope_blocks_are_absent(self):
        """No se maquetan las partes del mockup fuera del Sprint 1."""
        self.sign_in()

        response = self.client.get(self.album.get_absolute_url())
        content = response.content.decode()

        self.assertNotIn("Translation progress", content)
        self.assertNotIn("Open workspace", content)
        self.assertNotIn("Review &amp; export", content)

    def test_delete_is_shown_disabled(self):
        """Eliminar se maqueta deshabilitado, no funcional."""
        self.sign_in()

        response = self.client.get(self.album.get_absolute_url())
        content = response.content.decode()

        self.assertIn('aria-disabled="true"', content)
        self.assertIn("Eliminar álbumes llega en un sprint posterior", content)

    def test_there_is_a_link_back_to_the_library(self):
        """El detalle ofrece la vuelta a la biblioteca."""
        self.sign_in()

        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, reverse("albums:list"))
        self.assertContains(response, "Todos los álbumes")


class AlbumDetailIsolationTests(AlbumDetailTestCase):
    """Solo el propietario puede ver el detalle de su álbum."""

    def test_viewing_someone_elses_album_returns_404(self):
        """Ver un álbum ajeno responde 404, no 403."""
        self.sign_in()

        response = self.client.get(self.foreign_album.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_the_detail_requires_a_session(self):
        """Un visitante anónimo no accede al detalle."""
        response = self.client.get(self.album.get_absolute_url())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))


class AlbumCardLinkTests(AlbumDetailTestCase):
    """La tarjeta lleva al detalle sin estorbar a la acción de renombrar."""

    def test_the_card_links_to_the_album_detail(self):
        """El título de la tarjeta abre el detalle del álbum."""
        self.sign_in()

        response = self.client.get(reverse("albums:list"))

        self.assertContains(response, f'href="{self.album.get_absolute_url()}"')

    def test_the_card_has_no_anchor_nested_inside_another_anchor(self):
        """La tarjeta no puede envolverse entera en un enlace.

        Hoy la portada, el título y el botón de renombrar son enlaces
        HERMANOS: la portada queda fuera del orden de tabulación con
        tabindex="-1" y aria-hidden, y el título y el renombrado son dos
        paradas distintas.

        La tentación razonable es envolver la tarjeta completa en un <a> para
        que sea clicable de punta a punta. Si alguien lo hace, el botón de
        renombrar queda DENTRO de ese enlace, y un <a> dentro de otro <a> es
        HTML inválido: el navegador repara el marcado partiéndolo de forma
        impredecible, y el renombrado deja de poder activarse de manera fiable
        con teclado. Ninguna otra prueba lo detectaría, porque el HTML sigue
        conteniendo ambos href.

        Si esta prueba falla, no es caprichosa: la tarjeta se ha vuelto
        inaccesible. La salida no es envolverla en un enlace, sino hacerla
        clicable con una capa de superposición sobre el título.
        """
        self.sign_in()

        response = self.client.get(reverse("albums:list"))
        detector = NestedAnchorDetector()
        detector.feed(response.content.decode())

        self.assertFalse(
            detector.nested_found,
            "Hay un <a> anidado dentro de otro <a>. Lee el docstring: la "
            "tarjeta no puede envolverse entera en un enlace sin dejar el "
            "botón de renombrar inaccesible por teclado.",
        )

    def test_the_cover_link_is_not_a_second_tab_stop(self):
        """La portada duplica el destino pero no añade parada de tabulación."""
        self.sign_in()

        content = self.client.get(reverse("albums:list")).content.decode()

        self.assertIn('tabindex="-1" aria-hidden="true"', content)
