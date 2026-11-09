"""Pruebas de la vista previa traducida dentro del workspace (HU-87)."""

import re
from pathlib import Path

from django.conf import settings

from albums.models import TextRegion
from albums.tests.test_translation_review import ReviewTestCase
from albums.views import timestamp_version


class TranslatedPreviewTests(ReviewTestCase):
    """CP-87.1 a CP-87.7 — Vista previa de traducciones sobre la página."""

    def preview_for(self, response, region):
        """Busca la presentación calculada para una región concreta."""
        return next(
            item
            for item in response.context["preview_regions"]
            if item["region_pk"] == region.pk
        )

    def script(self):
        """Devuelve el JavaScript progresivo del workspace."""
        return (Path(settings.BASE_DIR) / "static" / "js" / "app.js").read_text(
            encoding="utf-8"
        )

    def stylesheet(self):
        """Devuelve los estilos usados por la vista previa."""
        return (Path(settings.BASE_DIR) / "static" / "css" / "app.css").read_text(
            encoding="utf-8"
        )

    def test_original_and_translated_selector_controls_the_decorative_layer(self):
        """CP-87.1 — El selector alterna una capa decorativa con traducciones."""
        response = self.workspace()

        self.assertContains(response, 'aria-label="Vista de la página"')
        self.assertContains(response, 'data-preview-mode="original"')
        self.assertContains(response, 'data-preview-mode="translated"')
        self.assertContains(response, "data-page-overlay")
        self.assertContains(response, 'aria-hidden="true"')
        self.assertContains(response, "[ES] こんにちは")
        self.assertRegex(
            response.content.decode(),
            re.compile(r"--preview-font-ratio: \d+(?:\.\d+)?;"),
        )
        self.assertIn('writePreference("panelingo.preview", mode)', self.script())

    def test_long_and_impossible_text_are_reflowed_or_warned(self):
        """CP-87.2 — Reduce, parte líneas y avisa si 8 px no bastan."""
        self.first.translation = (
            "Esta traducción es mucho más larga que el texto japonés original"
        )
        self.first.save(update_fields=["translation"])
        self.second.translation = "palabrainterminablementeextensísima"
        self.second.width = 18
        self.second.save(update_fields=["translation", "width"])

        response = self.workspace()
        first = self.preview_for(response, self.first)
        second = self.preview_for(response, self.second)

        self.assertGreater(len(first["lines"]), 1)
        self.assertGreaterEqual(first["font_size"], 8)
        self.assertFalse(second["fits"])
        self.assertEqual(second["font_size"], 8)
        self.assertContains(response, "El texto no cabe")
        self.assertContains(response, "is-overflowing")

    def test_dialogue_and_narration_use_local_comic_neue_variants(self):
        """CP-87.3 — Diálogo regular, narración cursiva y caracteres españoles."""
        self.second.kind = TextRegion.Kind.NARRATION
        self.second.translation = "¿El niño llegó? ¡Sí!"
        self.second.save(update_fields=["kind", "translation"])

        response = self.workspace()
        css = self.stylesheet()

        self.assertContains(response, "¿El niño llegó? ¡Sí!")
        self.assertContains(response, "page-overlay__region--narration")
        self.assertIn('font-family: "Comic Neue"', css)
        self.assertIn("ComicNeue-Regular.ttf", css)
        self.assertIn("ComicNeue-Italic.ttf", css)
        self.assertIn("font-style: italic", css)

    def test_translation_autosave_returns_and_renders_a_new_preview(self):
        """CP-87.4 — Guardar devuelve las líneas y JavaScript actualiza la capa."""
        response = self.client.post(
            self.first.get_translation_url(),
            {
                "text": "¿Nueva traducción?",
                "version": timestamp_version(self.first.translated_at),
            },
            HTTP_X_AUTOSAVE="1",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        preview = response.json()["preview"]
        self.assertEqual(preview["status"], "translated")
        self.assertEqual(" ".join(preview["lines"]), "¿Nueva traducción?")
        script = self.script()
        self.assertIn("updatePagePreview(result.payload.preview)", script)
        self.assertIn('document.createElement("span")', script)

    def test_untranslated_uses_source_and_skipped_region_has_no_overlay(self):
        """CP-87.5 — Sin traducir muestra origen; «No traducir» no superpone nada."""
        TextRegion.objects.filter(pk=self.first.pk).update(
            translation="",
            machine_translation="",
            translation_status=TextRegion.TranslationStatus.UNTRANSLATED,
        )
        self.client.post(self.second.get_skip_translation_url())
        self.first.refresh_from_db()
        self.second.refresh_from_db()

        response = self.workspace()
        first = self.preview_for(response, self.first)
        second = self.preview_for(response, self.second)

        self.assertEqual(first["status"], "untranslated")
        self.assertEqual(" ".join(first["lines"]), self.first.final_text)
        self.assertEqual(second["status"], "skipped")
        self.assertContains(response, "Sin traducir")
        self.assertNotContains(
            response,
            f'data-preview-region="{self.second.pk}"',
        )

    def test_preview_font_uses_container_units_and_shares_the_zoom_target(self):
        """CP-87.6 — Texto y cajas escalan dentro del mismo lienzo del zoom."""
        response = self.workspace()
        css = self.stylesheet()

        self.assertContains(response, "data-zoom-target")
        self.assertContains(response, "data-page-overlay")
        self.assertIn("container-type: inline-size", css)
        self.assertIn("calc(var(--preview-font-ratio) * 1cqw)", css)
        self.assertIn(
            'figure.style.width = ZOOM_BASE_WIDTH * zoom + "px"', self.script()
        )

    def test_selector_is_keyboard_operable_and_preview_is_not_announced_twice(self):
        """CP-87.7 — Botones nativos, flechas y capa aria-hidden accesible."""
        response = self.workspace()
        script = self.script()

        self.assertContains(response, '<button type="button" aria-pressed="true"')
        self.assertContains(response, '<button type="button" aria-pressed="false"')
        self.assertContains(response, 'class="page-overlay" aria-hidden="true"')
        self.assertIn("ArrowLeft|ArrowRight|Home|End", script)
        self.assertIn("button.focus()", script)
