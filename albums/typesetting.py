"""Maquetación de las traducciones sobre la página (HU-87 y HU-89, ADR-003).

Es el ÚNICO algoritmo de maquetación del proyecto: la vista previa, el editor
y la exportación usan layout_for_region, y el navegador pinta lo que este
módulo devuelve. No se duplica en JavaScript (ADR-003, decisión 4).

Todas las medidas están en píxeles de la imagen original (ADR-003).
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from albums.cleaning import restore_original_area
from albums.models import ComicPage, TextRegion, percent_box_style

MIN_FONT_SIZE = 8
# Tope del ajuste automático (HU-87). El tamaño fijo admite hasta
# MAX_FIXED_FONT_SIZE (ADR-003, P2).
MAX_FONT_SIZE = 72
MAX_FIXED_FONT_SIZE = 200
AUTO_SIZE_HEIGHT_RATIO = 0.7
# Lado mínimo de una caja maquetada: deja sitio al relleno y a una línea de
# MIN_FONT_SIZE, y a la vez es un objetivo de arrastre manejable en el editor.
MIN_BOX_SIZE = 16
LINE_SPACING_RATIO = 0.12
PREVIEW_PADDING_RATIO = 0.006
DEFAULT_TEXT_COLOR = "#000000"
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
FONT_DIRECTORY = Path(settings.BASE_DIR) / "static" / "fonts"
REGULAR_FONT_PATH = FONT_DIRECTORY / "ComicNeue-Regular.ttf"
BOLD_FONT_PATH = FONT_DIRECTORY / "ComicNeue-Bold.ttf"
ITALIC_FONT_PATH = FONT_DIRECTORY / "ComicNeue-Italic.ttf"
BANGERS_FONT_PATH = FONT_DIRECTORY / "Bangers-Regular.ttf"
BOX_FIELDS = ("x", "y", "width", "height")


@dataclass(frozen=True)
class FontSpec:
    """Archivo TTF de una fuente y cómo la declara @font-face en app.css."""

    path: Path
    css_family: str
    css_weight: int
    css_style: str


Font = TextRegion.FontFamily

FONTS = {
    Font.COMIC_NEUE: FontSpec(REGULAR_FONT_PATH, '"Comic Neue"', 400, "normal"),
    Font.COMIC_NEUE_BOLD: FontSpec(BOLD_FONT_PATH, '"Comic Neue"', 700, "normal"),
    Font.COMIC_NEUE_ITALIC: FontSpec(ITALIC_FONT_PATH, '"Comic Neue"', 400, "italic"),
    Font.BANGERS: FontSpec(BANGERS_FONT_PATH, "Bangers", 400, "normal"),
}

DEFAULT_FONT_BY_KIND = {
    TextRegion.Kind.BALLOON: Font.COMIC_NEUE,
    TextRegion.Kind.NARRATION: Font.COMIC_NEUE_ITALIC,
}


@lru_cache(maxsize=256)
def load_font(font_path, font_size):
    """Abre una fuente TTF a un tamaño; se reutiliza entre llamadas."""
    return ImageFont.truetype(str(font_path), font_size)


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
        font = load_font(font_path, font_size)
        latest_lines = wrap_text(text, font, box_width)
        if lines_fit(latest_lines, font, box_width, box_height):
            return font_size, latest_lines
    return minimum, latest_lines


def font_key_for(region):
    """Identificador de la fuente efectiva: la elegida o la del tipo."""
    if region.font_family in FONTS:
        return region.font_family
    return DEFAULT_FONT_BY_KIND.get(region.kind, Font.COMIC_NEUE)


def font_path_for(region):
    """Archivo TTF de la fuente efectiva de la región."""
    return FONTS[font_key_for(region)].path


def effective_box(region):
    """Caja maquetada si existe; si no, la caja del OCR (x, y, ancho, alto)."""
    layout_box = (
        region.layout_x,
        region.layout_y,
        region.layout_width,
        region.layout_height,
    )
    if None in layout_box:
        return region.x, region.y, region.width, region.height
    return layout_box


def layout_padding(page):
    """Relleno interior de la caja, proporcional al ancho de la página."""
    return (page.width or 1) * PREVIEW_PADDING_RATIO


def auto_max_size(box_height):
    """Tope del ajuste automático: 72 px y el 70 % del alto de la caja."""
    return min(
        MAX_FONT_SIZE,
        max(MIN_FONT_SIZE, round(box_height * AUTO_SIZE_HEIGHT_RATIO)),
    )


def preview_text(region):
    """Elige traducción o texto fuente según el estado de la región."""
    return region.translation if region.translation else region.final_text


def layout_for_region(region, text=None):
    """Calcula la maquetación completa de una región (HU-89, CA-89.1).

    Devuelve la caja efectiva, la fuente, el tamaño (automático de 8 a 72 o
    fijo de 8 a 200), las líneas, el interlineado y el relleno en píxeles,
    la alineación, el color y si el texto cabe. Un tamaño fijo que no cabe
    se conserva con fits=False (ADR-003, P2).
    """
    text = preview_text(region) if text is None else text
    x, y, width, height = effective_box(region)
    padding = layout_padding(region.page)
    content_width = max(1, width - 2 * padding)
    content_height = max(1, height - 2 * padding)
    font_key = font_key_for(region)
    spec = FONTS[font_key]
    if region.font_size:
        font_size = region.font_size
        lines = wrap_text(text, load_font(spec.path, font_size), content_width)
    else:
        font_size, lines = fit_text(
            text,
            content_width,
            content_height,
            spec.path,
            auto_max_size(height),
            MIN_FONT_SIZE,
        )
    font = load_font(spec.path, font_size)
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "font_family": font_key,
        "font_size": font_size,
        "is_auto_size": not region.font_size,
        "lines": lines,
        "line_height": line_height(font),
        "padding": round(padding, 3),
        "text_align": region.text_align or TextRegion.TextAlign.CENTER,
        "text_color": region.text_color or DEFAULT_TEXT_COLOR,
        "fits": lines_fit(lines, font, content_width, content_height),
    }


def css_number(value):
    """Formatea un número para CSS con punto decimal y sin ceros sobrantes."""
    return f"{value:.5f}".rstrip("0").rstrip(".") or "0"


def page_ratio(page, pixels):
    """Convierte píxeles de la imagen en % del ancho de la página (cqw)."""
    return round(pixels / (page.width or 1) * 100, 5)


def preview_style(region, layout):
    """Variables CSS de la superposición: caja, tipografía y color."""
    page = region.page
    spec = FONTS[layout["font_family"]]
    variables = {
        "--preview-font-ratio": css_number(page_ratio(page, layout["font_size"])),
        "--preview-line-ratio": css_number(page_ratio(page, layout["line_height"])),
        "--preview-padding-ratio": css_number(page_ratio(page, layout["padding"])),
        "--preview-font-family": spec.css_family,
        "--preview-font-weight": spec.css_weight,
        "--preview-font-style": spec.css_style,
        "--preview-text-align": layout["text_align"],
        "--preview-text-color": layout["text_color"],
    }
    box = percent_box_style(
        page, layout["x"], layout["y"], layout["width"], layout["height"]
    )
    return box + "".join(f" {name}: {value};" for name, value in variables.items())


def skipped_preview(region):
    """Datos de una región "No traducir": no tiene superposición."""
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
        "style": region.overlay_style,
    }


def preview_for_region(region):
    """Construye los datos de una región para la vista previa (HU-87).

    Es una envoltura de layout_for_region: no hay un segundo cálculo.
    """
    if region.skip_translation:
        return skipped_preview(region)
    layout = layout_for_region(region)
    font_ratio = page_ratio(region.page, layout["font_size"])
    return {
        "region_pk": region.pk,
        "status": "translated" if region.translation else "untranslated",
        "lines": layout["lines"],
        "font_size": layout["font_size"],
        "font_ratio": font_ratio,
        "font_ratio_css": css_number(font_ratio),
        "fits": layout["fits"],
        "kind": region.kind,
        "overlay_style": region.overlay_style,
        "style": preview_style(region, layout),
        "layout": layout,
    }


# --- Validación y guardado ---------------------------------------------------


def parse_whole_number(value):
    """Convierte un valor enviado en entero, o None si no lo es."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def clean_box(region, data, errors):
    """Valida la caja enviada, completándola con la caja efectiva actual."""
    if not any(name in data for name in BOX_FIELDS):
        return None
    box = dict(zip(BOX_FIELDS, effective_box(region), strict=True))
    for name in BOX_FIELDS:
        if name not in data:
            continue
        number = parse_whole_number(data.get(name))
        if number is None:
            errors[name] = ["Escribe un número entero de píxeles."]
        box[name] = number
    if any(name in errors for name in BOX_FIELDS):
        return None
    return check_box_limits(region.page, box, errors)


