"""Reglas de maquetación de las regiones detectadas (ADR-001, supuestos S3 y S4).

Viven aquí, y no en cada proveedor, para que cambiar de proveedor no cambie
cómo se forman las regiones, en qué orden se leen ni qué tipo se les asigna.
"""

from dataclasses import replace

from albums.ocr.base import DetectedRegion

# Idiomas de origen cuyas viñetas se leen de derecha a izquierda. El coreano
# (webtoon) y el chino simplificado se leen de izquierda a derecha.
RIGHT_TO_LEFT_LANGUAGES = frozenset({"ja"})

# Luminosidad mediana, de 0 a 255, a partir de la cual el fondo de una región
# se considera blanco y la región se clasifica como globo de diálogo. Es un
# valor provisional: hay que calibrarlo con el juego de páginas de prueba.
BALLOON_MIN_LUMINANCE = 200


def is_right_to_left(language_code):
    """Indica si un idioma de origen se lee de derecha a izquierda."""
    return language_code in RIGHT_TO_LEFT_LANGUAGES


def clamp_to_page(region, page_width, page_height):
    """Recorta una caja a los límites de la página, o devuelve None si queda vacía.

    Los proveedores pueden devolver coordenadas ligeramente fuera de la
    imagen; sin este recorte, el resaltado se saldría de la página.
    """
    left = min(max(region.x, 0), page_width)
    top = min(max(region.y, 0), page_height)
    right = min(max(region.right, 0), page_width)
    bottom = min(max(region.bottom, 0), page_height)
    if right <= left or bottom <= top:
        return None
    return replace(region, x=left, y=top, width=right - left, height=bottom - top)


def line_thickness(region):
    """Devuelve el grosor de una línea: su lado menor, sea horizontal o vertical."""
    return min(region.width, region.height)


def are_neighbours(first, second):
    """Indica si dos líneas están tan cerca que pertenecen al mismo globo.

    Se consideran vecinas si la separación entre sus cajas, en horizontal y en
    vertical, no supera el grosor de la línea más fina.
    """
    allowed_gap = min(line_thickness(first), line_thickness(second))
    horizontal_gap = max(first.x - second.right, second.x - first.right, 0)
    vertical_gap = max(first.y - second.bottom, second.y - first.bottom, 0)
    return horizontal_gap <= allowed_gap and vertical_gap <= allowed_gap


def group_neighbours(lines):
    """Agrupa las líneas vecinas, también de forma transitiva."""
    groups = []
    for line in lines:
        touching = [
            group
            for group in groups
            if any(are_neighbours(line, member) for member in group)
        ]
        merged = [line]
        for group in touching:
            merged.extend(group)
            groups.remove(group)
        groups.append(merged)
    return groups


def order_lines_inside(lines):
    """Ordena las líneas de un mismo globo.

    El texto vertical se escribe en columnas de derecha a izquierda en
    japonés, chino y coreano; el horizontal, en filas de arriba abajo.
    """
    vertical_lines = sum(1 for line in lines if line.height > line.width)
    if vertical_lines > len(lines) / 2:
        return sorted(lines, key=lambda line: -line.right)
    return sorted(lines, key=lambda line: line.y)


def merge_group(lines):
    """Funde un grupo de líneas en una sola región que las contiene a todas."""
    ordered = order_lines_inside(lines)
    left = min(line.x for line in lines)
    top = min(line.y for line in lines)
    right = max(line.right for line in lines)
    bottom = max(line.bottom for line in lines)
    confidences = [line.confidence for line in lines if line.confidence is not None]
    return DetectedRegion(
        x=left,
        y=top,
        width=right - left,
        height=bottom - top,
        text="\n".join(line.text for line in ordered if line.text),
        confidence=sum(confidences) / len(confidences) if confidences else None,
    )


def merge_lines_into_regions(lines):
    """Convierte las líneas de un proveedor en regiones, una por globo."""
    return [merge_group(group) for group in group_neighbours(lines)]


def shares_row(row, region):
    """Indica si una región solapa en vertical con una fila al menos a la mitad."""
    row_top = min(member.y for member in row)
    row_bottom = max(member.bottom for member in row)
    overlap = min(row_bottom, region.bottom) - max(row_top, region.y)
    return overlap >= min(region.height, row_bottom - row_top) / 2


def sort_in_reading_order(regions, right_to_left):
    """Ordena las regiones como las leería una persona (CA-12.2).

    Las regiones se agrupan en filas por solapamiento vertical, las filas se
    leen de arriba abajo y, dentro de cada fila, de derecha a izquierda o de
    izquierda a derecha según el idioma de origen.
    """
    rows = []
    for region in sorted(regions, key=lambda region: region.y):
        row = next((row for row in rows if shares_row(row, region)), None)
        if row is None:
            rows.append([region])
        else:
            row.append(region)

    direction = -1 if right_to_left else 1
    ordered = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda region: direction * region.x))
    return ordered


def arrange_regions(detected, page_width, page_height, language_code):
    """Convierte lo que devolvió un proveedor en regiones en orden de lectura.

    Recorta las cajas a la página, agrupa las líneas en globos y los ordena
    según el idioma de origen. Lo usan el procesamiento de páginas y la
    medición de precisión, para que las dos midan exactamente lo mismo.
    """
    clamped = [clamp_to_page(line, page_width, page_height) for line in detected]
    merged = merge_lines_into_regions([line for line in clamped if line])
    return sort_in_reading_order(merged, is_right_to_left(language_code))


def median_luminance(image, region):
    """Devuelve la luminosidad mediana, de 0 a 255, del interior de una región.

    La mediana, y no la media, para que los trazos del texto, que ocupan
    menos de la mitad del globo, no oscurezcan el resultado.
    """
    crop = image.crop((region.x, region.y, region.right, region.bottom))
    histogram = crop.convert("L").histogram()
    half = sum(histogram) / 2
    accumulated = 0
    for level, count in enumerate(histogram):
        accumulated += count
        if accumulated >= half:
            return level
    return 255


def is_balloon(image, region):
    """Indica si una región parece un globo de diálogo (supuesto S3).

    Heurística provisional: el fondo de los globos es blanco y el de los
    cuadros narrativos suele ser de color o gris. El usuario podrá corregir
    el tipo en HU-15.
    """
    return median_luminance(image, region) >= BALLOON_MIN_LUMINANCE
