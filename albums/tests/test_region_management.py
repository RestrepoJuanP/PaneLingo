"""Pruebas de eliminación y exclusión de regiones (HU-86)."""

from django.urls import reverse
from django.utils import timezone

from albums.exporting import build_export_snapshot
from albums.models import ComicPage, TextRegion
from albums.tests.test_translation_review import ReviewTestCase
from albums.translating import translatable_regions
from albums.translation_review import approve_translation


class DeleteRegionTests(ReviewTestCase):
    """CP-86.1 y CP-86.2 — Eliminar y restaurar una región."""

    def delete(self, region, follow=False):
        """Elimina la región mediante su acción privada."""
        return self.client.post(region.get_delete_url(), follow=follow)

    def restore(self, region_pk, follow=False):
        """Restaura el identificador guardado en la sesión."""
        return self.client.post(
            reverse("albums:region_restore", args=[region_pk]),
            follow=follow,
        )

    def test_delete_removes_the_region_and_renumbers_the_following_ones(self):
        """CP-86.1 — El falso positivo desaparece y el orden queda consecutivo."""
        deleted_pk = self.first.pk

        response = self.delete(self.first, follow=True)

        self.assertFalse(TextRegion.objects.filter(pk=deleted_pk).exists())
        self.second.refresh_from_db()
        self.assertEqual(self.second.reading_order, 1)
        self.assertContains(response, "Región eliminada.")
        self.assertContains(response, "Deshacer")
        self.assertContains(
            response, reverse("albums:region_restore", args=[deleted_pk])
        )

    def test_undo_restores_every_edit_and_the_original_reading_order(self):
        """CP-86.2 — Deshacer recupera texto, corrección, traducción y estado."""
        corrected_at = timezone.now()
        approved_at = timezone.now()
        TextRegion.objects.filter(pk=self.first.pk).update(
            corrected_text="こんにちは！",
            is_corrected=True,
            corrected_at=corrected_at,
            translation="¡Hola!",
            machine_translation="Hola",
            translation_status=TextRegion.TranslationStatus.APPROVED,
            translated_at=corrected_at,
            approved_at=approved_at,
            needs_review=True,
        )
        self.first.refresh_from_db()
        deleted_pk = self.first.pk

        self.delete(self.first)
        response = self.restore(deleted_pk, follow=True)

        restored = TextRegion.objects.get(pk=deleted_pk)
        self.second.refresh_from_db()
        self.assertEqual(restored.reading_order, 1)
        self.assertEqual(self.second.reading_order, 2)
        self.assertEqual(restored.corrected_text, "こんにちは！")
        self.assertEqual(restored.translation, "¡Hola!")
        self.assertEqual(restored.machine_translation, "Hola")
        self.assertEqual(
            restored.translation_status,
            TextRegion.TranslationStatus.APPROVED,
        )
        self.assertEqual(restored.approved_at, approved_at)
        self.assertTrue(restored.needs_review)
        self.assertContains(response, "Región 1 restaurada.")

    def test_undo_expires_after_another_page_change(self):
        """CP-86.2 — La instantánea no pisa cambios posteriores de la página."""
        deleted_pk = self.first.pk
        self.delete(self.first)
        TextRegion.objects.filter(pk=self.second.pk).update(source_text="変更")

        response = self.restore(deleted_pk, follow=True)

        self.assertFalse(TextRegion.objects.filter(pk=deleted_pk).exists())
        self.assertContains(response, "la página cambió")

    def test_delete_confirmation_is_accessible_and_uses_post(self):
        """CP-86.1 — La interfaz confirma el borrado en un modal accesible."""
        response = self.workspace()

        self.assertContains(response, f'id="eliminar-region-{self.first.pk}"')
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'aria-modal="true"')
        self.assertContains(response, f'action="{self.first.get_delete_url()}"')
        self.assertContains(response, "¿Eliminar la región 1?")


