"""Contrato común de los proveedores de detección de texto (ADR-001)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectedRegion:
    """Caja con texto que devuelve un proveedor.

    Es el contrato de datos compartido por HU-12, HU-13 y HU-14. La posición
    va en píxeles de la imagen original. El texto y la confianza los guarda
    HU-13; HU-12 solo usa la posición.
    """

    x: int
    y: int
    width: int
    height: int
    text: str = ""
    confidence: float | None = None

    @property
    def right(self):
        """Coordenada del borde derecho."""
        return self.x + self.width

    @property
    def bottom(self):
        """Coordenada del borde inferior."""
        return self.y + self.height


class OcrProviderError(Exception):
    """Fallo del proveedor. El mensaje se muestra tal cual al usuario."""


class OcrProvider:
    """Interfaz que cumple todo proveedor de detección de texto."""

    def detect(self, image_bytes):
        """Devuelve las cajas con texto de una imagen.

        Lanza OcrProviderError si el servicio no responde o devuelve un error.
        """
        raise NotImplementedError
