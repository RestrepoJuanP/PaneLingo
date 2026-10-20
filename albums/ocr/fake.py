"""Proveedor simulado: no usa la red ni gasta cuota (ADR-001)."""

import io

from PIL import Image

from albums.ocr.base import DetectedRegion, OcrProvider, OcrProviderError


class FakeOcrProvider(OcrProvider):
    """Devuelve resultados deterministas para pruebas y desarrollo sin clave.

    Sin argumentos simula dos globos en la mitad superior de la página, en
    posiciones relativas a su tamaño. Con regions se le indica exactamente qué
    devolver, incluida una lista vacía para una página sin texto. Con error
    simula un fallo del servicio.
    """

    def __init__(self, regions=None, error=None):
        """Guarda las regiones o el error que devolverá detect."""
        self.regions = regions
        self.error = error

    def detect(self, image_bytes):
        """Devuelve las regiones configuradas o lanza el error configurado."""
        if self.error:
            raise OcrProviderError(self.error)
        if self.regions is not None:
            return list(self.regions)
        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size
        return [
            DetectedRegion(
                x=width * 6 // 10,
                y=height // 20,
                width=width // 4,
                height=height // 8,
                text="こんにちは",
                confidence=0.97,
            ),
            DetectedRegion(
                x=width // 10,
                y=height // 4,
                width=width // 4,
                height=height // 8,
                text="ありがとう",
                confidence=0.91,
            ),
        ]
