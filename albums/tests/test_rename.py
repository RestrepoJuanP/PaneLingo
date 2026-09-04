"""Pruebas del título de álbum y su renombrado (HU-06)."""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from albums.models import Album, Language

PASSWORD = "TraduccionSegura42"


class AlbumTitleTestCase(TestCase):
    """Base común: dos cuentas, un álbum propio y otro ajeno."""

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
        self.list_url = reverse("albums:list")

    def make_album(self, owner, title):
        """Crea un álbum a nombre de la cuenta indicada."""
        return Album.objects.create(
            owner=owner,
            title=title,
            source_language=self.japanese,
            target_language=self.spanish,
        )

    def rename_url(self, album):
        """Devuelve la dirección de renombrado de un álbum."""
        return reverse("albums:rename", kwargs={"pk": album.pk})

    def sign_in(self, user=None):
        """Inicia la sesión del usuario indicado."""
        self.client.login(email=(user or self.owner).email, password=PASSWORD)


class AlbumRenameSuccessTests(AlbumTitleTestCase):
    """CP-06.1 — Definir el título persiste el cambio — Happy Path."""

    def test_renaming_persists_the_new_title(self):
        """CP-06.1 — El título nuevo se almacena y se recupera."""
        self.sign_in()

        response = self.client.post(
            self.rename_url(self.album), data={"title": "Neon Yokai Bureau vol. 2"}
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "Neon Yokai Bureau vol. 2")
        self.assertRedirects(response, self.list_url)

    def test_the_new_title_is_shown_in_the_library(self):
        """CP-06.1 — El título nuevo se muestra al consultar el álbum.

        El título de partida es deliberadamente distinto del ejemplo que usa
        el placeholder del formulario de creación: si coincidiera, la
        comprobación de que el título viejo ya no aparece daría un falso
        negativo por culpa de ese texto de ayuda.
        """
        self.album.title = "Título de partida"
        self.album.save()
        self.sign_in()

        self.client.post(self.rename_url(self.album), data={"title": "Título renovado"})
        response = self.client.get(self.list_url)

        self.assertContains(response, "Título renovado")
        self.assertNotContains(response, "Título de partida")

    def test_the_title_is_trimmed_when_renaming(self):
        """CP-06.1 — Los espacios sobrantes se recortan al renombrar."""
        self.sign_in()

        self.client.post(
            self.rename_url(self.album), data={"title": "   Salt & Static   "}
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "Salt & Static")

    def test_a_single_character_title_is_accepted(self):
        """Un título de un solo carácter es válido.

        PaneLingo traduce manga y el traductor puede introducir el título
        original; hay obras japonesas tituladas con un único kanji.
        """
        self.sign_in()

        self.client.post(self.rename_url(self.album), data={"title": "凪"})

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "凪")

    def test_renaming_leaves_languages_and_status_untouched(self):
        """El renombrado no altera los idiomas ni el estado del álbum."""
        self.sign_in()
        english = Language.objects.get(code="en")

        self.client.post(
            self.rename_url(self.album),
            data={
                "title": "Solo cambia el título",
                # Campos añadidos al POST que el formulario no expone.
                "source_language": english.pk,
                "target_language": english.pk,
                "status": Album.Status.COMPLETED,
            },
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "Solo cambia el título")
        self.assertEqual(self.album.source_language, self.japanese)
        self.assertEqual(self.album.target_language, self.spanish)
        self.assertEqual(self.album.status, Album.Status.DRAFT)


class AlbumRenameErrorTests(AlbumTitleTestCase):
    """CP-06.2 — Título vacío o inválido — Flujo alternativo."""

    def test_an_empty_title_is_not_saved(self):
        """CP-06.2 — Un título vacío no se guarda y se informa el error."""
        self.sign_in()

        response = self.client.post(self.rename_url(self.album), data={"title": ""})

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "Neon Yokai Bureau")
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", response.context["form"].errors)
        self.assertContains(response, "Escribe un título para el álbum.")

    def test_a_whitespace_only_title_is_not_saved(self):
        """CP-06.2 — Un título de solo espacios no se guarda."""
        self.sign_in()

        response = self.client.post(
            self.rename_url(self.album), data={"title": "      "}
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "Neon Yokai Bureau")
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", response.context["form"].errors)

    def test_an_overlong_title_is_not_saved(self):
        """CP-06.2 — Un título de más de 120 caracteres no se guarda."""
        self.sign_in()

        response = self.client.post(
            self.rename_url(self.album), data={"title": "x" * 121}
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "Neon Yokai Bureau")
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", response.context["form"].errors)


