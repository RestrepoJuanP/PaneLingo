"""Conversión de modos de color de las páginas (HU-90, ADR-003).

Una sola función para pasar cualquier página a RGB de 8 bits, que usan la
miniatura, la limpieza, el editor y la exportación: así lo que se ve en el
editor coincide con el PNG exportado.

Por qué existe: Image.convert("RGB") o convert("L") de Pillow RECORTA los
modos de 16 y 32 bits en lugar de escalarlos. Un PNG en gris de 16 bits (que
Pillow abre como "I;16") con un gris del 25 % (16384 de 65535) salía blanco
puro en la miniatura, en la capa limpia y, por tanto, en el editor, aunque
el navegador mostrara bien el original.
"""

from PIL import Image

# Modos de más de 8 bits por canal. Los formatos admitidos (PNG, JPEG, WebP)
# solo producen "I;16*" (PNG gris de 16 bits); "I" y "F" se tratan con el
# mismo rango de 16 bits por si una versión de Pillow los devolviera.
HIGH_DEPTH_MODES = ("I;16", "I;16L", "I;16B", "I;16N", "I", "F")
SIXTEEN_BIT_MAX = 65535
EIGHT_BIT_SCALE = SIXTEEN_BIT_MAX / 255
GRAYSCALE_MODES = ("1", "L", "LA", "La", *HIGH_DEPTH_MODES)
PALETTE_MODES = ("P", "PA")
MAX_PALETTE_COLORS = 256


def to_eight_bit(image):
    """Escala una imagen de 16 o 32 bits a gris de 8 bits ("L").

    Las imágenes de 8 bits se devuelven sin cambios.
    """
    if image.mode not in HIGH_DEPTH_MODES:
        return image
    wide = image.convert("I")
    return wide.point(lambda value: value / EIGHT_BIT_SCALE).convert("L")


def to_rgb(image):
    """Convierte cualquier página en RGB de 8 bits, sin canal alfa.

    El alfa se descarta igual que antes (las páginas de cómic son opacas),
    para no cambiar lo que ya muestran la limpieza y el editor.
    """
    return to_eight_bit(image).convert("RGB")


def palette_is_gray(image):
    """Indica si una imagen con paleta solo usa colores grises (R = G = B).

    Se miran solo los índices que la imagen usa de verdad: una paleta puede
    traer entradas de color que ningún píxel usa.
    """
    palette = image.getpalette() or []
    used = image.getcolors(maxcolors=MAX_PALETTE_COLORS) or []
    for _count, color in used:
        index = color[0] if isinstance(color, tuple) else color
        red, green, blue = palette[index * 3 : index * 3 + 3]
        if not red == green == blue:
            return False
    return True


def export_mode(image):
    """Modo del PNG exportado: "L" para páginas en gris y "RGB" para el resto.

    Nunca hay canal alfa (CA-90.3). Las paletas salen en "L" si todos los
    colores que usan son grises y en "RGB" si no.
    """
    if image.mode in GRAYSCALE_MODES:
        return "L"
    if image.mode in PALETTE_MODES and palette_is_gray(image):
        return "L"
    return "RGB"


def open_rgb(storage, name):
    """Abre un archivo del almacenamiento como RGB de 8 bits y lo cierra."""
    with storage.open(name, "rb") as image_file, Image.open(image_file) as source:
        return to_rgb(source)
