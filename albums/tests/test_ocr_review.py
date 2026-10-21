"""Pruebas unitarias de las reglas de revisión del OCR (HU-13)."""

from django.test import SimpleTestCase

from albums.ocr.base import DetectedRegion
from albums.ocr.review import matches_source_script, needs_review

THRESHOLD = 0.70


def region(text, confidence=0.95):
    """Atajo para crear una región con texto y confianza."""
    return DetectedRegion(0, 0, 10, 10, text, confidence)


class SourceScriptTests(SimpleTestCase):
    """CP-13.2 — El texto se comprueba contra el alfabeto del idioma de origen."""

    def test_japanese_text_matches_a_japanese_album(self):
        """CP-13.2 — Kana y kanji son japonés."""
        for text in ("こんにちは", "カタカナ", "元気", "OK、ありがとう"):
            with self.subTest(text=text):
                self.assertTrue(matches_source_script(text, "ja"))

    def test_latin_text_does_not_match_a_japanese_album(self):
        """CP-13.2 — Flujo alternativo: solo letras latinas en un álbum japonés."""
        self.assertFalse(matches_source_script("Hello world", "ja"))

    def test_each_source_language_has_its_script(self):
        """CP-13.2 — Coreano, chino y los idiomas latinos tienen su alfabeto."""
        self.assertTrue(matches_source_script("안녕하세요", "ko"))
        self.assertFalse(matches_source_script("こんにちは", "ko"))
        self.assertTrue(matches_source_script("你好", "zh-hans"))
        self.assertTrue(matches_source_script("¡Hola, Camión!", "es"))
        self.assertFalse(matches_source_script("안녕", "en"))

    def test_text_without_letters_is_not_a_mismatch(self):
        """CP-13.2 — "!?", "…" o números no delatan otro idioma."""
        for text in ("!?", "…", "123", "♥"):
            with self.subTest(text=text):
                self.assertTrue(matches_source_script(text, "ja"))


class NeedsReviewTests(SimpleTestCase):
    """CP-13.3 y CP-13.5 — Cuándo una región se marca para revisión."""

    def test_confident_text_in_the_right_script_is_accepted(self):
        """CP-13.3 — Texto fiable: no necesita revisión."""
        self.assertFalse(needs_review(region("こんにちは", 0.95), "ja", THRESHOLD))

    def test_low_confidence_needs_review(self):
        """CP-13.3 — Por debajo del umbral se marca para revisión."""
        self.assertTrue(needs_review(region("こんにちは", 0.69), "ja", THRESHOLD))

    def test_the_threshold_itself_is_accepted(self):
        """CP-13.3 — Justo en el umbral no se marca."""
        self.assertFalse(needs_review(region("こんにちは", 0.70), "ja", THRESHOLD))

    def test_missing_confidence_needs_review(self):
        """CP-13.3 — Sin confianza informada no se puede dar por bueno."""
        self.assertTrue(needs_review(region("こんにちは", None), "ja", THRESHOLD))

    def test_empty_text_needs_review(self):
        """CP-13.5 — Una región sin texto queda marcada para revisión."""
        self.assertTrue(needs_review(region("  ", 0.99), "ja", THRESHOLD))

    def test_wrong_script_needs_review(self):
        """CP-13.2 — Texto fiable pero en otro alfabeto: se revisa."""
        self.assertTrue(needs_review(region("Hello", 0.99), "ja", THRESHOLD))
