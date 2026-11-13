"""Fondo detrás del texto maquetado (corrección de HU-89 y HU-90).

Cuando la limpieza no puede borrar el texto original de una región (queda en
«Limpieza manual»), la traducción se dibujaba encima de él y no se leía. El
fondo automático lo tapa con blanco en la vista previa, el editor y el PNG
exportado; el traductor puede forzarlo o quitarlo.
"""

from PIL import Image

from albums.models import TextRegion
from albums.tests.test_typesetting_editor import (
    INK,
    WHITE,
    TypesettingTestCase,
    png_bytes,
)
from albums.typesetting import (
    TEXT_BACKGROUND_COLOR,
    background_for,
    draw_layout,
    layout_for_region,
    preview_for_region,
    render_page,
)


class TextBackgroundTestCase(TypesettingTestCase):
    """Base: la imagen limpia conserva el texto original de la región 1."""

    def keep_original_text_in_cleaned_image(self):
        """Simula una región en «Limpieza manual»: su texto sigue visible."""
        x, y, width, height = self.BOXES[1]
        cleaned = Image.new("RGB", (self.page.width, self.page.height), WHITE)
        cleaned.paste(INK, (x + 10, y + 10, x + width - 10, y + height - 10))
        with self.page.cleaned_image.open("wb") as image_file:
            image_file.write(png_bytes(cleaned))
        self.first.cleaning_status = TextRegion.CleaningStatus.MANUAL
        self.first.save(update_fields=["cleaning_status"])

    def ink_pixels_outside_text(self, image):
        """Cuenta píxeles de tinta original en una franja sin texto nuevo.

        La franja es el margen superior de la caja de la región 1, donde la
        traducción centrada no llega: solo puede haber tinta si el texto
        original sigue a la vista.
        """
        x, y, width, _height = self.BOXES[1]
        strip = image.crop((x + 12, y + 12, x + width - 12, y + 16))
        return sum(1 for pixel in strip.getdata() if pixel == INK)


class AutomaticBackgroundTests(TextBackgroundTestCase):
    """El fondo automático solo aparece donde el texto original sigue."""

    def test_clean_region_has_no_background(self):
        """CP-89.1 — Una región limpia se maqueta sin fondo."""
        self.assertEqual(background_for(self.first), "")
        self.assertEqual(layout_for_region(self.first)["background"], "")

    def test_manual_cleaning_region_gets_a_white_background(self):
        """CP-88.2 — Con limpieza manual, la traducción lleva fondo blanco."""
        self.keep_original_text_in_cleaned_image()

        layout = layout_for_region(self.first)
        preview = preview_for_region(self.first)

        self.assertEqual(layout["background"], TEXT_BACKGROUND_COLOR)
        self.assertEqual(layout["text_background"], "auto")
        self.assertIn(
            f"--preview-background: {TEXT_BACKGROUND_COLOR}", preview["style"]
        )

    def test_exported_page_covers_the_original_text(self):
        """CP-90.2 — El PNG no muestra el texto original bajo la traducción."""
        self.keep_original_text_in_cleaned_image()

        image = render_page(self.page)

        self.assertEqual(self.ink_pixels_outside_text(image), 0)

    def test_without_background_the_original_text_shows(self):
        """CP-90.2 — Con «Sin fondo», el original sigue a la vista."""
        self.keep_original_text_in_cleaned_image()
        self.first.text_background = TextRegion.TextBackground.NONE
        self.first.save(update_fields=["text_background"])

        image = render_page(self.page)

        self.assertGreater(self.ink_pixels_outside_text(image), 0)
        self.assertIn(
            "--preview-background: transparent", preview_for_region(self.first)["style"]
        )


class BackgroundChoiceTests(TextBackgroundTestCase):
    """El traductor elige el fondo desde el panel de propiedades."""

    def test_editor_offers_the_three_background_options(self):
        """CP-89.4 — El panel ofrece Automático, Blanco y Sin fondo."""
        response = self.client.get(
            self.page.get_absolute_url(), {"paso": "maquetacion"}
        )

        for value in ("auto", "white", "none"):
            self.assertContains(
                response, f'name="text_background" id="ts-background-{value}"'
            )
        self.assertContains(response, 'data-text-background="auto"')

    def test_saving_a_white_background(self):
        """CP-89.4 — Elegir «Blanco» se guarda y pinta el fondo."""
        response = self.post_layout(self.second, {"text_background": "white"})

        self.assertEqual(response.status_code, 200)
        self.second.refresh_from_db()
        self.assertEqual(self.second.text_background, TextRegion.TextBackground.WHITE)
        self.assertEqual(background_for(self.second), TEXT_BACKGROUND_COLOR)

    def test_rejects_an_unknown_background(self):
        """CP-89.4 — Un valor desconocido se rechaza sin guardar nada."""
        response = self.post_layout(self.second, {"text_background": "red"})

        self.assertEqual(response.status_code, 400)
        self.second.refresh_from_db()
        self.assertEqual(self.second.text_background, TextRegion.TextBackground.AUTO)

    def test_reset_returns_to_automatic(self):
        """CP-89.6 — Restablecer vuelve al fondo automático."""
        self.second.text_background = TextRegion.TextBackground.NONE
        self.second.save(update_fields=["text_background"])
        self.second.refresh_from_db()

        self.client.post(self.second.get_layout_reset_url())

        self.second.refresh_from_db()
        self.assertEqual(self.second.text_background, TextRegion.TextBackground.AUTO)

    def test_frozen_layouts_without_background_still_render(self):
        """CP-90.6 — Una exportación anterior al fondo se dibuja igual."""
        layout = layout_for_region(self.first, text="Hola")
        layout.pop("background")
        layout.pop("text_background")

        canvas = Image.new("RGB", (self.page.width, self.page.height), WHITE)
        draw_layout(canvas, layout)

        self.assertNotEqual(canvas.getbbox(), None)
