"""Pruebas del algoritmo de ajuste de texto de la HU-87."""

from django.test import SimpleTestCase
from PIL import ImageFont

from albums.typesetting import (
    MIN_FONT_SIZE,
    REGULAR_FONT_PATH,
    fit_text,
    lines_fit,
)


class FitTextTests(SimpleTestCase):
    """CP-87.2 y CP-87.3 — Ajuste tipográfico puro y determinista."""

    def test_short_text_keeps_the_largest_size(self):
        """CP-87.2 — Una frase corta conserva el tamaño máximo solicitado."""
        font_size, lines = fit_text("¡Hola!", 220, 90, REGULAR_FONT_PATH, 40)

        self.assertEqual(font_size, 40)
        self.assertEqual(lines, ["¡Hola!"])

    def test_long_text_wraps_without_cutting_words_and_reduces_size(self):
        """CP-87.2 — El ajuste conserva palabras y reduce hasta caber."""
        text = "Una traducción bastante más larga dentro del mismo globo"

        font_size, lines = fit_text(text, 130, 64, REGULAR_FONT_PATH, 34)
        font = ImageFont.truetype(str(REGULAR_FONT_PATH), font_size)

        self.assertLess(font_size, 34)
        self.assertEqual(" ".join(lines), text)
        self.assertTrue(lines_fit(lines, font, 130, 64))

    def test_explicit_line_break_is_preserved(self):
        """CP-87.2 — Los saltos escritos por el traductor no se fusionan."""
        _font_size, lines = fit_text(
            "Primera línea\nSegunda línea",
            400,
            100,
            REGULAR_FONT_PATH,
            26,
        )

        self.assertEqual(lines, ["Primera línea", "Segunda línea"])

    def test_unbreakable_word_reports_that_the_minimum_does_not_fit(self):
        """CP-87.2 — Una palabra demasiado ancha llega a 8 px sin cortarse."""
        word = "extraordinariamentelarguísima"

        font_size, lines = fit_text(
            word,
            20,
            100,
            REGULAR_FONT_PATH,
            30,
            MIN_FONT_SIZE,
        )
        font = ImageFont.truetype(str(REGULAR_FONT_PATH), font_size)

        self.assertEqual(font_size, MIN_FONT_SIZE)
        self.assertEqual(lines, [word])
        self.assertFalse(lines_fit(lines, font, 20, 100))

    def test_font_supports_spanish_characters(self):
        """CP-87.3 — Tildes, ñ y signos de apertura se miden sin perderse."""
        text = "¿El pingüino soñó? ¡Sí, señor!"

        _font_size, lines = fit_text(text, 300, 100, REGULAR_FONT_PATH, 28)

        self.assertEqual(" ".join(lines), text)
