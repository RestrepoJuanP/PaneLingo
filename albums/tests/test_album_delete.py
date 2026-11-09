"""Pruebas de la eliminación confirmada de álbumes (HU-20)."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from albums.models import Album, ComicPage, TextRegion
from albums.tests.test_page_delete import PASSWORD, PageDeleteTestCase
from albums.tests.test_pages import make_image_bytes


class AlbumDeleteTests(PageDeleteTestCase):
    """CP-20.1 a CP-20.5 — Eliminar un álbum propio con confirmación."""

    def fill_to_twenty_four_pages(self):
        """Completa las tres páginas reales con 21 registros ligeros."""
        ComicPage.objects.bulk_create(
            [
                ComicPage(
                    album=self.album,
                    page_number=number,
                    image=f"pages/tests/album-{self.album.pk}-{number}.png",
                    original_filename=f"pagina-{number}.png",
                    width=400,
                    height=560,
                    file_size=100,
                )
                for number in range(4, 25)
            ]
        )

    def snapshot(self):
        """Devuelve álbum, páginas y archivos para comprobar cancelaciones."""
        return {
            "album": list(
                Album.objects.filter(pk=self.album.pk).values(
                    "pk", "title", "updated_at"
                )
            ),
            "pages": list(
                self.album.pages.order_by("page_number").values_list(
                    "pk", "page_number"
                )
            ),
            "files": sorted(self.stored_files()),
        }

    def test_confirmation_identifies_the_album_and_its_pages(self):
        """CP-20.1 — La confirmación nombra el álbum y sus 24 páginas."""
        self.fill_to_twenty_four_pages()

        response = self.client.get(self.album.get_delete_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "albums/album_confirm_delete.html")
        self.assertContains(response, "¿Eliminar «Neon Yokai Bureau»?")
        self.assertContains(
            response,
            "Se eliminarán también las 24 páginas cargadas. "
            "Esta acción no se puede deshacer.",
        )
        self.assertContains(response, "Eliminar definitivamente")
        self.assertContains(response, "Cancelar")

    def test_detail_offers_an_accessible_confirmation_modal(self):
        """CP-20.1 / CP-20.3 — El modal conserva foco, Escape y cancelación."""
        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, 'data-modal-open="eliminar-album"')
        self.assertContains(response, 'id="eliminar-album"')
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'aria-modal="true"')
        self.assertContains(response, "data-modal-close")
        self.assertContains(response, f'action="{self.album.get_delete_url()}"')

    def test_confirming_deletes_the_album_pages_regions_and_files(self):
        """CP-20.2 — Confirmar elimina en cascada datos y archivos."""
        region = TextRegion.objects.create(
            page=self.pages[0],
            reading_order=1,
            x=10,
            y=10,
            width=100,
            height=50,
            source_text="原文",
            translation="Traducción aprobada",
            translation_status=TextRegion.TranslationStatus.APPROVED,
        )
        self.album.cover_image.save(
            "portada.png",
            SimpleUploadedFile(
                "portada.png",
                make_image_bytes(400, 560),
                content_type="image/png",
            ),
        )
        page_ids = list(self.album.pages.values_list("pk", flat=True))
        stored_before = self.stored_files()
        self.assertGreater(len(stored_before), 0)

        response = self.client.post(self.album.get_delete_url(), follow=True)

        self.assertRedirects(response, reverse("albums:list"))
        self.assertFalse(Album.objects.filter(pk=self.album.pk).exists())
        self.assertFalse(ComicPage.objects.filter(pk__in=page_ids).exists())
        self.assertFalse(TextRegion.objects.filter(pk=region.pk).exists())
        self.assertEqual(self.stored_files(), [])
        self.assertContains(response, "Se eliminó el álbum «Neon Yokai Bureau».")

    def test_canceling_keeps_the_album_and_returns_to_the_trigger(self):
        """CP-20.3 — Cancelar no escribe y vuelve al detalle del álbum."""
        before = self.snapshot()

        confirmation = self.client.get(self.album.get_delete_url())
        self.client.get(self.album.get_absolute_url())

        self.assertEqual(self.snapshot(), before)
        self.assertContains(
            confirmation,
            f'<a class="btn btn--secondary" href="{self.album.get_absolute_url()}">',
            html=False,
        )

    def test_a_foreign_album_returns_404_and_survives(self):
        """CP-20.4 — Un álbum ajeno responde 404 y no se elimina."""
        get_response = self.client.get(self.foreign_album.get_delete_url())
        post_response = self.client.post(self.foreign_album.get_delete_url())

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(post_response.status_code, 404)
        self.assertTrue(Album.objects.filter(pk=self.foreign_album.pk).exists())

    def test_a_get_never_deletes_the_album(self):
        """CP-20.5 — Abrir la dirección de eliminación no borra nada."""
        before = self.snapshot()

        response = self.client.get(self.album.get_delete_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.snapshot(), before)

    def test_deleting_requires_a_session(self):
        """Seguridad — Una persona anónima no puede eliminar un álbum."""
        self.client.logout()

        response = self.client.post(self.album.get_delete_url())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))
        self.assertTrue(Album.objects.filter(pk=self.album.pk).exists())

    def test_a_post_without_csrf_token_is_rejected(self):
        """Seguridad — El POST exige un token CSRF válido."""
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(email=self.owner.email, password=PASSWORD)

        response = csrf_client.post(self.album.get_delete_url())

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Album.objects.filter(pk=self.album.pk).exists())

    def test_the_library_menu_links_to_the_confirmation(self):
        """CP-20.1 — La tarjeta permite abrir la confirmación sin JavaScript."""
        response = self.client.get(reverse("albums:list"))

        self.assertContains(response, f'href="{self.album.get_delete_url()}"')
