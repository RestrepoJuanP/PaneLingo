"""Ajuste de traducciones dentro de las cajas detectadas (HU-87)."""

from pathlib import Path

from django.conf import settings
from PIL import ImageFont

from albums.models import TextRegion

MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 72
LINE_SPACING_RATIO = 0.12
PREVIEW_PADDING_RATIO = 0.006
FONT_DIRECTORY = Path(settings.BASE_DIR) / "static" / "fonts"
REGULAR_FONT_PATH = FONT_DIRECTORY / "ComicNeue-Regular.ttf"
ITALIC_FONT_PATH = FONT_DIRECTORY / "ComicNeue-Italic.ttf"


def line_width(font, text):
    """Mide una línea con la caja real de la fuente."""
    if not text:
        return 0
    left, _top, right, _bottom = font.getbbox(text)
    return right - left


def line_height(font):
    """Calcula un interlineado estable que incluye tildes y descendentes."""
    _left, top, _right, bottom = font.getbbox("Ág¿¡")
    glyph_height = bottom - top
    return glyph_height + max(1, round(font.size * LINE_SPACING_RATIO))


def wrap_paragraph(paragraph, font, box_width):
    """Parte un párrafo de forma voraz sin cortar ninguna palabra."""
    words = paragraph.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if line_width(font, candidate) <= box_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def wrap_text(text, font, box_width):
    """Ajusta palabras y conserva los saltos escritos por el traductor."""
    paragraphs = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = []
    for paragraph in paragraphs:
        lines.extend(wrap_paragraph(paragraph, font, box_width))
    return lines or [""]


def lines_fit(lines, font, box_width, box_height):
    """Indica si todas las líneas caben en el ancho y alto disponibles."""
    fits_width = all(line_width(font, line) <= box_width for line in lines)
    fits_height = len(lines) * line_height(font) <= box_height
    return fits_width and fits_height


def fit_text(text, box_width, box_height, font_path, max_size, min_size=8):
    """Devuelve el mayor tamaño y sus líneas sin cortar palabras.

    Si ni el tamaño mínimo cabe, lo devuelve igualmente para que la interfaz
    pueda mostrar el aviso «El texto no cabe» sin ocultar el contenido.
    """
    minimum = max(1, int(min_size))
    maximum = max(minimum, int(max_size))
    latest_lines = [text]
    for font_size in range(maximum, minimum - 1, -1):
        font = ImageFont.truetype(str(font_path), font_size)
        latest_lines = wrap_text(text, font, box_width)
        if lines_fit(latest_lines, font, box_width, box_height):
            return font_size, latest_lines
    return minimum, latest_lines


def font_path_for(region):
    """Usa Comic Neue cursiva para narración y regular para diálogo."""
    if region.kind == TextRegion.Kind.NARRATION:
        return ITALIC_FONT_PATH
    return REGULAR_FONT_PATH


def preview_text(region):
    """Elige traducción o texto fuente según el estado de la región."""
    return region.translation if region.translation else region.final_text


def preview_for_region(region):
    """Construye los datos de una región para la vista previa decorativa."""
    if region.skip_translation:
        return {
            "region_pk": region.pk,
            "status": "skipped",
            "lines": [],
            "font_size": MIN_FONT_SIZE,
            "font_ratio": 0,
            "font_ratio_css": "0",
            "fits": True,
            "kind": region.kind,
            "overlay_style": region.overlay_style,
        }

    text = preview_text(region)
    padding = (region.page.width or 1) * PREVIEW_PADDING_RATIO
    box_width = max(1, region.width - 2 * padding)
    box_height = max(1, region.height - 2 * padding)
    max_size = min(MAX_FONT_SIZE, max(MIN_FONT_SIZE, round(region.height * 0.7)))
    font_path = font_path_for(region)
    font_size, lines = fit_text(
        text,
        box_width,
        box_height,
        font_path,
        max_size,
        MIN_FONT_SIZE,
    )
    font = ImageFont.truetype(str(font_path), font_size)
    font_ratio = round(font_size / (region.page.width or 1) * 100, 5)
    return {
        "region_pk": region.pk,
        "status": "translated" if region.translation else "untranslated",
        "lines": lines,
        "font_size": font_size,
        "font_ratio": font_ratio,
        "font_ratio_css": f"{font_ratio:.5f}".rstrip("0").rstrip("."),
        "fits": lines_fit(lines, font, box_width, box_height),
        "kind": region.kind,
        "overlay_style": region.overlay_style,
    }