def check_box_limits(page, box, errors):
    """Comprueba el tamaño mínimo y que la caja quede dentro de la imagen."""
    for name in ("width", "height"):
        if box[name] < MIN_BOX_SIZE:
            errors[name] = [
                f"La caja debe medir al menos {MIN_BOX_SIZE} px de ancho y de alto."
            ]
    inside = (
        box["x"] >= 0
        and box["y"] >= 0
        and box["x"] + box["width"] <= page.width
        and box["y"] + box["height"] <= page.height
    )
    if not inside:
        errors["box"] = ["La caja debe quedar dentro de la imagen."]
    return None if errors else box


def clean_font_family(value, errors):
    """Acepta una fuente de la lista, o vacío para la del tipo de región."""
    value = str(value).strip()
    if value and value not in FONTS:
        errors["font_family"] = ["Elige una de las fuentes disponibles."]
    return value


def clean_font_size(value, errors):
    """Acepta un tamaño fijo de 8 a 200 px, o vacío/«auto» para automático."""
    value = str(value).strip().lower()
    if value in ("", "auto"):
        return None
    number = parse_whole_number(value)
    if number is None or not MIN_FONT_SIZE <= number <= MAX_FIXED_FONT_SIZE:
        errors["font_size"] = [
            f"El tamaño debe estar entre {MIN_FONT_SIZE} y "
            f"{MAX_FIXED_FONT_SIZE} px, o ser automático."
        ]
    return number


