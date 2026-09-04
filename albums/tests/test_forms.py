"""Pruebas del formulario de creación de álbumes (HU-05)."""

from django.test import TestCase

from albums.forms import AlbumForm
from albums.models import Language


class AlbumFormTestCase(TestCase):
    """Base común: los idiomas del catálogo y unos datos válidos."""

    def setUp(self):
        """Prepara los idiomas y el conjunto de datos válido."""
        self.japanese = Language.objects.get(code="ja")
        self.spanish = Language.objects.get(code="es")
        self.valid_data = {
            "title": "Neon Yokai Bureau",
            "source_language": self.japanese.pk,
            "target_language": self.spanish.pk,
        }

    def data_with(self, **overrides):
        """Devuelve los datos válidos con los campos indicados sustituidos."""
        payload = self.valid_data.copy()
        payload.update(overrides)
        return payload


class AlbumFormValidTests(AlbumFormTestCase):
    """El formulario acepta datos completos y correctos."""

    def test_form_is_valid_with_complete_data(self):
        """CP-05.1 — El formulario acepta los datos requeridos."""
        form = AlbumForm(data=self.valid_data)

        self.assertTrue(form.is_valid(), form.errors.as_data())

    def test_the_title_is_trimmed(self):
        """Los espacios sobrantes del título se recortan."""
        form = AlbumForm(data=self.data_with(title="  Salt & Static  "))
        self.assertTrue(form.is_valid(), form.errors.as_data())

        self.assertEqual(form.cleaned_data["title"], "Salt & Static")

    def test_the_form_does_not_expose_the_owner(self):
        """El propietario no puede llegar desde el formulario.

        Es la barrera de diseño que impide crear álbumes a nombre de otra
        cuenta: sin campo owner no hay nada que manipular en el POST.
        """
        self.assertNotIn("owner", AlbumForm().fields)


class AlbumFormValidationTests(AlbumFormTestCase):
    """Validaciones del formulario de álbum."""

    def test_missing_title_is_rejected(self):
        """CP-05.2 — Falta el título — Flujo alternativo."""
        form = AlbumForm(data=self.data_with(title=""))

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_a_blank_title_is_rejected(self):
        """CP-05.2 — Un título de solo espacios no vale como título."""
        form = AlbumForm(data=self.data_with(title="     "))

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_an_overlong_title_is_rejected(self):
        """CP-05.2 — El título no puede superar los 120 caracteres."""
        form = AlbumForm(data=self.data_with(title="x" * 121))

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_missing_source_language_is_rejected(self):
        """CP-05.2 — Falta el idioma de origen — Flujo alternativo."""
        form = AlbumForm(data=self.data_with(source_language=""))

        self.assertFalse(form.is_valid())
        self.assertIn("source_language", form.errors)

    def test_missing_target_language_is_rejected(self):
        """CP-05.2 — Falta el idioma de destino — Flujo alternativo."""
        form = AlbumForm(data=self.data_with(target_language=""))

        self.assertFalse(form.is_valid())
        self.assertIn("target_language", form.errors)

    def test_a_language_outside_the_catalogue_is_rejected(self):
        """CP-05.2 — Un idioma que no existe en el catálogo se rechaza."""
        missing = Language.objects.order_by("-pk").first().pk + 1000

        form = AlbumForm(data=self.data_with(source_language=missing))

        self.assertFalse(form.is_valid())
        self.assertIn("source_language", form.errors)

    def test_invalid_field_gets_its_accessibility_attributes(self):
        """Un campo con error queda asociado a su bloque de errores."""
        form = AlbumForm(data=self.data_with(title=""))
        self.assertFalse(form.is_valid())

        attrs = form.fields["title"].widget.attrs

        self.assertEqual(attrs["aria-describedby"], "id_title-error")
        self.assertEqual(attrs["aria-invalid"], "true")
