"""Pruebas de la edición de un álbum (HU-08)."""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from albums.models import Album, Language

PASSWORD = "TraduccionSegura42"


class AlbumEditTestCase(TestCase):
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
        self.english = Language.objects.get(code="en")
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

    def snapshot(self, album):
        """Devuelve el estado completo de un álbum, para comparar después."""
        album.refresh_from_db()
        return {
            "pk": album.pk,
            "title": album.title,
            "source_language": album.source_language_id,
            "target_language": album.target_language_id,
            "status": album.status,
            "owner": album.owner_id,
            "created_at": album.created_at,
            "updated_at": album.updated_at,
        }


class AlbumEditSuccessTests(AlbumEditTestCase):
    """CP-08.1 — Modificar y guardar actualiza el álbum — Happy Path."""

    def test_the_form_arrives_filled_with_the_current_values(self):
        """El formulario de edición llega con los valores actuales."""
        self.sign_in()

        response = self.client.get(self.album.get_edit_url())

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.initial["title"], "Neon Yokai Bureau")
        self.assertEqual(form.initial["source_language"], self.japanese.pk)
        self.assertEqual(form.initial["target_language"], self.spanish.pk)

    def test_saving_updates_the_same_record(self):
        """CP-08.1 — Los cambios se aplican al mismo álbum, sin crear otro."""
        self.sign_in()
        original_pk = self.album.pk

        response = self.client.post(
            self.album.get_edit_url(),
            data={
                "title": "Neon Yokai Bureau vol. 2",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
            },
        )

        self.assertEqual(Album.objects.filter(owner=self.owner).count(), 1)
        self.album.refresh_from_db()
        self.assertEqual(self.album.pk, original_pk)
        self.assertEqual(self.album.title, "Neon Yokai Bureau vol. 2")
        self.assertEqual(self.album.target_language, self.english)
        self.assertRedirects(response, self.album.get_absolute_url())

    def test_the_changes_are_visible_when_reloading_the_detail(self):
        """CP-08.1 — El encabezado del detalle refleja los cambios."""
        self.sign_in()

        self.client.post(
            self.album.get_edit_url(),
            data={
                "title": "Título actualizado",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
            },
        )
        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "Título actualizado")
        self.assertContains(response, "JA → EN")

    def test_a_confirmation_message_is_shown(self):
        """CP-08.1 — El sistema confirma que el álbum quedó actualizado."""
        self.sign_in()

        response = self.client.post(
            self.album.get_edit_url(),
            data={
                "title": "Título actualizado",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
            },
            follow=True,
        )

        self.assertContains(response, "Álbum actualizado correctamente")


class AlbumEditCancelTests(AlbumEditTestCase):
    """CP-08.2 — Cancelar conserva la información previa — Flujo alternativo."""

    def test_opening_and_leaving_the_form_changes_nothing(self):
        """CP-08.2 — Abrir el formulario y salir no altera ningún campo.

        Se compara el álbum completo, incluido updated_at: cancelar es un
        enlace de vuelta al detalle, no un envío, así que no debe producirse
        ninguna escritura.
        """
        before = self.snapshot(self.album)
        self.sign_in()

        self.client.get(self.album.get_edit_url())
        self.client.get(self.album.get_absolute_url())

        self.assertEqual(self.snapshot(self.album), before)

    def test_the_cancel_control_is_a_link_and_not_a_submit(self):
        """Cancelar no envía el formulario: es un enlace al detalle.

        Si fuera un botón de envío, cancelar escribiría en la base de datos y
        movería updated_at, incumpliendo CA-08.2.
        """
        self.sign_in()

        content = self.client.get(self.album.get_edit_url()).content.decode()
        detail_url = self.album.get_absolute_url()

        self.assertIn(
            f'<a class="btn btn--secondary" href="{detail_url}">Cancelar</a>',
            content,
        )


class AlbumEditErrorTests(AlbumEditTestCase):
    """Una edición inválida no deja cambios a medias."""

    def test_an_invalid_post_persists_no_partial_changes(self):
        """Un POST inválido no guarda ninguno de los campos enviados."""
        before = self.snapshot(self.album)
        self.sign_in()

        response = self.client.post(
            self.album.get_edit_url(),
            data={
                # El título es válido, pero el par de idiomas no.
                "title": "Título que no debe guardarse",
                "source_language": self.japanese.pk,
                "target_language": self.japanese.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("target_language", response.context["form"].errors)
        self.assertEqual(self.snapshot(self.album), before)

    def test_an_empty_title_persists_nothing(self):
        """Un título vacío no altera el álbum."""
        before = self.snapshot(self.album)
        self.sign_in()

        response = self.client.post(
            self.album.get_edit_url(),
            data={
                "title": "",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.snapshot(self.album), before)


class AlbumEditIsolationTests(AlbumEditTestCase):
    """Solo el propietario puede editar su álbum."""

    def test_editing_someone_elses_album_returns_404(self):
        """Editar un álbum ajeno responde 404, no 403."""
        before = self.snapshot(self.foreign_album)
        self.sign_in()

        response = self.client.post(
            self.foreign_album.get_edit_url(),
            data={
                "title": "Secuestrado",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.snapshot(self.foreign_album), before)

    def test_opening_the_edit_form_of_a_foreign_album_returns_404(self):
        """Ni siquiera se puede abrir el formulario de un álbum ajeno."""
        self.sign_in()

        response = self.client.get(self.foreign_album.get_edit_url())

        self.assertEqual(response.status_code, 404)

    def test_editing_requires_a_session(self):
        """Un visitante anónimo no puede editar."""
        before = self.snapshot(self.album)

        response = self.client.post(
            self.album.get_edit_url(),
            data={
                "title": "Anónimo",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))
        self.assertEqual(self.snapshot(self.album), before)

    def test_a_forged_owner_field_does_not_transfer_the_album(self):
        """Un POST con owner manipulado no cambia el propietario."""
        self.sign_in()

        self.client.post(
            self.album.get_edit_url(),
            data={
                "title": "Sigue siendo mío",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
                "owner": self.other.pk,
            },
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.owner, self.owner)
        self.assertEqual(self.other.albums.count(), 1)
        self.assertEqual(self.other.albums.get(), self.foreign_album)


class AlbumStatusIsNotEditableTests(AlbumEditTestCase):
    """El estado no está entre los campos editables de HU-08.

    Los cuatro estados describen fases de un flujo de traducción que no existe
    en el Sprint 1: "En revisión" supone bloques esperando revisión y
    "Completado" supone una traducción terminada. Permitir fijarlos a mano
    dejaría que el usuario afirme algo que el sistema sabe que es falso.

    Si el Product Owner decide activarlo, entra como historia nueva del
    backlog y esta prueba se sustituye por su contraria.
    """

    def test_status_is_not_offered_in_the_form(self):
        """El formulario de edición no expone el campo de estado."""
        self.sign_in()

        response = self.client.get(self.album.get_edit_url())

        self.assertNotIn("status", response.context["form"].fields)

    def test_a_forged_status_field_is_ignored(self):
        """Un estado enviado en el POST no altera el del álbum."""
        self.sign_in()

        self.client.post(
            self.album.get_edit_url(),
            data={
                "title": "Neon Yokai Bureau",
                "source_language": self.japanese.pk,
                "target_language": self.english.pk,
                "status": Album.Status.COMPLETED,
            },
        )

        self.album.refresh_from_db()
        self.assertEqual(self.album.status, Album.Status.DRAFT)