class AlbumTitleEscapingTests(AlbumTitleTestCase):
    """El título se escapa en cada contexto donde se interpola.

    Son pruebas de regresión: si alguien marca el título como seguro con
    |safe en cualquiera de los dos sitios, estas pruebas fallan.
    """

    def test_html_in_the_title_is_escaped_in_the_document_body(self):
        """Un título con etiquetas HTML no inyecta nada en el cuerpo."""
        self.album.title = "<script>alert(1)</script>"
        self.album.save()
        self.sign_in()

        response = self.client.get(self.list_url)
        content = response.content.decode()

        self.assertNotIn("<script>alert(1)</script>", content)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", content)

    def test_double_quotes_in_the_title_do_not_break_the_aria_label(self):
        """Unas comillas dobles no pueden romper el atributo aria-label.

        El aria-label del botón de renombrar interpola el título dentro de un
        atributo HTML. Ahí unas comillas mal escapadas cierran el atributo
        antes de tiempo y descomponen la maqueta, un fallo distinto del que
        produciría el mismo título en el cuerpo del documento.
        """
        self.album.title = 'Salt " Static'
        self.album.save()
        self.sign_in()

        response = self.client.get(self.list_url)
        content = response.content.decode()

        self.assertNotIn('aria-label="Renombrar «Salt " Static»"', content)
        self.assertIn("Salt &quot; Static", content)
        self.assertIn(
            'aria-label="Renombrar «Salt &quot; Static»"',
            content,
        )

    def test_quotes_survive_a_round_trip_through_the_rename_form(self):
        """Un título con comillas se guarda y se vuelve a mostrar intacto."""
        self.sign_in()

        self.client.post(self.rename_url(self.album), data={"title": 'Ember "Line"'})

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, 'Ember "Line"')
        response = self.client.get(self.list_url)
        self.assertContains(response, "Ember &quot;Line&quot;")


class AlbumRenameIsolationTests(AlbumTitleTestCase):
    """Solo el propietario puede renombrar su álbum."""

    def test_renaming_someone_elses_album_returns_404(self):
        """Renombrar un álbum ajeno responde 404, no 403.

        Un 403 confirmaría que ese álbum existe; el 404 no revela nada.
        """
        self.sign_in()

        response = self.client.post(
            self.rename_url(self.foreign_album), data={"title": "Secuestrado"}
        )

        self.assertEqual(response.status_code, 404)
        self.foreign_album.refresh_from_db()
        self.assertEqual(self.foreign_album.title, "Álbum ajeno")

    def test_opening_the_rename_form_of_a_foreign_album_returns_404(self):
        """Ni siquiera se puede abrir el formulario de un álbum ajeno."""
        self.sign_in()

        response = self.client.get(self.rename_url(self.foreign_album))

        self.assertEqual(response.status_code, 404)

    def test_renaming_requires_a_session(self):
        """Un visitante anónimo no puede renombrar."""
        response = self.client.post(
            self.rename_url(self.album), data={"title": "Anónimo"}
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.title, "Neon Yokai Bureau")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_the_rename_action_is_reachable_by_keyboard(self):
        """La acción de renombrar es un enlace real, alcanzable por teclado.

        Un div con un manejador de clic no aparece en el orden de tabulación
        ni se activa con Enter. Aquí es un <a href>, así que funciona sin
        JavaScript y con teclado.
        """
        self.sign_in()

        response = self.client.get(self.list_url)
        content = response.content.decode()

        self.assertIn(f'href="{self.rename_url(self.album)}"', content)
        self.assertIn('aria-label="Renombrar «Neon Yokai Bureau»"', content)
