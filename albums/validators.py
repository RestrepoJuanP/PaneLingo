"""Validación de las imágenes de página que se cargan (HU-09).

La regla de fondo es que **nada de lo que envía el cliente se cree**: ni la
extensión del nombre, ni el content_type de la petición. Lo único que
determina si un archivo es una imagen, y de qué tipo, es abrirlo con Pillow.
"""

import warnings

from django.conf import settings
from PIL import Image, UnidentifiedImageError

# Umbral propio de Pillow para las "decompression bombs". Se fija al arrancar
# el módulo con el valor del proyecto, porque el que trae Pillow por defecto
# solo emite un aviso y no detiene la carga.
Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS

# Formatos que Pillow puede detectar y su extensión canónica en disco. La
# extensión sale de aquí, del formato REAL, y no del nombre que envió el
# cliente: un archivo llamado "pagina.png" que en realidad es un JPEG se
# guarda como .jpg.
FORMAT_EXTENSIONS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


class InvalidPageImageError(Exception):
    """El archivo cargado no puede aceptarse como página de un álbum.

    Lleva un mensaje en español, dirigido a la persona que hizo la carga, que
    dice qué pasó y qué puede hacer al respecto.
    """


def human_size(size_in_bytes):
    """Devuelve un tamaño en bytes expresado en megabytes, para los mensajes."""
    return f"{size_in_bytes / 1_000_000:.0f} MB"


def _check_size(uploaded_file):
    """Rechaza los archivos que superen el tamaño máximo permitido."""
    if uploaded_file.size > settings.MAX_FILE_SIZE:
        raise InvalidPageImageError(
            f"Pesa {human_size(uploaded_file.size)} y el máximo por archivo "
            f"es {human_size(settings.MAX_FILE_SIZE)}."
        )
    if uploaded_file.size == 0:
        raise InvalidPageImageError("El archivo está vacío.")


def _check_extension(uploaded_file):
    """Comprueba la extensión del nombre como primer filtro, no como prueba.

    Sirve para dar un mensaje claro y barato antes de abrir el archivo. La
    comprobación que de verdad decide es la de Pillow, más abajo: una
    extensión permitida no garantiza nada sobre el contenido.
    """
    name = (uploaded_file.name or "").lower()
    if not any(name.endswith(ext) for ext in settings.ALLOWED_IMAGE_EXTENSIONS):
        allowed = ", ".join(
            ext.lstrip(".").upper() for ext in settings.ALLOWED_IMAGE_EXTENSIONS
        )
        raise InvalidPageImageError(
            f"El formato no está admitido. Se aceptan {allowed}."
        )


def _open_checking_bombs(uploaded_file):
    """Abre la imagen convirtiendo el aviso de bomba en un rechazo.

    Pillow comprueba las dimensiones declaradas en la cabecera al abrir, antes
    de decodificar píxeles, así que una imagen desmesurada se detiene aquí sin
    llegar a reservar memoria. Por encima de MAX_IMAGE_PIXELS emite un aviso y
    por encima del doble lanza un error; el aviso se eleva a error para que
    ambos casos se traten igual.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        return Image.open(uploaded_file)


def validate_page_image(uploaded_file):
    """Valida un archivo cargado y devuelve (ancho, alto, extensión).

    El orden importa y es la parte delicada de esta función:

    1. Se abre y se llama a verify(), que recorre el archivo entero para
       detectar truncamientos o datos corruptos.
    2. verify() CONSUME el archivo y deja la instancia inservible, así que hay
       que rebobinar y volver a abrir para leer dimensiones y formato.
    3. Antes de devolver se rebobina otra vez, porque quien llame va a guardar
       el archivo a continuación. Sin ese último seek(0), Django escribiría
       desde la posición donde quedó el puntero y el archivo acabaría truncado
       o vacío en disco, con la validación en verde. Es un fallo silencioso:
       no lanza nada y solo se descubre al intentar abrir la página guardada.

    Lanza InvalidPageImageError con un mensaje en español si el archivo no sirve.
    """
    _check_size(uploaded_file)
    _check_extension(uploaded_file)

    try:
        uploaded_file.seek(0)
        _open_checking_bombs(uploaded_file).verify()
    except Image.DecompressionBombWarning as error:
        raise InvalidPageImageError(
            "La imagen declara unas dimensiones desproporcionadas y no se "
            "puede procesar con seguridad."
        ) from error
    except Image.DecompressionBombError as error:
        raise InvalidPageImageError(
            "La imagen declara unas dimensiones desproporcionadas y no se "
            "puede procesar con seguridad."
        ) from error
    except UnidentifiedImageError as error:
        raise InvalidPageImageError(
            "El archivo no es una imagen, aunque su nombre lo parezca."
        ) from error
    except OSError as error:
        raise InvalidPageImageError(
            "La imagen está dañada o incompleta. Vuelve a exportarla e "
            "inténtalo de nuevo."
        ) from error

    # verify() dejó la instancia inutilizable: hay que reabrir para poder
    # consultar tamaño y formato.
    try:
        uploaded_file.seek(0)
        image = _open_checking_bombs(uploaded_file)
        width, height = image.size
        detected_format = image.format
    except (UnidentifiedImageError, OSError) as error:
        raise InvalidPageImageError(
            "La imagen está dañada o incompleta. Vuelve a exportarla e "
            "inténtalo de nuevo."
        ) from error

    if detected_format not in FORMAT_EXTENSIONS:
        allowed = ", ".join(FORMAT_EXTENSIONS)
        raise InvalidPageImageError(
            f"El contenido del archivo es {detected_format}, que no está "
            f"admitido. Se aceptan {allowed}."
        )

    if not width or not height:
        raise InvalidPageImageError("La imagen no tiene dimensiones válidas.")

    # Rebobinado final: quien llame guarda el archivo justo después.
    uploaded_file.seek(0)
    return width, height, FORMAT_EXTENSIONS[detected_format]


def is_low_resolution(width, height):
    """Indica si la página debe llevar advertencia de baja resolución.

    Es advertencia, nunca bloqueo: la página se carga igual.
    """
    return width * height < settings.LOW_RESOLUTION_PIXELS
