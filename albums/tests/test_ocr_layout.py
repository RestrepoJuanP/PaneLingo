"""Pruebas unitarias de las reglas de maquetación de regiones (HU-12, ADR-001)."""

from django.test import SimpleTestCase
from PIL import Image, ImageDraw

from albums.ocr.base import DetectedRegion
from albums.ocr.layout import (
    clamp_to_page,
    is_balloon,
    is_right_to_left,
    merge_lines_into_regions,
    sort_in_reading_order,
)


def box(x, y, width, height, text="", confidence=None):
    """Atajo para crear una caja detectada."""
    return DetectedRegion(x, y, width, height, text, confidence)


class ReadingOrderTests(SimpleTestCase):
    """CP-12.2 — Las regiones se numeran en el orden de lectura del idioma."""

    def setUp(self):
        """Dos globos en la fila superior y uno en la inferior."""
        self.top_left = box(50, 40, 200, 100)
        self.top_right = box(500, 60, 200, 100)
        self.bottom = box(280, 600, 200, 100)
        self.regions = [self.bottom, self.top_left, self.top_right]

    def test_japanese_reads_right_to_left(self):
        """CP-12.2 — En japonés la fila se lee de derecha a izquierda."""
        ordered = sort_in_reading_order(self.regions, right_to_left=True)

        self.assertEqual(ordered, [self.top_right, self.top_left, self.bottom])

    def test_other_languages_read_left_to_right(self):
        """CP-12.2 — Flujo alternativo: en coreano o inglés, de izquierda a derecha."""
        ordered = sort_in_reading_order(self.regions, right_to_left=False)

        self.assertEqual(ordered, [self.top_left, self.top_right, self.bottom])

    def test_only_japanese_is_right_to_left(self):
        """CP-12.2 — Solo el japonés del catálogo se lee de derecha a izquierda."""
        self.assertTrue(is_right_to_left("ja"))
        for code in ("ko", "zh-hans", "en", "es"):
            with self.subTest(code=code):
                self.assertFalse(is_right_to_left(code))

    def test_rows_are_read_top_to_bottom(self):
        """CP-12.2 — Las filas se leen siempre de arriba abajo."""
        ordered = sort_in_reading_order(
            [self.bottom, self.top_right], right_to_left=False
        )

        self.assertEqual(ordered, [self.top_right, self.bottom])


class MergeLinesTests(SimpleTestCase):
    """CP-12.1 — Las líneas de un mismo globo forman una sola región."""

    def test_adjacent_vertical_lines_become_one_region(self):
        """CP-12.1 — Dos columnas pegadas se funden en un globo."""
        right_column = box(130, 100, 30, 200, "こんにちは", 0.9)
        left_column = box(95, 100, 30, 180, "せかい", 0.7)

        regions = merge_lines_into_regions([left_column, right_column])

        self.assertEqual(len(regions), 1)
        merged = regions[0]
        self.assertEqual(
            (merged.x, merged.y, merged.right, merged.bottom), (95, 100, 160, 300)
        )
        # Texto vertical: la columna de la derecha se lee primero.
        self.assertEqual(merged.text, "こんにちは\nせかい")
        self.assertAlmostEqual(merged.confidence, 0.8)

    def test_distant_lines_stay_separate(self):
        """CP-12.1 — Flujo alternativo: dos globos separados no se mezclan."""
        first = box(10, 10, 200, 30, "Hola")
        second = box(10, 400, 200, 30, "Adiós")

        regions = merge_lines_into_regions([first, second])

        self.assertEqual(len(regions), 2)

    def test_merging_is_transitive(self):
        """CP-12.1 — A toca a B y B toca a C: las tres forman un globo."""
        lines = [
            box(10, 10, 200, 30, "uno"),
            box(10, 75, 200, 30, "tres"),
            box(10, 42, 200, 30, "dos"),
        ]

        regions = merge_lines_into_regions(lines)

        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0].text, "uno\ndos\ntres")

    def test_no_lines_means_no_regions(self):
        """CP-12.3 — Sin líneas detectadas no hay regiones."""
        self.assertEqual(merge_lines_into_regions([]), [])


class ClampTests(SimpleTestCase):
    """CP-12.2 — El resaltado nunca se sale de la página."""

    def test_box_partly_outside_is_trimmed(self):
        """CP-12.2 — Una caja que sobresale se recorta al borde."""
        clamped = clamp_to_page(box(-10, 90, 50, 30), page_width=100, page_height=100)

        self.assertEqual(
            (clamped.x, clamped.y, clamped.width, clamped.height), (0, 90, 40, 10)
        )

    def test_box_fully_outside_is_discarded(self):
        """CP-12.2 — Flujo alternativo: una caja fuera de la página se descarta."""
        self.assertIsNone(clamp_to_page(box(150, 10, 20, 20), 100, 100))


class RegionKindTests(SimpleTestCase):
    """CP-12.1 — Cada región se guarda con su tipo (supuesto S3)."""

    def setUp(self):
        """Página blanca con texto negro y un cuadro gris a la derecha."""
        self.image = Image.new("RGB", (400, 200), "white")
        draw = ImageDraw.Draw(self.image)
        draw.rectangle((20, 20, 180, 120), fill="white", outline="black")
        draw.text((40, 50), "Hola, mundo", fill="black")
        draw.rectangle((220, 20, 380, 120), fill=(150, 140, 120))

    def test_white_background_is_a_balloon(self):
        """CP-12.1 — Fondo blanco con texto: globo de diálogo."""
        self.assertTrue(is_balloon(self.image, box(20, 20, 160, 100)))

    def test_dark_background_is_a_narration_box(self):
        """CP-12.1 — Flujo alternativo: fondo gris o de color: cuadro narrativo."""
        self.assertFalse(is_balloon(self.image, box(220, 20, 160, 100)))
