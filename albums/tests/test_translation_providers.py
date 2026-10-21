"""Pruebas de los proveedores de traducción (HU-16, ADR-002).

Ninguna prueba llama a Gemini: la red se sustituye por un doble de urlopen.
"""

import io
import json
from unittest import mock
from urllib.error import HTTPError, URLError

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from albums.translation import (
    PageTranslationRequest,
    RegionText,
    TranslationError,
    get_translator,
)
from albums.translation.fake import FakeTranslationProvider
from albums.translation.gemini import (
    BUSY_MESSAGE,
    CREDENTIALS_MESSAGE,
    INVALID_RESPONSE_MESSAGE,
    NOT_CONFIGURED_MESSAGE,
    QUOTA_MESSAGE,
    RESPONSE_SCHEMA,
    TIMEOUT_MESSAGE,
    UNAVAILABLE_MESSAGE,
    GeminiProvider,
)

KEY = "clave-de-prueba"
MODEL = "gemini-3.5-flash-lite"

REQUEST = PageTranslationRequest(
    source_language="Japonés",
    target_language="Español",
    target_code="es",
    regions=(
        RegionText(number=1, kind="Globo de diálogo", text="バーカ!!"),
        RegionText(number=2, kind="Cuadro narrativo", text="三代目", translate=False),
        RegionText(number=3, kind="Globo de diálogo", text="イルカ先生だ"),
    ),
)


