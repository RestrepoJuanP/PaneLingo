"""Pruebas de los idiomas de origen y destino de un álbum (HU-07)."""

import re

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from albums.forms import AlbumForm, AlbumRenameForm
from albums.models import Album, Language

PASSWORD = "TraduccionSegura42"


class AlbumLanguageTestCase(TestCase):
    """Base común: una cuenta, los idiomas del catálogo y unos datos válidos."""

    def setUp(self):
        """Prepara la cuenta, los idiomas y el conjunto de datos válido."""
        self.owner = User.objects.create_user(
            email="mira@estudio.test",
            password=PASSWORD,
            display_name="Mira Okonkwo",
        )
        self.japanese = Language.objects.get(code="ja")
        self.spanish = Language.objects.get(code="es")
        self.english = Language.objects.get(code="en")
        self.list_url = reverse("albums:list")
        self.create_url = reverse("albums:create")
        self.payload = {
            "title": "Neon Yokai Bureau",
            "source_language": self.japanese.pk,
            "target_language": self.spanish.pk,
        }

    def sign_in(self):
        """Inicia la sesión del propietario."""
        self.client.login(email=self.owner.email, password=PASSWORD)

    def payload_with(self, **overrides):
        """Devuelve los datos válidos con los campos indicados sustituidos."""
        data = self.payload.copy()
        data.update(overrides)
        return data


class LanguagePersistenceTests(AlbumLanguageTestCase):
    """CP-07.1 — Ambos idiomas se conservan — Happy Path."""

    def test_both_languages_are_stored(self):
        """CP-07.1 — El álbum conserva idioma de origen y de destino."""
        self.sign_in()

        response = self.client.post(self.create_url, data=self.payload)

        self.assertRedirects(response, self.list_url)
        album = Album.objects.get()
        self.assertEqual(album.source_language, self.japanese)
        self.assertEqual(album.target_language, self.spanish)

    def test_both_languages_are_recovered_when_consulting_the_album(self):
        """CP-07.1 — Las dos relaciones se recuperan al consultar el álbum."""
        self.sign_in()
        self.client.post(self.create_url, data=self.payload)

        album = Album.objects.select_related("source_language", "target_language").get()

        self.assertEqual(album.source_language.name, "Japonés")
        self.assertEqual(album.target_language.name, "Español")
        self.assertEqual(album.language_pair, "JA → ES")

    def test_the_language_pair_is_rendered_on_the_card(self):
        """CP-07.1 — El par de idiomas aparece en la portada de la tarjeta."""
        self.sign_in()
        self.client.post(self.create_url, data=self.payload)

        response = self.client.get(self.list_url)
        content = response.content.decode()

        self.assertIn('<span class="cover__lang">JA → ES</span>', content)

    def test_each_album_shows_its_own_language_pair(self):
        """Dos álbumes con distinto destino muestran pares distintos."""
        self.sign_in()
        self.client.post(self.create_url, data=self.payload)
        self.client.post(
            self.create_url,
            data=self.payload_with(target_language=self.english.pk),
        )

        response = self.client.get(self.list_url)
        pairs = re.findall(
            r'<span class="cover__lang">([^<]+)</span>',
            response.content.decode(),
        )

        self.assertEqual(sorted(pairs), ["JA → EN", "JA → ES"])


class LanguageRequiredTests(AlbumLanguageTestCase):
    """CP-07.2 — Falta alguno de los dos idiomas — Flujo alternativo."""

    def test_a_missing_source_language_is_rejected(self):
        """CP-07.2 — Sin idioma de origen no se guarda y se informa."""
        self.sign_in()

        response = self.client.post(
            self.create_url, data=self.payload_with(source_language="")
        )

        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("source_language", response.context["form"].errors)
        self.assertContains(response, "Elige el idioma de origen.")

    def test_a_missing_target_language_is_rejected(self):
        """CP-07.2 — Sin idioma de destino no se guarda y se informa."""
        self.sign_in()

        response = self.client.post(
            self.create_url, data=self.payload_with(target_language="")
        )

        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("target_language", response.context["form"].errors)
        self.assertContains(response, "Elige el idioma de destino.")

    def test_a_language_outside_the_catalogue_is_rejected(self):
        """CP-07.2 — Un idioma inexistente enviado en el POST se rechaza."""
        self.sign_in()
        missing = Language.objects.order_by("-pk").first().pk + 1000

        response = self.client.post(
            self.create_url, data=self.payload_with(source_language=missing)
        )

        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("source_language", response.context["form"].errors)


