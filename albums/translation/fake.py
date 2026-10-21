"""Proveedor de traducción simulado: no usa la red ni gasta cuota (ADR-002)."""

from albums.translation.base import (
    RegionTranslation,
    TranslationError,
    TranslationProvider,
)


class FakeTranslationProvider(TranslationProvider):
    """Traducción determinista para pruebas y desarrollo sin clave.

    Antepone el código del idioma de destino al texto ("[ES] こんにちは"), así
    que las pruebas pueden comprobar qué texto se tradujo. Con error simula
    un fallo del servicio y con skip omite las regiones indicadas, como haría
    una respuesta incompleta. Guarda la última petición en last_request para
    comprobar el contexto que se envió (CA-16.2).
    """

    def __init__(self, error=None, skip=()):
        """Guarda el error que lanzará y las regiones que omitirá."""
        self.error = error
        self.skip = set(skip)
        self.last_request = None

    def translate(self, request):
        """Devuelve una traducción simulada por cada región pedida."""
        self.last_request = request
        if self.error:
            raise TranslationError(self.error)
        prefix = f"[{request.target_code.upper()}]"
        return [
            RegionTranslation(
                number=region.number, translation=f"{prefix} {region.text}"
            )
            for region in request.regions
            if region.translate and region.number not in self.skip
        ]
