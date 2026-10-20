"""Pruebas de los proveedores de detección de texto (HU-12, ADR-001).

Ninguna prueba llama a Azure: la red se sustituye por un doble de urlopen.
"""

import io
import json
from unittest import mock
from urllib.error import HTTPError, URLError

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from albums.ocr import get_provider
from albums.ocr.azure_read import (
    CREDENTIALS_MESSAGE,
    INVALID_RESPONSE_MESSAGE,
    NOT_CONFIGURED_MESSAGE,
    QUOTA_MESSAGE,
    TIMEOUT_MESSAGE,
    UNAVAILABLE_MESSAGE,
    AzureReadProvider,
)
from albums.ocr.base import OcrProviderError
from albums.ocr.fake import FakeOcrProvider
from albums.tests.test_pages import make_image_bytes

ENDPOINT = "https://panelingo-pruebas.cognitiveservices.azure.com/"

# Respuesta con la forma documentada de Image Analysis 4.0: un bloque con dos
# líneas, cada una con su polígono y sus palabras.
AZURE_RESPONSE = {
    "readResult": {
        "blocks": [
            {
                "lines": [
                    {
                        "text": "こんにちは",
                        "boundingPolygon": [
                            {"x": 120, "y": 40},
                            {"x": 150, "y": 40},
                            {"x": 150, "y": 220},
                            {"x": 120, "y": 220},
                        ],
                        "words": [
                            {"text": "こんにちは", "confidence": 0.9},
                        ],
                    },
                    {
                        "text": "Hello world",
                        "boundingPolygon": [
                            {"x": 10, "y": 500},
                            {"x": 210, "y": 498},
                            {"x": 212, "y": 530},
                            {"x": 12, "y": 532},
                        ],
                        "words": [
                            {"text": "Hello", "confidence": 0.8},
                            {"text": "world", "confidence": 0.6},
                        ],
                    },
                ]
            }
        ]
    }
}


def fake_response(payload):
    """Devuelve un objeto que se comporta como la respuesta de urlopen."""
    body = io.BytesIO(json.dumps(payload).encode("utf-8"))
    response = mock.MagicMock()
    response.__enter__.return_value = body
    return response


def http_error(status_code):
    """Construye el error HTTP que lanzaría urlopen."""
    return HTTPError(ENDPOINT, status_code, "error", hdrs=None, fp=None)


class AzureReadSuccessTests(SimpleTestCase):
    """CP-12.1 — El adaptador de Azure convierte su respuesta al contrato común."""

    def setUp(self):
        """Proveedor con credenciales de prueba."""
        self.provider = AzureReadProvider(ENDPOINT, "clave-de-prueba", timeout=5)

    @mock.patch("albums.ocr.azure_read.urlopen")
    def test_each_line_becomes_a_detected_region(self, urlopen):
        """CP-12.1 — Cada línea llega con su caja, su texto y su confianza."""
        urlopen.return_value = fake_response(AZURE_RESPONSE)

        regions = self.provider.detect(b"imagen")

        self.assertEqual(len(regions), 2)
        vertical, horizontal = regions
        self.assertEqual(
            (vertical.x, vertical.y, vertical.width, vertical.height),
            (120, 40, 30, 180),
        )
        self.assertEqual(vertical.text, "こんにちは")
        self.assertAlmostEqual(vertical.confidence, 0.9)
        self.assertEqual((horizontal.x, horizontal.y), (10, 498))
        self.assertAlmostEqual(horizontal.confidence, 0.7)

    @mock.patch("albums.ocr.azure_read.urlopen")
    def test_the_request_follows_the_documented_contract(self, urlopen):
        """CP-12.1 — Se llama a la API 4.0 con la clave en cabecera y sin idioma."""
        urlopen.return_value = fake_response(AZURE_RESPONSE)

        self.provider.detect(b"imagen")

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://panelingo-pruebas.cognitiveservices.azure.com"
            "/computervision/imageanalysis:analyze"
            "?api-version=2024-02-01&features=read",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            request.get_header("Ocp-apim-subscription-key"), "clave-de-prueba"
        )
        self.assertEqual(request.get_header("Content-type"), "application/octet-stream")
        self.assertEqual(request.data, b"imagen")
        self.assertNotIn("language", request.full_url)

    @mock.patch("albums.ocr.azure_read.urlopen")
    def test_a_page_without_text_returns_no_regions(self, urlopen):
        """CP-12.3 — Una página sin texto devuelve una lista vacía."""
        urlopen.return_value = fake_response({"readResult": {"blocks": []}})

        self.assertEqual(self.provider.detect(b"imagen"), [])


