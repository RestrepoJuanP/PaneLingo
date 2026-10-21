"""Adaptador de Google Gemini para traducir páginas (ADR-002).

Igual que el de Azure Read, usa la API REST con la biblioteca estándar en
lugar del SDK: es una sola llamada HTTP y así no se añade ninguna dependencia.
"""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from albums.translation.base import (
    RegionTranslation,
    TranslationError,
    TranslationProvider,
)

logger = logging.getLogger(__name__)

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"

NOT_CONFIGURED_MESSAGE = "El servicio de traducción no está configurado."
CREDENTIALS_MESSAGE = "El servicio de traducción rechazó las credenciales."
QUOTA_MESSAGE = (
    "Se alcanzó el límite de uso del servicio de traducción. "
    "Inténtalo de nuevo más tarde."
)
BUSY_MESSAGE = (
    "El servicio de traducción está saturado en este momento. "
    "Inténtalo de nuevo en unos segundos."
)
TIMEOUT_MESSAGE = "El servicio de traducción no respondió a tiempo."
UNAVAILABLE_MESSAGE = "El servicio de traducción no está disponible."
INVALID_RESPONSE_MESSAGE = (
    "El servicio de traducción devolvió una respuesta que no se pudo leer."
)

# Instrucción fija. No hay selector de estilo (CA-16.6): la IA decide el
# registro a partir del contexto de la página.
SYSTEM_INSTRUCTION = (
    "Eres un traductor profesional de cómic, manga y webtoon. Recibes todas "
    "las regiones de texto de una página en orden de lectura, con su tipo "
    "(globo de diálogo o cuadro narrativo). Usa la página entera como "
    "contexto: quién habla, el tono y lo que pasa. Traduce solo las regiones "
    "con translate=true, del idioma de origen al de destino, con naturalidad "
    "y con la puntuación propia del idioma de destino. Los saltos de línea del "
    "texto de origen vienen de las columnas del globo, no del sentido: no los "
    "copies y escribe cada traducción como texto corrido. No añadas notas ni "
    "explicaciones. "
    "Devuelve exactamente una traducción por cada región pedida, con su mismo "
    "número."
)

# Esquema de la respuesta: obliga a la IA a devolver JSON validable.
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "translations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "number": {"type": "INTEGER"},
                    "translation": {"type": "STRING"},
                },
                "required": ["number", "translation"],
            },
        }
    },
    "required": ["translations"],
}


def message_for_status(status_code):
    """Traduce un código HTTP de error a un mensaje para el usuario."""
    if status_code in (401, 403):
        return CREDENTIALS_MESSAGE
    if status_code == 429:
        return QUOTA_MESSAGE
    if status_code == 503:
        return BUSY_MESSAGE
    return UNAVAILABLE_MESSAGE


def build_prompt(request):
    """Convierte la petición en el contenido que lee la IA (CA-16.2)."""
    return json.dumps(
        {
            "source_language": request.source_language,
            "target_language": request.target_language,
            "regions": [
                {
                    "number": region.number,
                    "kind": region.kind,
                    "text": region.text,
                    "translate": region.translate,
                }
                for region in request.regions
            ],
        },
        ensure_ascii=False,
    )


def build_body(request):
    """Cuerpo de la llamada a generateContent."""
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": build_prompt(request)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0.3,
        },
    }


def parse_response(payload, request):
    """Extrae las traducciones de la respuesta y descarta lo que no se pidió."""
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    items = json.loads(text)["translations"]
    wanted = set(request.numbers_to_translate)
    translations = {}
    for item in items:
        number = int(item["number"])
        if number in wanted and number not in translations:
            translations[number] = str(item["translation"]).strip()
    if wanted and not translations:
        raise ValueError("La respuesta no traduce ninguna región pedida.")
    return [
        RegionTranslation(number=number, translation=translation)
        for number, translation in sorted(translations.items())
    ]


class GeminiProvider(TranslationProvider):
    """Traduce una página con la API generateContent de Gemini."""

    def __init__(self, key, model, timeout):
        """Guarda la clave, el modelo y el tiempo de espera."""
        self.key = (key or "").strip()
        self.model = (model or "").strip()
        self.timeout = timeout

    def build_request(self, request):
        """Construye la petición HTTP. La clave va en una cabecera, nunca en
        la URL, para que no quede en los registros."""
        url = f"{API_ROOT}/{quote(self.model, safe='-.')}:generateContent"
        return Request(
            url,
            data=json.dumps(build_body(request)).encode("utf-8"),
            method="POST",
            headers={"x-goog-api-key": self.key, "Content-Type": "application/json"},
        )

    def translate(self, request):
        """Envía la página a Gemini y devuelve sus traducciones."""
        if not self.key or not self.model:
            raise TranslationError(NOT_CONFIGURED_MESSAGE)
        try:
            with urlopen(self.build_request(request), timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as error:
            logger.warning("Gemini respondió %s.", error.code)
            raise TranslationError(message_for_status(error.code)) from error
        except TimeoutError as error:
            raise TranslationError(TIMEOUT_MESSAGE) from error
        except (URLError, OSError) as error:
            logger.warning("No se pudo contactar con Gemini: %s", error)
            raise TranslationError(UNAVAILABLE_MESSAGE) from error
        except ValueError as error:
            raise TranslationError(INVALID_RESPONSE_MESSAGE) from error
        try:
            return parse_response(payload, request)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise TranslationError(INVALID_RESPONSE_MESSAGE) from error