def clean_text_align(value, errors):
    """Acepta izquierda, centro o derecha."""
    value = str(value).strip()
    if value not in TextRegion.TextAlign.values:
        errors["text_align"] = ["Elige alineación izquierda, centro o derecha."]
    return value


def clean_text_color(value, errors):
    """Acepta un color #RRGGBB y lo guarda en mayúsculas."""
    value = str(value).strip()
    if not HEX_COLOR_PATTERN.match(value):
        errors["text_color"] = ["Escribe el color con el formato #RRGGBB."]
    return value.upper()


STYLE_CLEANERS = {
    "font_family": clean_font_family,
    "font_size": clean_font_size,
    "text_align": clean_text_align,
    "text_color": clean_text_color,
}


def validate_layout(region, data):
    """Valida un cambio parcial de maquetación (HU-89, CA-89.3 y CA-89.4).

    Solo se validan los campos enviados: un arrastre manda la caja y el
    panel manda el estilo. Devuelve (datos limpios, errores por campo); si
    hay errores, los datos limpios no deben guardarse.
    """
    errors = {}
    cleaned = {}
    box = clean_box(region, data, errors)
    if box is not None:
        cleaned["box"] = box
    for name, cleaner in STYLE_CLEANERS.items():
        if name in data:
            cleaned[name] = cleaner(data.get(name), errors)
    return cleaned, errors


LAYOUT_UPDATE_FIELDS = [
    "layout_x",
    "layout_y",
    "layout_width",
    "layout_height",
    "font_family",
    "font_size",
    "text_align",
    "text_color",
    "layout_updated_at",
]


def store_layout(region):
    """Guarda la maquetación y deja la página sin maquetar (ADR-003, P1)."""
    with transaction.atomic():
        region.layout_updated_at = timezone.now()
        region.save(update_fields=LAYOUT_UPDATE_FIELDS)
        region.page.clear_typeset_approval()


def save_layout(region, cleaned):
    """Aplica los datos ya validados por validate_layout y los guarda."""
    box = cleaned.get("box")
    if box is not None:
        region.layout_x = box["x"]
        region.layout_y = box["y"]
        region.layout_width = box["width"]
        region.layout_height = box["height"]
    for name in STYLE_CLEANERS:
        if name in cleaned:
            setattr(region, name, cleaned[name])
    store_layout(region)


def reset_layout(region):
    """Vuelve a la caja del OCR y al estilo por defecto (CA-89.6)."""
    region.layout_x = None
    region.layout_y = None
    region.layout_width = None
    region.layout_height = None
    region.font_family = ""
    region.font_size = None
    region.text_align = TextRegion.TextAlign.CENTER
    region.text_color = DEFAULT_TEXT_COLOR
    store_layout(region)


# --- Aprobación de la maquetación --------------------------------------------


@dataclass
class TypesetApproval:
    """Resultado de pedir "Aprobar página" en la pestaña Maquetación."""

    is_approved: bool
    message: str
    warnings: list = field(default_factory=list)


def pending_translation_count(page):
    """Número de regiones con texto que traducir sin traducción aprobada."""
    return sum(
        1
        for region in page.regions.all()
        if region.needs_translation and not region.is_translation_approved
    )


def manual_cleaning_warning(page):
    """Aviso, sin bloquear, por regiones que necesitan limpieza manual."""
    count = page.regions.filter(
        cleaning_status=TextRegion.CleaningStatus.MANUAL,
        skip_translation=False,
    ).count()
    if not count:
        return []
    if count == 1:
        return ["1 región necesita limpieza manual: su texto original sigue visible."]
    return [
        f"{count} regiones necesitan limpieza manual: su texto original sigue "
        "visible."
    ]


