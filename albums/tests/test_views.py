"""Pruebas de las vistas de la app albums (HU-05)."""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from albums.models import Album, Language

PASSWORD = "TraduccionSegura42"


class AlbumViewTestCase(TestCase):
    """Base común: dos cuentas distintas y los idiomas del catálogo."""

    def setUp(self):
        """Crea las cuentas, los idiomas y las direcciones usadas."""
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
        self.list_url = reverse("albums:list")
        self.create_url = reverse("albums:create")
        self.payload = {
            "title": "Neon Yokai Bureau",
            "source_language": self.japanese.pk,
            "target_language": self.spanish.pk,
        }

    def sign_in(self, user=None):
        """Inicia la sesión del usuario indicado."""
        self.client.login(email=(user or self.owner).email, password=PASSWORD)

    def make_album(self, owner, title="Álbum"):
        """Crea un álbum a nombre de la cuenta indicada."""
        return Album.objects.create(
            owner=owner,
            title=title,
            source_language=self.japanese,
            target_language=self.spanish,
        )


class AlbumCreateSuccessTests(AlbumViewTestCase):
    """CP-05.1 — Crear un álbum con datos válidos — Happy Path."""

    def test_valid_post_creates_one_album_for_the_signed_in_user(self):
        """CP-05.1 — El álbum se crea asociado a la cuenta autenticada."""
        self.sign_in()

        response = self.client.post(self.create_url, data=self.payload)

        self.assertEqual(Album.objects.count(), 1)
        album = Album.objects.get()
        self.assertEqual(album.owner, self.owner)
        self.assertEqual(album.title, "Neon Yokai Bureau")
        self.assertEqual(album.source_language, self.japanese)
        self.assertEqual(album.target_language, self.spanish)
        self.assertRedirects(response, self.list_url)

    def test_the_new_album_appears_in_the_library(self):
        """CP-05.1 — El álbum queda visible en la biblioteca del usuario."""
        self.sign_in()

        self.client.post(self.create_url, data=self.payload)
        response = self.client.get(self.list_url)

        self.assertContains(response, "Neon Yokai Bureau")
        self.assertIn(Album.objects.get(), response.context["albums"])

    def test_a_confirmation_message_is_shown(self):
        """CP-05.1 — El sistema confirma que el álbum quedó creado."""
        self.sign_in()

        response = self.client.post(self.create_url, data=self.payload, follow=True)

        self.assertContains(response, "creado correctamente")


class AlbumCreateErrorTests(AlbumViewTestCase):
    """CP-05.2 — Falta información obligatoria — Flujo alternativo."""

    def test_a_post_without_a_title_creates_no_album(self):
        """CP-05.2 — Sin título no se crea el álbum y se informa el error."""
        self.sign_in()
        payload = self.payload.copy()
        payload["title"] = ""

        response = self.client.post(self.create_url, data=payload)

        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", response.context["form"].errors)
        self.assertContains(response, "Escribe un título para el álbum.")

    def test_a_post_without_languages_creates_no_album(self):
        """CP-05.2 — Sin idiomas no se crea el álbum."""
        self.sign_in()

        response = self.client.post(self.create_url, data={"title": "Sin idiomas"})

        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("source_language", response.context["form"].errors)
        self.assertIn("target_language", response.context["form"].errors)

    def test_what_was_typed_is_kept(self):
        """CP-05.2 — Se conserva lo escrito al volver a mostrar el formulario."""
        self.sign_in()
        payload = self.payload.copy()
        payload["source_language"] = ""

        response = self.client.post(self.create_url, data=payload)

        self.assertContains(response, 'value="Neon Yokai Bureau"')


class AlbumOwnershipTests(AlbumViewTestCase):
    """El propietario lo fija el servidor, nunca los datos enviados."""

    def test_a_forged_owner_field_is_ignored(self):
        """El álbum se crea a nombre de quien tiene la sesión, no del id enviado.

        Es la prueba central del aislamiento por propietario. Un POST que
        incluya owner con el identificador de otra cuenta no debe suplantarla:
        se comprueba el valor final de owner, no solo que la petición no
        falle.
        """
        self.sign_in()
        forged = self.payload.copy()
        forged["owner"] = self.other.pk

        response = self.client.post(self.create_url, data=forged)

        self.assertRedirects(response, self.list_url)
        self.assertEqual(Album.objects.count(), 1)

        album = Album.objects.get()
        self.assertEqual(album.owner, self.owner)
        self.assertNotEqual(album.owner, self.other)
        self.assertEqual(self.other.albums.count(), 0)
        self.assertEqual(self.owner.albums.count(), 1)

    def test_a_forged_owner_field_is_ignored_even_by_its_email(self):
        """Tampoco sirve enviar el correo de otra cuenta."""
        self.sign_in()
        forged = self.payload.copy()
        forged["owner"] = self.other.email

        self.client.post(self.create_url, data=forged)

        self.assertEqual(Album.objects.get().owner, self.owner)
        self.assertEqual(self.other.albums.count(), 0)


class AlbumLibraryIsolationTests(AlbumViewTestCase):
    """Cada usuario solo ve su propia biblioteca."""

    def test_the_library_hides_albums_from_other_accounts(self):
        """Un usuario no ve en su biblioteca los álbumes de otra cuenta."""
        mine = self.make_album(self.owner, "Álbum propio")
        theirs = self.make_album(self.other, "Álbum ajeno")
        self.sign_in()

        response = self.client.get(self.list_url)

        listed = list(response.context["albums"])
        self.assertEqual(listed, [mine])
        self.assertNotIn(theirs, listed)
        self.assertNotContains(response, "Álbum ajeno")

    def test_the_empty_state_is_shown_without_albums(self):
        """Sin álbumes se muestra el estado vacío, no una rejilla en blanco."""
        self.make_album(self.other, "Álbum ajeno")
        self.sign_in()

        response = self.client.get(self.list_url)

        self.assertEqual(list(response.context["albums"]), [])
        self.assertContains(response, "Todavía no tienes álbumes")


class AlbumAccessTests(AlbumViewTestCase):
    """Ambas vistas son privadas."""

    def test_the_library_redirects_anonymous_visitors(self):
        """Un visitante anónimo no accede a la biblioteca."""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_creating_redirects_anonymous_visitors(self):
        """Un visitante anónimo no puede crear álbumes."""
        response = self.client.post(self.create_url, data=self.payload)

        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))