class AzureReadFailureTests(SimpleTestCase):
    """CP-12.4 — Los fallos de Azure llegan como mensajes comprensibles."""

    def setUp(self):
        """Proveedor con credenciales de prueba."""
        self.provider = AzureReadProvider(ENDPOINT, "clave-de-prueba", timeout=5)

    def assert_fails_with(self, urlopen, side_effect, message):
        """Comprueba que un fallo de urlopen se traduce al mensaje indicado."""
        urlopen.side_effect = side_effect
        with self.assertRaisesMessage(OcrProviderError, message):
            self.provider.detect(b"imagen")

    @mock.patch("albums.ocr.azure_read.urlopen")
    def test_http_errors_are_translated(self, urlopen):
        """CP-12.4 — Credenciales, cuota y caídas tienen su propio mensaje."""
        cases = [
            (401, CREDENTIALS_MESSAGE),
            (403, CREDENTIALS_MESSAGE),
            (429, QUOTA_MESSAGE),
            (500, UNAVAILABLE_MESSAGE),
            (503, UNAVAILABLE_MESSAGE),
        ]
        for status_code, message in cases:
            with self.subTest(status_code=status_code):
                self.assert_fails_with(urlopen, http_error(status_code), message)

    @mock.patch("albums.ocr.azure_read.urlopen")
    def test_network_problems_are_translated(self, urlopen):
        """CP-12.4 — Sin conexión o sin respuesta a tiempo."""
        self.assert_fails_with(urlopen, URLError("sin red"), UNAVAILABLE_MESSAGE)
        self.assert_fails_with(urlopen, TimeoutError(), TIMEOUT_MESSAGE)

    @mock.patch("albums.ocr.azure_read.urlopen")
    def test_unreadable_responses_are_translated(self, urlopen):
        """CP-12.4 — Una respuesta que no es JSON o no tiene la forma esperada."""
        broken = mock.MagicMock()
        broken.__enter__.return_value = io.BytesIO(b"<html>")
        urlopen.return_value = broken
        with self.assertRaisesMessage(OcrProviderError, INVALID_RESPONSE_MESSAGE):
            self.provider.detect(b"imagen")

        urlopen.return_value = fake_response(
            {"readResult": {"blocks": [{"lines": [{}]}]}}
        )
        with self.assertRaisesMessage(OcrProviderError, INVALID_RESPONSE_MESSAGE):
            self.provider.detect(b"imagen")

    @mock.patch("albums.ocr.azure_read.urlopen")
    def test_missing_or_insecure_configuration_never_calls_the_network(self, urlopen):
        """CP-12.4 — Sin clave o sin HTTPS no se hace ninguna llamada."""
        for endpoint, key in [
            (ENDPOINT, ""),
            ("", "clave"),
            ("http://panelingo.cognitiveservices.azure.com/", "clave"),
            ("file:///etc/passwd", "clave"),
        ]:
            with self.subTest(endpoint=endpoint, key=key):
                provider = AzureReadProvider(endpoint, key, timeout=5)
                with self.assertRaisesMessage(OcrProviderError, NOT_CONFIGURED_MESSAGE):
                    provider.detect(b"imagen")
        urlopen.assert_not_called()


class ProviderSelectionTests(SimpleTestCase):
    """CP-12.1 — El proveedor se elige por configuración."""

    @override_settings(OCR_PROVIDER="fake")
    def test_fake_is_selected(self):
        """CP-12.1 — "fake" devuelve el proveedor simulado."""
        self.assertIsInstance(get_provider(), FakeOcrProvider)

    @override_settings(
        OCR_PROVIDER="azure",
        AZURE_VISION_ENDPOINT=ENDPOINT,
        AZURE_VISION_KEY="clave",
    )
    def test_azure_is_selected(self):
        """CP-12.1 — "azure" devuelve el adaptador de Azure con su configuración."""
        provider = get_provider()

        self.assertIsInstance(provider, AzureReadProvider)
        self.assertEqual(provider.key, "clave")

    @override_settings(OCR_PROVIDER="tesseract")
    def test_unknown_provider_is_a_configuration_error(self):
        """CP-12.1 — Flujo alternativo: un proveedor desconocido se rechaza."""
        with self.assertRaises(ImproperlyConfigured):
            get_provider()


class FakeProviderTests(SimpleTestCase):
    """CP-12.1 — El proveedor simulado cubre los tres desenlaces."""

    def test_default_result_has_two_regions_inside_the_page(self):
        """CP-12.1 — Sin configurar, simula dos globos dentro de la página."""
        regions = FakeOcrProvider().detect(make_image_bytes(400, 560))

        self.assertEqual(len(regions), 2)
        for region in regions:
            self.assertLessEqual(region.right, 400)
            self.assertLessEqual(region.bottom, 560)

    def test_it_can_return_no_regions(self):
        """CP-12.3 — Puede simular una página sin texto."""
        self.assertEqual(FakeOcrProvider(regions=[]).detect(b""), [])

    def test_it_can_fail(self):
        """CP-12.4 — Puede simular un fallo del servicio."""
        with self.assertRaisesMessage(OcrProviderError, "Caído"):
            FakeOcrProvider(error="Caído").detect(b"")
