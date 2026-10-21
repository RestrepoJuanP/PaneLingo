"""Contrato común de los proveedores de traducción (HU-16, ADR-002)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegionText:
    """Región que viaja al proveedor como parte del contexto de la página.

    Se envían todas las regiones con texto, en orden de lectura, para que la
    IA traduzca con el contexto de la página entera (CA-16.2). Solo las que
    llevan translate=True esperan traducción; el resto, por ejemplo las ya
    aprobadas (CA-16.3), van únicamente como contexto.
    """

    number: int
    kind: str
    text: str
    translate: bool = True


@dataclass(frozen=True)
class PageTranslationRequest:
    """Lo que se envía al proveedor para traducir una página."""

    source_language: str
    target_language: str
    target_code: str
    regions: tuple

    @property
    def numbers_to_translate(self):
        """Números de las regiones que esperan traducción."""
        return [region.number for region in self.regions if region.translate]


@dataclass(frozen=True)
class RegionTranslation:
    """Traducción que devuelve el proveedor para una región."""

    number: int
    translation: str


class TranslationError(Exception):
    """Fallo del proveedor. El mensaje se muestra tal cual al usuario."""


class TranslationProvider:
    """Interfaz que cumple todo proveedor de traducción."""

    def translate(self, request):
        """Devuelve una RegionTranslation por cada región que hay que traducir.

        Lanza TranslationError si el servicio no responde o devuelve algo que
        no se puede usar.
        """
        raise NotImplementedError
