"""Pruebas de la eliminación de páginas de un álbum (HU-10)."""

import os
import shutil
import tempfile

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from albums.models import Album, ComicPage, Language
from albums.tests.test_pages import make_image_bytes

PASSWORD = "TraduccionSegura42"

MEDIA_ROOT = tempfile.mkdtemp(prefix="panelingo-delete-media-")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PageDeleteTestCase(TestCase):
    """Base común: dos cuentas, un álbum con páginas y otro ajeno."""

    def setUp(self):
        """Crea las cuentas, los álbumes y carga tres páginas."""
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

        self.sign_in()
        self.upload_pages(self.album, 3)
        self.pages = list(self.album.pages.all())

    def tearDown(self):
        """Borra los archivos que la prueba haya dejado en media/."""
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

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

    def upload_pages(self, album, count):
        """Carga varias páginas en un álbum a través de la vista de carga."""
        files = [
            SimpleUploadedFile(
                f"pagina{index}.png", make_image_bytes(400, 560), "image/png"
            )
            for index in range(count)
        ]
        self.client.post(album.get_upload_url(), data={"pages": files})

    def stored_files(self):
        """Devuelve todos los archivos que hay ahora mismo en MEDIA_ROOT."""
        found = []
        for root, _dirs, filenames in os.walk(MEDIA_ROOT):
            found.extend(os.path.join(root, name) for name in filenames)
        return found


class PageDeleteSuccessTests(PageDeleteTestCase):
    """CP-10.1 — Confirmar elimina la página — Happy Path."""

    def test_confirming_removes_the_page_from_the_album(self):
        """CP-10.1 — La página se elimina del álbum al confirmar."""
        page = self.pages[1]

        response = self.client.post(page.get_delete_url())

        self.assertFalse(ComicPage.objects.filter(pk=page.pk).exists())
        self.assertEqual(self.album.pages.count(), 2)
        self.assertRedirects(response, self.album.get_absolute_url())

    def test_the_files_stop_existing_in_media_root(self):
        """CP-10.1 — La imagen y la miniatura desaparecen del disco."""
        page = self.pages[1]
        image_path = page.image.path
        thumbnail_path = page.thumbnail.path
        self.assertTrue(os.path.exists(image_path))
        self.assertTrue(os.path.exists(thumbnail_path))

        self.client.post(page.get_delete_url())

        self.assertFalse(os.path.exists(image_path))
        self.assertFalse(os.path.exists(thumbnail_path))

    def test_no_orphan_files_are_left_behind(self):
        """CP-10.1 — No quedan archivos huérfanos tras el borrado."""
        page = self.pages[1]

        self.client.post(page.get_delete_url())

        # Dos páginas por dos archivos cada una: imagen y miniatura.
        self.assertEqual(len(self.stored_files()), 4)

    def test_the_page_no_longer_appears_in_the_detail(self):
        """CP-10.1 — La página deja de verse en el detalle del álbum."""
        page = self.pages[1]
        thumbnail_url = page.thumbnail.url

        self.client.post(page.get_delete_url())
        response = self.client.get(self.album.get_absolute_url())

        self.assertNotContains(response, thumbnail_url)
        self.assertNotContains(response, "Página 2")

    def test_the_page_counter_is_recalculated(self):
        """CP-10.1 — El contador de páginas refleja la eliminación."""
        self.client.post(self.pages[1].get_delete_url())

        response = self.client.get(self.album.get_absolute_url())

        self.assertEqual(self.album.page_count, 2)
        self.assertContains(response, "2 páginas")

    def test_a_confirmation_message_is_shown(self):
        """CP-10.1 — El sistema confirma la eliminación."""
        response = self.client.post(self.pages[1].get_delete_url(), follow=True)

        self.assertContains(response, "Se eliminó la página 2")