def gemini_payload(translations):
    """Respuesta con la forma de generateContent y el JSON estructurado."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps({"translations": translations})}]
                }
            }
        ]
    }


def fake_response(payload):
    """Doble de la respuesta de urlopen, usable con "with"."""
    return io.BytesIO(json.dumps(payload).encode("utf-8"))


def http_error(code):
    """Error HTTP como el que lanza urlopen."""
    return HTTPError("https://gemini", code, "error", {}, io.BytesIO(b"{}"))


class GeminiRequestTests(SimpleTestCase):
    """CP-16.2 — La llamada envía el contexto de la página."""

    def setUp(self):
        """Proveedor de Gemini con una clave de prueba."""
        self.provider = GeminiProvider(key=KEY, model=MODEL, timeout=5)

    def test_the_key_travels_in_a_header_not_in_the_url(self):
        """La clave va en x-goog-api-key y no aparece en la dirección."""
        request = self.provider.build_request(REQUEST)

        self.assertIn(f"/models/{MODEL}:generateContent", request.full_url)
        self.assertNotIn(KEY, request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), KEY)

    def test_the_body_carries_every_region_and_the_languages(self):
        """CP-16.2 — Viajan todas las regiones en orden, con tipo e idiomas."""
        body = json.loads(self.provider.build_request(REQUEST).data)

        page = json.loads(body["contents"][0]["parts"][0]["text"])
        self.assertEqual(page["source_language"], "Japonés")
        self.assertEqual(page["target_language"], "Español")
        self.assertEqual([region["number"] for region in page["regions"]], [1, 2, 3])
        self.assertEqual(page["regions"][1]["kind"], "Cuadro narrativo")
        self.assertFalse(page["regions"][1]["translate"])

    def test_the_answer_must_follow_the_schema(self):
        """La respuesta se pide en JSON con un esquema validable."""
        body = json.loads(self.provider.build_request(REQUEST).data)

        config = body["generationConfig"]
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertEqual(config["responseSchema"], RESPONSE_SCHEMA)
        self.assertIn("systemInstruction", body)


@mock.patch("albums.translation.gemini.urlopen")
class GeminiResponseTests(SimpleTestCase):
    """CP-16.1 y CP-16.4 — Lectura de la respuesta y errores del servicio."""

    def setUp(self):
        """Proveedor de Gemini con una clave de prueba."""
        self.provider = GeminiProvider(key=KEY, model=MODEL, timeout=5)

    def test_it_returns_one_translation_per_requested_region(self, urlopen):
        """CP-16.1 — Devuelve las traducciones pedidas, en orden."""
        urlopen.return_value = fake_response(
            gemini_payload(
                [
                    {"number": 3, "translation": " Es el maestro Iruka "},
                    {"number": 1, "translation": "¡Idiota!"},
                ]
            )
        )

        result = self.provider.translate(REQUEST)

        self.assertEqual(
            [(item.number, item.translation) for item in result],
            [(1, "¡Idiota!"), (3, "Es el maestro Iruka")],
        )

    def test_regions_that_were_not_requested_are_ignored(self, urlopen):
        """CP-16.3 — Si la IA traduce una región de contexto, se descarta."""
        urlopen.return_value = fake_response(
            gemini_payload(
                [
                    {"number": 1, "translation": "¡Idiota!"},
                    {"number": 2, "translation": "El Tercero"},
                    {"number": 99, "translation": "inventada"},
                ]
            )
        )

        result = self.provider.translate(REQUEST)

        self.assertEqual([item.number for item in result], [1])

    def test_http_errors_become_readable_messages(self, urlopen):
        """CP-16.4 — Cada error HTTP tiene su mensaje para el usuario."""
        cases = {
            401: CREDENTIALS_MESSAGE,
            403: CREDENTIALS_MESSAGE,
            429: QUOTA_MESSAGE,
            503: BUSY_MESSAGE,
            500: UNAVAILABLE_MESSAGE,
        }
        for code, message in cases.items():
            with self.subTest(code=code):
                urlopen.side_effect = http_error(code)
                with self.assertRaisesMessage(TranslationError, message):
                    self.provider.translate(REQUEST)

    def test_a_timeout_is_reported(self, urlopen):
        """CP-16.4 — Si se agota el tiempo de espera, se informa."""
        urlopen.side_effect = TimeoutError()

        with self.assertRaisesMessage(TranslationError, TIMEOUT_MESSAGE):
            self.provider.translate(REQUEST)

    def test_no_network_is_reported(self, urlopen):
        """CP-16.4 — Sin conexión, el servicio no está disponible."""
        urlopen.side_effect = URLError("sin red")

        with self.assertRaisesMessage(TranslationError, UNAVAILABLE_MESSAGE):
            self.provider.translate(REQUEST)

    def test_an_unreadable_answer_is_reported(self, urlopen):
        """CP-16.4 — Una respuesta fuera del esquema es un error, no se guarda."""
        for payload in (
            {"candidates": []},
            {"candidates": [{"content": {"parts": [{"text": "no es JSON"}]}}]},
            gemini_payload([{"number": 2, "translation": "solo contexto"}]),
        ):
            with self.subTest(payload=payload):
                urlopen.side_effect = None
                urlopen.return_value = fake_response(payload)
                with self.assertRaisesMessage(
                    TranslationError, INVALID_RESPONSE_MESSAGE
                ):
                    self.provider.translate(REQUEST)

    def test_without_a_key_nothing_is_sent(self, urlopen):
        """Sin clave no se llama al servicio."""
        provider = GeminiProvider(key="", model=MODEL, timeout=5)

        with self.assertRaisesMessage(TranslationError, NOT_CONFIGURED_MESSAGE):
            provider.translate(REQUEST)
        urlopen.assert_not_called()


class ProviderChoiceTests(SimpleTestCase):
    """La variable TRANSLATION_PROVIDER elige el proveedor."""

    @override_settings(TRANSLATION_PROVIDER="fake")
    def test_fake_by_default(self):
        """Con "fake" se usa el proveedor simulado."""
        self.assertIsInstance(get_translator(), FakeTranslationProvider)

    @override_settings(
        TRANSLATION_PROVIDER="gemini", GEMINI_API_KEY=KEY, GEMINI_MODEL=MODEL
    )
    def test_gemini(self):
        """Con "gemini" se usa Gemini con la clave y el modelo configurados."""
        provider = get_translator()

        self.assertIsInstance(provider, GeminiProvider)
        self.assertEqual(provider.model, MODEL)

    @override_settings(TRANSLATION_PROVIDER="otro")
    def test_an_unknown_provider_is_a_configuration_error(self):
        """Un valor desconocido falla con un error de configuración."""
        with self.assertRaises(ImproperlyConfigured):
            get_translator()


class FakeProviderTests(SimpleTestCase):
    """El proveedor simulado solo traduce las regiones pedidas."""

    def test_it_translates_only_the_requested_regions(self):
        """Antepone el idioma de destino y omite las de contexto."""
        result = FakeTranslationProvider().translate(REQUEST)

        self.assertEqual(
            [(item.number, item.translation) for item in result],
            [(1, "[ES] バーカ!!"), (3, "[ES] イルカ先生だ")],
        )