def approval_blocker(page):
    """Motivo por el que no se puede aprobar la maquetación, o vacío (P7)."""
    if not page.has_cleaned_image:
        return "Limpia la página antes de aprobar la maquetación."
    if page.status != ComicPage.Status.APPROVED:
        pending = pending_translation_count(page)
        if pending == 1:
            return "Falta 1 traducción por aprobar."
        return f"Faltan {pending} traducciones por aprobar."
    return ""


def approve_typesetting(page):
    """Marca la página como "Maquetada" si cumple P7 (CA-89.7)."""
    blocker = approval_blocker(page)
    if blocker:
        return TypesetApproval(is_approved=False, message=blocker)
    page.typeset_approved_at = timezone.now()
    page.save(update_fields=["typeset_approved_at", "updated_at"])
    return TypesetApproval(
        is_approved=True,
        message="Página maquetada.",
        warnings=manual_cleaning_warning(page),
    )


# --- Renderizado --------------------------------------------------------------


def is_drawn(region):
    """Indica si la región lleva su traducción dibujada sobre la imagen."""
    return (
        region.needs_translation
        and region.is_translation_approved
        and bool(region.translation.strip())
    )


def keeps_original(region):
    """Indica si la región conserva el texto original (CA-90.4, CA-90.5).

    "No traducir", sin traducción aprobada, o aprobada vacía, que según
    ADR-002 T1 significa "dejar sin traducir".
    """
    if region.skip_translation:
        return True
    return region.needs_translation and not is_drawn(region)


def open_rgb(image_field):
    """Abre un ImageField como RGB y cierra el archivo al terminar.

    Igual que la limpieza (HU-88): sin girar por EXIF, para que las
    coordenadas de las regiones coincidan con las de la capa limpia.
    """
    with image_field.open("rb") as image_file, Image.open(image_file) as source:
        return source.convert("RGB")


def line_left(layout, advance, content_width):
    """Posición horizontal de una línea dentro del área de contenido."""
    padding = layout["padding"]
    if layout["text_align"] == TextRegion.TextAlign.LEFT:
        return padding
    if layout["text_align"] == TextRegion.TextAlign.RIGHT:
        return padding + content_width - advance
    return padding + (content_width - advance) / 2


def text_mask(layout, font_path):
    """Dibuja las líneas en una máscara del tamaño de la caja.

    Reproduce el modelo de caja del CSS de la superposición: bloque centrado
    en vertical, una caja de línea de line_height por línea con la línea
    base a medio interlineado, y recorte en el borde de la caja.
    """
    width, height = layout["width"], layout["height"]
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    font = load_font(font_path, layout["font_size"])
    ascent, descent = font.getmetrics()
    padding = layout["padding"]
    content_width = width - 2 * padding
    step = layout["line_height"]
    top = padding + (height - 2 * padding - step * len(layout["lines"])) / 2
    half_leading = (step - (ascent + descent)) / 2
    for index, line in enumerate(layout["lines"]):
        left = line_left(layout, font.getlength(line), content_width)
        baseline = top + index * step + half_leading + ascent
        draw.text((left, baseline), line, font=font, fill=255, anchor="ls")
    return mask


def draw_region_text(canvas, region):
    """Pinta la traducción aprobada de la región con su maquetación."""
    layout = layout_for_region(region, text=region.translation)
    mask = text_mask(layout, FONTS[layout["font_family"]].path)
    color = hex_to_rgb(layout["text_color"])
    box = (
        layout["x"],
        layout["y"],
        layout["x"] + layout["width"],
        layout["y"] + layout["height"],
    )
    canvas.paste(color, box, mask)


def hex_to_rgb(hex_color):
    """Convierte #RRGGBB en una tupla (r, g, b)."""
    value = hex_color.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def render_page(page):
    """Compone la página traducida en RGB (HU-89, CA-89.8; HU-90).

    Parte de la imagen limpia (o de la original si no hay), vuelve a pegar
    la zona original de las regiones que conservan su texto (P6) y dibuja
    las traducciones aprobadas con layout_for_region.
    """
    regions = list(page.regions.select_related("page").order_by("reading_order"))
    if not page.has_cleaned_image:
        canvas = open_rgb(page.image)
    else:
        canvas = open_rgb(page.cleaned_image)
        restored = [region for region in regions if keeps_original(region)]
        if restored:
            original = open_rgb(page.image)
            for region in restored:
                restore_original_area(original, canvas, region)
            original.close()
    for region in regions:
        if is_drawn(region):
            draw_region_text(canvas, region)
    return canvas
