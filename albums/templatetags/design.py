"""Filtros de presentación del sistema de diseño de PaneLingo.

Generan la portada abstracta de un álbum de forma determinista a partir de su
identificador, sin imágenes externas ni obra con derechos.
"""

import hashlib

from django import template

register = template.Library()

# Composiciones de viñetas definidas en static/css/app.css.
COVER_LAYOUTS = ["a", "b", "c", "d"]

# Número de viñetas que dibuja cada composición.
PANELS_PER_LAYOUT = {"a": 4, "b": 3, "c": 3, "d": 5}

# Degradados disponibles, declarados como --cover-1 … --cover-8.
COVER_VARIANTS = 8


def _seed_value(seed):
    """Convierte cualquier identificador en un entero estable no negativo.

    Se usa un resumen SHA-256 en lugar de hash(), porque hash() aplica una
    sal distinta en cada proceso de Python y la portada de un álbum cambiaría
    cada vez que se reiniciara el servidor. Aquí el resumen solo reparte
    valores en cubetas, no cumple ninguna función criptográfica.
    """
    if isinstance(seed, int):
        return abs(seed)
    if not seed:
        return 0
    digest = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _layout_for(value):
    """Elige la composición a partir del tramo bajo del valor."""
    return COVER_LAYOUTS[value % len(COVER_LAYOUTS)]


@register.filter
def cover_layout(seed):
    """Devuelve la composición de viñetas que corresponde al identificador."""
    return _layout_for(_seed_value(seed))


@register.filter
def cover_panels(seed):
    """Devuelve la lista de degradados de cada viñeta de la portada.

    El resultado es siempre el mismo para un identificador dado, de modo que
    la portada de un álbum no cambia entre visitas ni entre reinicios.

    La composición, el degradado inicial y el salto entre degradados se toman
    de tramos distintos del valor. Si salieran todos del mismo resto, dos
    identificadores con la misma cubeta producirían portadas idénticas.
    """
    value = _seed_value(seed)
    count = PANELS_PER_LAYOUT[_layout_for(value)]
    start = (value >> 2) % COVER_VARIANTS
    # El salto debe ser coprimo con el número de degradados para recorrerlos
    # sin repetir dentro de una misma portada.
    step = ((value >> 6) % (COVER_VARIANTS // 2)) * 2 + 1
    return [(start + index * step) % COVER_VARIANTS + 1 for index in range(count)]