class PageNumberingAfterDeleteTests(PageDeleteTestCase):
    """Las páginas restantes conservan su número.

    Renumerar movería la etiqueta de las demás y borraría información: un
    hueco en la secuencia indica que a la obra le falta esa página.
    """

    def test_the_remaining_pages_keep_their_numbers(self):
        """Tras borrar la 2, quedan la 1 y la 3, no la 1 y la 2."""
        self.client.post(self.pages[1].get_delete_url())

        numbers = list(self.album.pages.values_list("page_number", flat=True))

        self.assertEqual(numbers, [1, 3])

    def test_a_new_upload_continues_after_the_highest_number(self):
        """Una carga posterior sigue al número más alto, sin rellenar huecos."""
        self.client.post(self.pages[1].get_delete_url())

        self.upload_pages(self.album, 1)

        numbers = list(self.album.pages.values_list("page_number", flat=True))
        self.assertEqual(numbers, [1, 3, 4])

    def test_the_message_explains_that_numbers_are_kept(self):
        """El mensaje explica el hueco donde podría parecer un error."""
        response = self.client.post(self.pages[1].get_delete_url(), follow=True)

        self.assertContains(response, "Las demás conservan su número")


class LastPageDeleteTests(PageDeleteTestCase):
    """Eliminar la última página deja el álbum en estado vacío consistente."""

    def delete_every_page(self):
        """Elimina todas las páginas del álbum, una a una."""
        for page in self.pages:
            self.client.post(page.get_delete_url())

    def test_the_album_ends_up_empty_without_errors(self):
        """El álbum queda sin páginas y sus cálculos no revientan."""
        self.delete_every_page()

        self.assertEqual(self.album.pages.count(), 0)
        self.assertEqual(self.album.page_count, 0)
        self.assertEqual(self.album.progress_percentage, 0)

    def test_the_detail_falls_back_to_the_empty_state(self):
        """El detalle vuelve a mostrar el estado vacío."""
        self.delete_every_page()

        response = self.client.get(self.album.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este álbum aún no tiene páginas")

    def test_no_files_are_left_in_media_root(self):
        """No queda ningún archivo del álbum en disco."""
        self.delete_every_page()

        self.assertEqual(self.stored_files(), [])

    def test_the_message_does_not_mention_remaining_pages(self):
        """Al borrar la última no se habla de las "demás", que no existen.

        Cada borrado previo se sigue con follow para que su mensaje se
        consuma: sin eso los toasts se acumulan y el último render mostraría
        también los de las eliminaciones anteriores.
        """
        for page in self.pages[:-1]:
            self.client.post(page.get_delete_url(), follow=True)

        response = self.client.post(self.pages[-1].get_delete_url(), follow=True)
        messages = [str(message) for message in get_messages(response.wsgi_request)]

        self.assertEqual(len(messages), 1)
        self.assertIn("El álbum se quedó sin páginas", messages[0])
        self.assertNotIn("Las demás conservan su número", messages[0])


class PageDeleteCancelTests(PageDeleteTestCase):
    """CP-10.2 — Cancelar deja todo intacto — Flujo alternativo."""

    def snapshot(self):
        """Devuelve el estado del álbum, sus páginas y sus archivos."""
        self.album.refresh_from_db()
        return {
            "updated_at": self.album.updated_at,
            "pages": list(self.album.pages.values_list("pk", "page_number", "image")),
            "files": sorted(self.stored_files()),
        }

    def test_opening_the_confirmation_and_leaving_changes_nothing(self):
        """CP-10.2 — Abrir la confirmación y salir no altera nada.

        Se comprueban las páginas, sus archivos y el updated_at del álbum:
        cancelar es un enlace de vuelta al detalle, no un envío, así que no
        debe producirse ninguna escritura.
        """
        before = self.snapshot()

        self.client.get(self.pages[1].get_delete_url())
        self.client.get(self.album.get_absolute_url())

        self.assertEqual(self.snapshot(), before)

    def test_a_get_does_not_delete_anything(self):
        """CP-10.2 — Un GET a la URL de eliminación no borra la página."""
        page = self.pages[1]

        response = self.client.get(page.get_delete_url())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ComicPage.objects.filter(pk=page.pk).exists())
        self.assertTrue(os.path.exists(page.image.path))
        self.assertEqual(len(self.stored_files()), 6)

    def test_the_cancel_control_is_a_link_and_not_a_submit(self):
        """Cancelar no envía el formulario: es un enlace al detalle."""
        content = self.client.get(self.pages[1].get_delete_url()).content.decode()
        detail_url = self.album.get_absolute_url()

        self.assertIn(f'<a class="btn btn--secondary" href="{detail_url}">', content)

    def test_a_post_without_csrf_token_is_rejected(self):
        """Un POST sin token CSRF no elimina la página."""
        page = self.pages[1]
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(email=self.owner.email, password=PASSWORD)

        response = csrf_client.post(page.get_delete_url())

        self.assertEqual(response.status_code, 403)
        self.assertTrue(ComicPage.objects.filter(pk=page.pk).exists())


