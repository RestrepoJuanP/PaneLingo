"""Proveedores de detección de texto de las páginas (HU-12, ADR-001)."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from albums.ocr.azure_read import AzureReadProvider
from albums.ocr.base import DetectedRegion, OcrProvider, OcrProviderError
from albums.ocr.fake import FakeOcrProvider

__all__ = [
    "DetectedRegion",
    "OcrProvider",
    "OcrProviderError",
    "get_provider",
]


def get_provider():
    """Devuelve el proveedor que indica la variable OCR_PROVIDER."""
    if settings.OCR_PROVIDER == "fake":
        return FakeOcrProvider()
    if settings.OCR_PROVIDER == "azure":
        return AzureReadProvider(
            endpoint=settings.AZURE_VISION_ENDPOINT,
            key=settings.AZURE_VISION_KEY,
            timeout=settings.OCR_TIMEOUT_SECONDS,
        )
    raise ImproperlyConfigured(
        f"OCR_PROVIDER no reconocido: «{settings.OCR_PROVIDER}». "
        "Usa «fake» o «azure»."
    )
