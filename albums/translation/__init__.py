"""Proveedores de traducción asistida por IA (HU-16, ADR-002)."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from albums.translation.base import (
    PageTranslationRequest,
    RegionText,
    RegionTranslation,
    TranslationError,
    TranslationProvider,
)
from albums.translation.fake import FakeTranslationProvider
from albums.translation.gemini import GeminiProvider

__all__ = [
    "PageTranslationRequest",
    "RegionText",
    "RegionTranslation",
    "TranslationError",
    "TranslationProvider",
    "get_translator",
]


def get_translator():
    """Devuelve el proveedor que indica la variable TRANSLATION_PROVIDER."""
    if settings.TRANSLATION_PROVIDER == "fake":
        return FakeTranslationProvider()
    if settings.TRANSLATION_PROVIDER == "gemini":
        return GeminiProvider(
            key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
            timeout=settings.TRANSLATION_TIMEOUT_SECONDS,
        )
    raise ImproperlyConfigured(
        f"TRANSLATION_PROVIDER no reconocido: «{settings.TRANSLATION_PROVIDER}». "
        "Usa «fake» o «gemini»."
    )
