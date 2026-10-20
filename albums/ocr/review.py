"""Reglas que marcan una región para revisión manual (HU-13, CA-13.2 a 13.5).

Una región se marca cuando no se puede confiar en su texto sin que alguien lo
mire: el OCR no leyó nada, lo leyó con poca confianza o lo leyó en un alfabeto
que no es el del idioma de origen del álbum.
"""

import unicodedata

# Fragmentos del nombre Unicode de las letras de cada idioma de origen. Se usa
# el nombre del carácter y no rangos de códigos para que la regla se lea sola.
# Los idiomas que no aparecen se escriben con el alfabeto latino.
SCRIPT_NAME_PARTS = {
    "ja": ("HIRAGANA", "KATAKANA", "CJK UNIFIED IDEOGRAPH"),
    "ko": ("HANGUL",),
    "zh-hans": ("CJK UNIFIED IDEOGRAPH",),
}
LATIN_NAME_PARTS = ("LATIN",)


def script_name_parts(language_code):
    """Devuelve los fragmentos de nombre Unicode del alfabeto de un idioma."""
    return SCRIPT_NAME_PARTS.get(language_code, LATIN_NAME_PARTS)


def matches_source_script(text, language_code):
    """Indica si el texto está escrito en el alfabeto del idioma de origen.

    Es la forma en que PaneLingo cumple CA-13.2: Azure detecta el idioma por
    su cuenta (ADR-001), así que en lugar de forzarlo se comprueba el
    resultado. Basta con que una letra sea del alfabeto esperado: un globo
    japonés con una palabra en inglés sigue siendo japonés. Un texto sin
    letras, como "!?" o "…", no se considera un desajuste.
    """
    letters = [character for character in text if character.isalpha()]
    if not letters:
        return True
    parts = script_name_parts(language_code)
    return any(
        part in unicodedata.name(letter, "") for letter in letters for part in parts
    )


def text_needs_review(text, confidence, language_code, threshold):
    """Indica si un texto reconocido debe revisarse a mano.

    threshold es la confianza mínima, de 0 a 1 (OCR_REVIEW_THRESHOLD). Se
    usa al procesar la página y al restaurar el texto del OCR (HU-15).
    """
    if not text.strip():
        return True
    if confidence is None or confidence < threshold:
        return True
    return not matches_source_script(text, language_code)


def needs_review(region, language_code, threshold):
    """Indica si una región detectada debe revisarse a mano."""
    return text_needs_review(region.text, region.confidence, language_code, threshold)
