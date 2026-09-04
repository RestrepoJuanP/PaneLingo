"""Pruebas de los modelos de la app albums."""

from django.db.models import ProtectedError
from django.test import TestCase

from accounts.models import User
from albums.models import Album, Language


class LanguageCatalogTests(TestCase):
    """El catálogo de idiomas lo siembra una migración de datos."""

    def test_seeded_languages_are_available(self):
        """Los ocho idiomas del mockup están en el catálogo."""
        codes = set(Language.objects.values_list("code", flat=True))

        self.assertEqual(
            codes,
            {"ja", "ko", "zh-hans", "fr", "en", "es", "de", "pt-br"},
        )

    def test_language_is_shown_by_its_name(self):
        """El idioma se representa por su nombre."""
        self.assertEqual(str(Language.objects.get(code="ja")), "Japonés")


class AlbumModelTestCase(TestCase):
    """Base común: una cuenta y un par de idiomas."""

    def setUp(self):
        """Crea el propietario y los idiomas del álbum de prueba."""
        self.owner = User.objects.create_user(
            email="mira@estudio.test",
            password="TraduccionSegura42",
            display_name="Mira Okonkwo",
        )
        self.japanese = Language.objects.get(code="ja")
        self.spanish = Language.objects.get(code="es")

    def make_album(self, title="Neon Yokai Bureau", owner=None, target=None):
        """Crea un álbum con los valores de prueba por defecto."""
        return Album.objects.create(
            owner=owner or self.owner,
            title=title,
            source_language=self.japanese,
            target_language=target or self.spanish,
        )


class AlbumModelTests(AlbumModelTestCase):
    """Comportamiento del modelo Album."""

    def test_album_is_shown_by_its_title(self):
        """El álbum se representa por su título."""
        self.assertEqual(str(self.make_album()), "Neon Yokai Bureau")

    def test_new_album_starts_as_a_draft(self):
        """Un álbum recién creado queda en borrador."""
        album = self.make_album()

        self.assertEqual(album.status, Album.Status.DRAFT)
        self.assertEqual(album.get_status_display(), "Borrador")

    def test_album_belongs_to_its_owner(self):
        """El álbum queda asociado a la cuenta de su propietario."""
        album = self.make_album()

        self.assertEqual(album.owner, self.owner)
        self.assertIn(album, self.owner.albums.all())

    def test_language_pair_is_shown_in_short_form(self):
        """El par de idiomas se muestra en formato corto."""
        self.assertEqual(self.make_album().language_pair, "JA → ES")

    def test_an_empty_album_reports_no_pages_or_progress(self):
        """Un álbum sin páginas no rompe ni divide por cero."""
        album = self.make_album()

        self.assertEqual(album.page_count, 0)
        self.assertEqual(album.progress_percentage, 0)

    def test_albums_are_listed_with_the_most_recent_first(self):
        """El orden por defecto es por fecha de actualización descendente."""
        older = self.make_album(title="Antiguo")
        newer = self.make_album(title="Reciente")
        older.title = "Antiguo, tocado después"
        older.save()

        self.assertEqual(list(Album.objects.all()), [older, newer])

    def test_the_same_title_is_allowed_for_different_language_pairs(self):
        """El título no es único: la misma obra puede ir a dos idiomas.

        Es una decisión deliberada, documentada en el docstring del modelo.
        """
        english = Language.objects.get(code="en")

        self.make_album(title="Neon Yokai Bureau")
        self.make_album(title="Neon Yokai Bureau", target=english)

        self.assertEqual(Album.objects.filter(title="Neon Yokai Bureau").count(), 2)

    def test_deleting_the_owner_deletes_their_albums(self):
        """Al borrar una cuenta desaparecen sus álbumes."""
        self.make_album()

        self.owner.delete()

        self.assertEqual(Album.objects.count(), 0)

    def test_a_language_in_use_cannot_be_removed(self):
        """Retirar un idioma del catálogo no puede borrar álbumes."""
        self.make_album()

        with self.assertRaises(ProtectedError):
            self.japanese.delete()

        self.assertEqual(Album.objects.count(), 1)
