"""Adaptador de Azure AI Vision Read, Image Analysis 4.0 (ADR-001).

Usa la API REST con la biblioteca estándar en lugar del SDK de Azure: es una
sola llamada HTTP y así no se añade ninguna dependencia que auditar.
"""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from albums.ocr.base import DetectedRegion, OcrProvider, OcrProviderError

logger = logging.getLogger(__name__)

ANALYZE_PATH = "/computervision/imageanalysis:analyze"
API_VERSION = "2024-02-01"

NOT_CONFIGURED_MESSAGE = "El servicio de detección de texto no está configurado."
CREDENTIALS_MESSAGE = "El servicio de detección de texto rechazó las credenciales."
QUOTA_MESSAGE = (
    "Se alcanzó el límite de uso del servicio de detección de texto. "
    "Inténtalo de nuevo más tarde."
)
TIMEOUT_MESSAGE = "El servicio de detección de texto no respondió a tiempo."
UNAVAILABLE_MESSAGE = "El servicio de detección de texto no está disponible."
INVALID_RESPONSE_MESSAGE = (
    "El servicio de detección de texto devolvió una respuesta que no se pudo leer."
)


def message_for_status(status_code):
    """Traduce un código HTTP de error a un mensaje para el usuario."""
    if status_code in (401, 403):
        return CREDENTIALS_MESSAGE
    if status_code == 429:
        return QUOTA_MESSAGE
    return UNAVAILABLE_MESSAGE


def polygon_to_box(polygon):
    """Convierte un polígono de puntos en la caja que lo contiene."""
    xs = [point["x"] for point in polygon]
    ys = [point["y"] for point in polygon]
    left, top = max(min(xs), 0), max(min(ys), 0)
    return left, top, max(max(xs) - left, 1), max(max(ys) - top, 1)


def average_confidence(words):
    """Devuelve la confianza media de las palabras de una línea."""
    values = [word["confidence"] for word in words if "confidence" in word]
    if not values:
        return None
    return sum(values) / len(values)


def parse_read_result(payload):
    """Convierte la respuesta de Azure en una región por cada línea de texto.

    Azure no agrupa las líneas en globos: eso lo hace PaneLingo después, en
    albums.ocr.layout, para que la regla no dependa del proveedor.
    """
    regions = []
    blocks = (payload.get("readResult") or {}).get("blocks") or []
    for block in blocks:
        for line in block.get("lines") or []:
            x, y, width, height = polygon_to_box(line["boundingPolygon"])
            regions.append(
                DetectedRegion(
                    x=round(x),
                    y=round(y),
                    width=round(width),
                    height=round(height),
                    text=line.get("text", ""),
                    confidence=average_confidence(line.get("words") or []),
                )
            )
    return regions


class AzureReadProvider(OcrProvider):
    """Detecta texto con la característica read de Image Analysis 4.0.

    No se envía el idioma: el modelo es multilingüe y Microsoft desaconseja
    forzarlo, porque puede devolver texto incompleto.
    """

    def __init__(self, endpoint, key, timeout):
        """Guarda el punto de conexión, la clave y el tiempo de espera."""
        self.endpoint = (endpoint or "").strip().rstrip("/")
        self.key = (key or "").strip()
        self.timeout = timeout

    def build_request(self, image_bytes):
        """Construye la petición HTTP a Azure."""
        url = f"{self.endpoint}{ANALYZE_PATH}?api-version={API_VERSION}&features=read"
        return Request(
            url,
            data=image_bytes,
            method="POST",
            headers={
                "Ocp-Apim-Subscription-Key": self.key,
                "Content-Type": "application/octet-stream",
            },
        )

    def detect(self, image_bytes):
        """Envía la imagen a Azure y devuelve sus líneas de texto."""
        # Solo HTTPS: la clave viaja en una cabecera, y un punto de conexión
        # mal escrito no puede convertir la llamada en una lectura de archivo
        # local ni en una petición en claro.
        if not self.key or not self.endpoint.startswith("https://"):
            raise OcrProviderError(NOT_CONFIGURED_MESSAGE)
        request = self.build_request(image_bytes)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as error:
            logger.warning("Azure Read respondió %s.", error.code)
            raise OcrProviderError(message_for_status(error.code)) from error
        except TimeoutError as error:
            raise OcrProviderError(TIMEOUT_MESSAGE) from error
        except (URLError, OSError) as error:
            logger.warning("No se pudo contactar con Azure Read: %s", error)
            raise OcrProviderError(UNAVAILABLE_MESSAGE) from error
        except ValueError as error:
            raise OcrProviderError(INVALID_RESPONSE_MESSAGE) from error
        try:
            return parse_read_result(payload)
        except (KeyError, TypeError, AttributeError) as error:
            raise OcrProviderError(INVALID_RESPONSE_MESSAGE) from error
