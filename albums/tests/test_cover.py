"""Pruebas de la portada del álbum al crear y editar (HU-49)."""

import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from albums.models import Album
from albums.tests.test_edit import AlbumEditTestCase
from albums.tests.test_pages import make_upload

COVER_MEDIA_ROOT = tempfile.mkdtemp(prefix="panelingo-test-covers-")


@override_settings(MEDIA_ROOT=COVER_MEDIA_ROOT)
class AlbumCoverTests(AlbumEditTestCase):
    """Subir, reemplazar y quitar la portada de un álbum."""

    @classmethod
    def tearDownClass(cls):
        """Elimina los archivos de prueba."""
        super().tearDownClass()
        shutil.rmtree(COVER_MEDIA_ROOT, ignore_errors=True)

    def edit_data(self, **extra):
        """Datos válidos del formulario de álbum."""
        data = {
            "title": self.album.title,
            "source_language": self.japanese.pk,
            "target_language": self.spanish.pk,
        }
        data.update(extra)
        return data

    def test_create_album_with_cover(self):
        """HU-49 — Crear un álbum con portada la guarda."""
        self.sign_in()

        self.client.post(
            reverse("albums:create"),
            self.edit_data(title="Con portada", cover_image=make_upload("a.png")),
        )

        album = Album.objects.get(title="Con portada")
        self.assertTrue(album.cover_image)
        self.assertTrue(
            album.cover_image.name.startswith(f"albums/user_{self.owner.pk}/covers/")
        )

    def test_create_album_without_cover_keeps_the_default(self):
        """HU-49 — Sin portada se conserva la predeterminada."""
        self.sign_in()

        self.client.post(reverse("albums:create"), self.edit_data(title="Sin portada"))

        album = Album.objects.get(title="Sin portada")
        self.assertFalse(album.cover_image)
        self.assertEqual(album.cover_url, "")

    def test_edit_replaces_cover_and_deletes_the_old_file(self):
        """HU-49 — Reemplazar la portada borra el archivo anterior."""
        self.sign_in()
        url = self.album.get_edit_url()
        self.client.post(url, self.edit_data(cover_image=make_upload("a.png")))
        self.album.refresh_from_db()
        old_path = self.album.cover_image.path

        self.client.post(url, self.edit_data(cover_image=make_upload("b.png")))

        self.album.refresh_from_db()
        self.assertNotEqual(self.album.cover_image.path, old_path)
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(self.album.cover_image.path))

    def test_edit_without_file_keeps_current_cover(self):
        """HU-49 — Editar sin subir archivo no toca la portada."""
        self.sign_in()
        url = self.album.get_edit_url()
        self.client.post(url, self.edit_data(cover_image=make_upload("a.png")))
        self.album.refresh_from_db()
        name = self.album.cover_image.name

        self.client.post(url, self.edit_data(title="Otro título"))

        self.album.refresh_from_db()
        self.assertEqual(self.album.cover_image.name, name)

    def test_remove_cover_returns_to_the_default(self):
        """HU-49 — Quitar la portada vuelve a la predeterminada."""
        self.sign_in()
        url = self.album.get_edit_url()
        self.client.post(url, self.edit_data(cover_image=make_upload("a.png")))
        self.album.refresh_from_db()
        old_path = self.album.cover_image.path

        self.client.post(url, self.edit_data(remove_cover="on"))

        self.album.refresh_from_db()
        self.assertFalse(self.album.cover_image)
        self.assertFalse(os.path.exists(old_path))

    def test_fake_image_is_rejected(self):
        """HU-49 — Un archivo que no es imagen se rechaza y no se guarda."""
        self.sign_in()
        fake = SimpleUploadedFile("x.png", b"no soy una imagen", "image/png")

        response = self.client.post(
            self.album.get_edit_url(), self.edit_data(cover_image=fake)
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["cover_image"])
        self.album.refresh_from_db()
        self.assertFalse(self.album.cover_image)

    def test_foreign_album_cover_cannot_be_changed(self):
        """HU-49 — Cambiar la portada de un álbum ajeno responde 404."""
        self.sign_in()

        response = self.client.post(
            self.foreign_album.get_edit_url(),
            self.edit_data(cover_image=make_upload("a.png")),
        )

        self.assertEqual(response.status_code, 404)

    def test_deleting_the_album_removes_the_cover_file(self):
        """HU-49 — Al borrar el álbum se borra el archivo de portada."""
        self.sign_in()
        self.client.post(
            self.album.get_edit_url(), self.edit_data(cover_image=make_upload("a.png"))
        )
        self.album.refresh_from_db()
        path = self.album.cover_image.path

        self.album.delete()

        self.assertFalse(os.path.exists(path))

    def test_list_card_shows_the_cover_and_links_to_edit(self):
        """HU-49 — La tarjeta muestra la portada subida y el lápiz edita."""
        self.sign_in()
        self.client.post(
            self.album.get_edit_url(), self.edit_data(cover_image=make_upload("a.png"))
        )
        self.album.refresh_from_db()

        content = self.client.get(reverse("albums:list")).content.decode()

        self.assertIn(self.album.cover_image.url, content)
        self.assertIn(f'href="{self.album.get_edit_url()}"', content)
        self.assertIn('enctype="multipart/form-data"', content)