class PageDeleteIsolationTests(PageDeleteTestCase):
    """Nadie puede eliminar páginas de álbumes ajenos."""

    def setUp(self):
        """Añade una página al álbum de la otra cuenta."""
        super().setUp()
        self.sign_in(self.other)
        self.upload_pages(self.foreign_album, 1)
        self.foreign_page = self.foreign_album.pages.get()
        self.sign_in(self.owner)

    def test_deleting_a_page_of_another_account_returns_404(self):
        """Un POST sobre una página ajena responde 404 y no borra nada."""
        image_path = self.foreign_page.image.path

        response = self.client.post(self.foreign_page.get_delete_url())

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ComicPage.objects.filter(pk=self.foreign_page.pk).exists())
        self.assertTrue(os.path.exists(image_path))

    def test_opening_the_confirmation_of_a_foreign_page_returns_404(self):
        """Ni siquiera se puede ver la confirmación de una página ajena."""
        response = self.client.get(self.foreign_page.get_delete_url())

        self.assertEqual(response.status_code, 404)

    def test_deleting_requires_a_session(self):
        """Un visitante anónimo no puede eliminar páginas."""
        self.client.logout()
        page = self.pages[1]

        response = self.client.post(page.get_delete_url())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))
        self.assertTrue(ComicPage.objects.filter(pk=page.pk).exists())


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class CascadeFileCleanupTests(PageDeleteTestCase):
    """El borrado en cascada también limpia los archivos del disco.

    Se usa una señal post_delete y NO se sobrescribe ComicPage.delete(): al
    borrar en cascada, el recolector de Django elimina las páginas en bloque
    sin llamar al método delete() de cada instancia, y los archivos quedarían
    huérfanos. Estas pruebas fijan que los dos niveles de cascada funcionan.
    """

    def test_deleting_the_album_removes_its_page_files(self):
        """Borrar un álbum entero no deja archivos de sus páginas.

        Eliminar álbumes está deshabilitado en la interfaz del Sprint 1, pero
        el borrado a nivel de modelo ya limpia el disco. Cuando llegue esa
        historia no hará falta añadir nada.
        """
        self.assertEqual(len(self.stored_files()), 6)

        self.album.delete()

        self.assertEqual(ComicPage.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_deleting_the_account_removes_every_page_file(self):
        """Borrar la cuenta no deja archivos de ninguno de sus álbumes.

        Es el caso que anuncia la pantalla de perfil del mockup: eliminar la
        cuenta retira todos los álbumes y todas las páginas. Esa pantalla está
        fuera del alcance del Sprint 1, pero dejar demostrado que a nivel de
        modelo no quedan archivos es información útil para el sprint que la
        implemente.
        """
        second_album = self.make_album(self.owner, "Salt & Static")
        self.upload_pages(second_album, 2)
        self.assertEqual(len(self.stored_files()), 10)

        self.owner.delete()

        self.assertEqual(Album.objects.filter(owner_id=self.owner.pk).count(), 0)
        self.assertEqual(ComicPage.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class FileCleanupToleranceTests(PageDeleteTestCase):
    """El borrado del registro no depende de que el archivo exista.

    La limpieza corre dentro de la transacción del borrado, así que dejar
    escapar una excepción revertiría la eliminación de la fila: quedarían el
    registro Y el archivo. De los dos desenlaces, un archivo huérfano es
    recuperable y un borrado a medias no.
    """

    def test_a_missing_file_does_not_break_the_deletion(self):
        """Si el archivo ya no está en disco, la página se elimina igual."""
        page = self.pages[1]
        os.remove(page.image.path)
        os.remove(page.thumbnail.path)

        response = self.client.post(page.get_delete_url())

        self.assertFalse(ComicPage.objects.filter(pk=page.pk).exists())
        self.assertRedirects(response, self.album.get_absolute_url())
