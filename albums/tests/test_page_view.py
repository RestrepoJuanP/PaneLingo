"""Pruebas de la vista de una página y del acceso a sus imágenes (HU-11)."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from albums.models import ComicPage
from albums.tests.test_pages import make_image_bytes
from albums.tests.test_processing import ProcessingTestCase


class PageSelectionTests(ProcessingTestCase):
    """CP-11.2 — Seleccionar una página — Happy Path."""

    def setUp(self):
        """Deja el álbum con tres páginas: la 1 (de la base), la 2 y la 3."""
        super().setUp()
        self.second = self.make_page(self.album)
        self.third = self.make_page(self.album)

    def test_the_page_shows_its_data(self):
        """CP-11.2 — Se ven número, nombre, dimensiones, estado y fecha."""
        response = self.client.get(self.second.get_absolute_url())

        self.assertContains(response, '<h1 class="sr-only">Página 2 de')
        self.assertContains(response, "pagina.png")
        self.assertContains(response, "400 × 560 px")
        self.assertContains(response, "Pendiente de procesamiento")
        self.assertContains(response, "<dt>Cargada</dt>")
        self.assertContains(response, f'src="{self.second.get_image_url()}"')

    def test_previous_and_next_pages_are_linked(self):
        """CP-11.2 — Se puede pasar a la página anterior y a la siguiente."""
        response = self.client.get(self.second.get_absolute_url())

        self.assertContains(response, f'href="{self.page.get_absolute_url()}"')
        self.assertContains(response, f'href="{self.third.get_absolute_url()}"')
        self.assertContains(response, 'rel="prev"')
        self.assertContains(response, 'rel="next"')
        self.assertContains(response, "Página 2 de 3")

    def test_the_keyboard_can_follow_the_links(self):
        """CP-11.2 — Los enlaces llevan las marcas que usan las flechas."""
        response = self.client.get(self.second.get_absolute_url())

        self.assertContains(response, "data-page-pager")
        self.assertContains(response, "data-page-prev")
        self.assertContains(response, "data-page-next")

    def test_the_first_and_last_pages_have_no_link_beyond(self):
        """CP-11.2 — Flujo alternativo: en los extremos no hay a dónde ir."""
        first = self.client.get(self.page.get_absolute_url())
        last = self.client.get(self.third.get_absolute_url())

        self.assertNotContains(first, 'rel="prev"')
        self.assertContains(first, 'rel="next"')
        self.assertContains(last, 'rel="prev"')
        self.assertNotContains(last, 'rel="next"')

    def test_deleted_pages_are_skipped(self):
        """CP-11.2 — Con un hueco en la numeración, "Anterior" lo salta."""
        self.second.delete()

        response = self.client.get(self.third.get_absolute_url())

        self.assertContains(response, f'href="{self.page.get_absolute_url()}"')
        self.assertContains(response, "Página 2 de 2")

    def test_the_pages_never_mix_albums(self):
        """CP-11.2 — La navegación no salta a páginas de otro álbum."""
        other_album = self.make_album(self.owner, "ja")
        self.make_page(other_album)

        response = self.client.get(self.third.get_absolute_url())

        self.assertNotContains(response, 'rel="next"')


class ImageAccessTests(ProcessingTestCase):
    """CP-11.4 — Las imágenes de otra cuenta no son accesibles."""

    def image_addresses(self, page):
        """Devuelve las direcciones de la vista, la imagen y la miniatura."""
        return [
            page.get_absolute_url(),
            page.get_image_url(),
            page.get_thumbnail_url(),
        ]

    def test_the_owner_receives_the_image_and_the_thumbnail(self):
        """CP-11.4 — El propietario recibe sus imágenes, sin caché."""
        for address in (self.page.get_image_url(), self.page.get_thumbnail_url()):
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response["Content-Type"].startswith("image/"))
                self.assertIn("no-store", response["Cache-Control"])
                self.assertTrue(b"".join(response.streaming_content))

    def test_another_account_gets_not_found(self):
        """CP-11.4 — Con sesión de otra cuenta: 404 y la imagen no se entrega."""
        for address in self.image_addresses(self.foreign_page):
            with self.subTest(address=address):
                self.assertEqual(self.client.get(address).status_code, 404)

    def test_without_a_session_the_image_is_not_delivered(self):
        """CP-11.4 — Sin sesión se pide iniciarla y la imagen no se entrega."""
        self.client.logout()

        for address in self.image_addresses(self.page):
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/cuentas/ingresar/", response.url)

    def test_the_media_address_is_not_served(self):
        """CP-11.4 — La dirección en disco ya no es una puerta trasera (DT-02)."""
        response = self.client.get(self.page.image.url)

        self.assertEqual(response.status_code, 404)

    def test_the_grid_uses_the_protected_thumbnail(self):
        """CP-11.4 — La rejilla del álbum pide la miniatura protegida."""
        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, self.page.get_thumbnail_url())
        self.assertNotContains(response, self.page.thumbnail.url)

    def test_a_page_without_thumbnail_falls_back_to_the_original(self):
        """CP-11.4 — Sin miniatura, la dirección de miniatura sirve el original."""
        ComicPage.objects.filter(pk=self.page.pk).update(thumbnail="")

        response = self.client.get(self.page.get_thumbnail_url())

        self.assertEqual(response.status_code, 200)


class CoverAccessTests(ProcessingTestCase):
    """CP-11.4 — La portada subida tiene el mismo control de acceso (DT-02)."""

    def setUp(self):
        """Sube una portada al álbum propio y otra al ajeno."""
        super().setUp()
        self.foreign_album = self.foreign_page.album
        for album in (self.album, self.foreign_album):
            album.cover_image = SimpleUploadedFile(
                "portada.png", make_image_bytes(300, 400), "image/png"
            )
            album.save()

    def test_the_owner_receives_the_cover(self):
        """CP-11.4 — El propietario recibe su portada."""
        response = self.client.get(self.album.cover_url)

        self.assertEqual(response.status_code, 200)

    def test_another_account_cannot_get_the_cover(self):
        """CP-11.4 — La portada de otra cuenta responde 404."""
        address = reverse("albums:album_cover", kwargs={"pk": self.foreign_album.pk})

        self.assertEqual(self.client.get(address).status_code, 404)

    def test_an_album_without_cover_has_no_cover_address(self):
        """CP-11.4 — Sin portada subida no hay dirección y la vista da 404."""
        self.album.cover_image = ""
        self.album.save()

        self.assertEqual(self.album.cover_url, "")
        address = reverse("albums:album_cover", kwargs={"pk": self.album.pk})
        self.assertEqual(self.client.get(address).status_code, 404)


class OpenWorkspaceTests(ProcessingTestCase):
    """CP-11.2 — El detalle del álbum abre el espacio de trabajo."""

    def test_the_workspace_opens_on_the_first_page_with_work(self):
        """CP-11.2 — "Abrir espacio de trabajo" lleva a la primera pendiente."""
        self.page.status = ComicPage.Status.PROCESSED
        self.page.save()
        second = self.make_page(self.album)

        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "Abrir espacio de trabajo")
        self.assertContains(
            response,
            f'class="btn btn--primary" href="{second.get_absolute_url()}"',
        )

    def test_an_album_without_pages_offers_to_add_them(self):
        """CP-11.3 — Flujo alternativo: sin páginas no hay espacio de trabajo."""
        self.page.delete()

        response = self.client.get(self.album.get_absolute_url())

        self.assertNotContains(response, "Abrir espacio de trabajo")
