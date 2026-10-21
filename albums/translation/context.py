"""Contexto de página que se envía a la IA (HU-16, CA-16.2 y CA-16.3)."""

from albums.translation.base import PageTranslationRequest, RegionText


def wants_translation(region, only_region_id):
    """Indica si la región espera traducción en esta petición.

    Las aprobadas nunca se sobrescriben (CA-16.3). Con only_region_id, el
    "Reintentar con IA" de una región, solo esa espera traducción.
    """
    if region.is_translation_approved:
        return False
    return only_region_id is None or region.pk == only_region_id


def build_page_request(page, regions, only_region_id=None):
    """Construye la petición con todas las regiones de la página.

    Viajan todas las regiones con texto, en orden de lectura y con su tipo,
    aunque solo se pida traducir algunas: así la IA traduce con el contexto
    de la página entera y no frases sueltas (CA-16.2). Las regiones sin texto
    que traducir (CA-15.5) no aportan contexto y no se envían.
    """
    album = page.album
    return PageTranslationRequest(
        source_language=album.source_language.name,
        target_language=album.target_language.name,
        target_code=album.target_language.code,
        regions=tuple(
            RegionText(
                number=region.reading_order,
                kind=region.get_kind_display(),
                text=region.final_text.strip(),
                translate=wants_translation(region, only_region_id),
            )
            for region in sorted(regions, key=lambda item: item.reading_order)
            if region.needs_translation
        ),
    )