class SameLanguageRuleTests(AlbumLanguageTestCase):
    """El idioma de destino debe diferir del de origen.

    Un álbum con el mismo idioma en ambos extremos no describe ninguna
    traducción posible, así que es un error del usuario y no una preferencia.
    """

    def test_the_same_language_on_both_sides_is_rejected(self):
        """Origen igual a destino no crea el álbum."""
        self.sign_in()

        response = self.client.post(
            self.create_url,
            data=self.payload_with(target_language=self.japanese.pk),
        )

        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_the_error_is_shown_on_the_target_language(self):
        """El error se muestra en el campo que hay que cambiar."""
        self.sign_in()

        response = self.client.post(
            self.create_url,
            data=self.payload_with(target_language=self.japanese.pk),
        )

        self.assertIn("target_language", response.context["form"].errors)
        self.assertNotIn("source_language", response.context["form"].errors)
        self.assertContains(response, "debe ser distinto del de origen")

    def test_two_variants_of_the_same_script_are_allowed(self):
        """Dos códigos distintos del catálogo sí se aceptan.

        El caso que podría parecerse a "el mismo idioma" —de chino
        simplificado a otra variante— son entradas distintas del catálogo, y
        la regla no debe bloquearlo.
        """
        self.sign_in()
        simplified = Language.objects.get(code="zh-hans")

        self.client.post(
            self.create_url,
            data=self.payload_with(
                source_language=simplified.pk, target_language=self.spanish.pk
            ),
        )

        self.assertEqual(Album.objects.count(), 1)


class RenameIsUnaffectedByTheLanguageRuleTests(AlbumLanguageTestCase):
    """El renombrado de HU-06 no pasa por la regla de idiomas.

    AlbumRenameForm no hereda de AlbumForm y solo expone el título, así que su
    clean() es el de ModelForm y la comprobación de idiomas no interviene.
    Estas pruebas fijan esa separación: si alguien hiciera que AlbumRenameForm
    heredara de AlbumForm, un álbum guardado antes de esta regla dejaría de
    poder renombrarse.
    """

    def test_the_rename_form_does_not_inherit_the_language_rule(self):
        """El formulario de renombrado no comparte el clean() de AlbumForm."""
        self.assertNotIsInstance(AlbumRenameForm(), AlbumForm)
        self.assertEqual(list(AlbumRenameForm().fields), ["title"])

    def test_an_album_can_be_renamed_whatever_its_languages(self):
        """Renombrar funciona sin que los idiomas se revaliden."""
        album = Album.objects.create(
            owner=self.owner,
            title="Título anterior",
            source_language=self.japanese,
            target_language=self.spanish,
        )
        self.sign_in()

        self.client.post(
            reverse("albums:rename", kwargs={"pk": album.pk}),
            data={"title": "Título nuevo"},
        )

        album.refresh_from_db()
        self.assertEqual(album.title, "Título nuevo")
        self.assertEqual(album.source_language, self.japanese)
        self.assertEqual(album.target_language, self.spanish)

    def test_reusing_the_album_form_on_a_saved_album_still_validates(self):
        """Un álbum ya guardado con idiomas válidos supera AlbumForm.clean().

        Es el escenario de reutilización: si en una etapa futura se usara
        AlbumForm para editar un álbum existente, la regla nueva no debe
        invalidar datos que ya eran correctos.
        """
        album = Album.objects.create(
            owner=self.owner,
            title="Álbum guardado",
            source_language=self.japanese,
            target_language=self.spanish,
        )

        form = AlbumForm(
            instance=album,
            data={
                "title": album.title,
                "source_language": album.source_language.pk,
                "target_language": album.target_language.pk,
            },
        )

        self.assertTrue(form.is_valid(), form.errors.as_data())


class LanguagePillMarkupTests(AlbumLanguageTestCase):
    """Los selectores son grupos de radios nativos, no botones."""

    def test_the_selectors_are_native_radio_groups(self):
        """Cada idioma es un radio real dentro de un fieldset con leyenda."""
        self.sign_in()

        response = self.client.get(self.create_url)
        content = response.content.decode()

        self.assertNotIn("<select", content)
        self.assertEqual(content.count('class="pill-field"'), 2)
        self.assertEqual(content.count("<legend"), 2)
        pattern = r'type="radio"[^>]*name="(source|target)_language"'
        radios = re.findall(pattern, content)
        self.assertEqual(len(radios), Language.objects.count() * 2)

    def test_no_language_is_preselected(self):
        """Ningún idioma viene marcado de antemano.

        Marcar uno por defecto haría que un descuido creara el álbum con un
        idioma que el usuario nunca eligió.
        """
        self.sign_in()

        response = self.client.get(self.create_url)

        self.assertNotIn("checked", response.content.decode())

    def test_each_radio_is_labelled(self):
        """Cada radio tiene su etiqueta asociada por for/id."""
        self.sign_in()

        content = self.client.get(self.create_url).content.decode()
        ids = re.findall(r'type="radio"[^>]*id="([^"]+)"', content)
        labels = re.findall(r'<label class="pill" for="([^"]+)"', content)

        self.assertEqual(sorted(ids), sorted(labels))
        self.assertEqual(len(ids), Language.objects.count() * 2)