class SkipTranslationTests(ReviewTestCase):
    """CP-86.3 a CP-86.5 — Conservar o volver a traducir una región."""

    def skip(self, region):
        """Marca la región como «No traducir» y vuelve a leerla."""
        response = self.client.post(region.get_skip_translation_url())
        region.refresh_from_db()
        self.page.refresh_from_db()
        return response

    def enable(self, region):
        """Devuelve la región al flujo de traducción y vuelve a leerla."""
        response = self.client.post(region.get_enable_translation_url())
        region.refresh_from_db()
        self.page.refresh_from_db()
        return response

    def test_skipped_region_keeps_source_and_is_excluded_from_every_flow(self):
        """CP-86.3 — No va a IA, aprobación ni exportación y conserva origen."""
        approve_translation(self.first)
        self.first.refresh_from_db()
        source_text = self.second.source_text

        self.skip(self.second)

        self.assertTrue(self.second.skip_translation)
        self.assertEqual(self.second.source_text, source_text)
        self.assertFalse(self.second.needs_translation)
        self.assertEqual(self.second.translation, "")
        self.assertEqual(self.second.machine_translation, "")
        self.assertEqual(
            self.second.translation_status,
            TextRegion.TranslationStatus.UNTRANSLATED,
        )
        self.assertEqual(translatable_regions(self.page), [self.first])
        self.assertEqual(self.page.status, ComicPage.Status.APPROVED)
        snapshot, skipped_count = build_export_snapshot(self.album)
        self.assertEqual(len(snapshot["regions"]), 1)
        self.assertEqual(skipped_count, 0)

    def test_skipped_region_shows_its_chip_and_original_text_explanation(self):
        """CP-86.3 — El bloque explica que el texto original queda intacto."""
        self.skip(self.second)

        response = self.workspace()

        self.assertContains(response, "No traducir")
        self.assertContains(response, "Traducir esta región")
        self.assertContains(response, "no se traducirá")
        self.assertContains(response, "limpiará en la página final")
        self.assertNotContains(response, 'id="region-translation-2"')

    def test_enable_translation_returns_an_empty_pending_region(self):
        """CP-86.4 — Volver a traducir deja la región pendiente y sin propuesta."""
        self.skip(self.second)

        self.enable(self.second)

        self.assertFalse(self.second.skip_translation)
        self.assertTrue(self.second.needs_translation)
        self.assertEqual(self.second.translation, "")
        self.assertEqual(self.second.machine_translation, "")
        self.assertEqual(
            self.second.translation_status,
            TextRegion.TranslationStatus.UNTRANSLATED,
        )
        self.assertNotEqual(self.page.status, ComicPage.Status.APPROVED)

    def test_empty_text_and_skip_translation_remain_distinct_decisions(self):
        """CP-86.5 — Vaciar limpia la zona; «No traducir» conserva el original."""
        self.client.post(self.first.get_correct_url(), {"text": ""})
        self.skip(self.second)
        self.first.refresh_from_db()

        self.assertTrue(self.first.has_nothing_to_translate)
        self.assertFalse(self.first.skip_translation)
        self.assertFalse(self.second.has_nothing_to_translate)
        self.assertTrue(self.second.skip_translation)
        self.assertNotEqual(self.second.source_text, "")


class RegionManagementAccessTests(ReviewTestCase):
    """CP-86.6 — Todas las acciones mantienen aislamiento por propietario."""

    def setUp(self):
        """Crea una región ajena con texto y traducción."""
        super().setUp()
        self.foreign = TextRegion.objects.create(
            page=self.foreign_page,
            reading_order=1,
            x=10,
            y=10,
            width=50,
            height=40,
            source_text="秘密",
            translation="Secreto",
            translation_status=TextRegion.TranslationStatus.GENERATED,
        )

    def test_foreign_region_actions_return_not_found_without_changes(self):
        """CP-86.6 — Eliminar o alternar una región ajena responde 404."""
        urls = (
            self.foreign.get_delete_url(),
            self.foreign.get_skip_translation_url(),
            self.foreign.get_enable_translation_url(),
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url).status_code, 404)

        self.foreign.refresh_from_db()
        self.assertFalse(self.foreign.skip_translation)
        self.assertEqual(self.foreign.translation, "Secreto")

    def test_actions_reject_get_and_restore_without_a_session_snapshot(self):
        """CP-86.6 — Las acciones son POST y no revelan regiones borradas."""
        own_urls = (
            self.first.get_delete_url(),
            self.first.get_skip_translation_url(),
            self.first.get_enable_translation_url(),
            reverse("albums:region_restore", args=[self.first.pk]),
        )
        for url in own_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

        self.assertEqual(
            self.client.post(
                reverse("albums:region_restore", args=[self.foreign.pk])
            ).status_code,
            404,
        )
