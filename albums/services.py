"""Servicios de la app albums: carga de páginas (HU-09)."""

import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from PIL import Image

from albums.models import ComicPage
from albums.validators import InvalidPageImageError, validate_page_image


class RejectedUpload:
    """Un archivo del lote que no pudo cargarse, con su motivo."""

    def __init__(self, filename, reason):
        """Guarda el nombre original del archivo y el motivo del rechazo."""
        self.filename = filename
        self.reason = reason


def build_thumbnail(uploaded_file):
    """Genera la miniatura de una página y la devuelve como archivo.

    Sin miniatura, la rejilla del álbum descargaría la imagen original de
    varios megapíxeles para mostrarla a 146 px: con veinticuatro páginas
    serían decenas de megabytes por visita.

    Se genera aquí, en la carga, y no bajo demanda: hacerlo más tarde
    obligaría a una migración de datos para rellenar las páginas ya cargadas.
    """
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as image:
        # Las páginas de cómic son opacas; convertir a RGB permite guardar en
        # JPEG, que para una miniatura pesa bastante menos que PNG.
        thumbnail = image.convert("RGB")
        side = settings.THUMBNAIL_MAX_SIDE
        thumbnail.thumbnail((side, side))
        buffer = io.BytesIO()
        thumbnail.save(buffer, format="JPEG", quality=82, optimize=True)

    uploaded_file.seek(0)
    return ContentFile(buffer.getvalue())


def next_page_number(album):
    """Devuelve el siguiente número de página libre del álbum."""
    last = (
        album.pages.order_by("-page_number")
        .values_list("page_number", flat=True)
        .first()
    )
    return (last or 0) + 1


def create_page(album, uploaded_file, page_number):
    """Crea una página a partir de un archivo ya validado."""
    width, height, extension = validate_page_image(uploaded_file)

    page = ComicPage(
        album=album,
        page_number=page_number,
        original_filename=(uploaded_file.name or "")[:255],
        width=width,
        height=height,
        file_size=uploaded_file.size,
    )
    # page_image_path lee esto para poner en disco la extensión del formato
    # realmente detectado, no la del nombre que envió el cliente.
    page.image_extension = extension

    thumbnail = build_thumbnail(uploaded_file)
    page.thumbnail.save("thumb.jpg", thumbnail, save=False)
    page.image.save(f"page{extension}", uploaded_file, save=False)
    page.save()
    return page


def create_pages_from_upload(album, uploaded_files):
    """Carga un lote de archivos y devuelve las páginas creadas y los rechazos.

    Un archivo inválido NO aborta el lote: los válidos se cargan y de cada
    rechazo se informa con su motivo, que es lo que pide CA-09.2. Abortar todo
    obligaría a quien sube veinte páginas a repetir la carga entera por culpa
    de una mala.

    Los números de página continúan la secuencia existente del álbum. La
    asignación va dentro de una transacción, y la restricción de unicidad de
    (album, page_number) queda como red de seguridad ante cargas simultáneas.
    """
    created = []
    rejected = []

    with transaction.atomic():
        page_number = next_page_number(album)
        for uploaded_file in uploaded_files:
            try:
                page = create_page(album, uploaded_file, page_number)
            except InvalidPageImageError as error:
                rejected.append(
                    RejectedUpload(uploaded_file.name or "archivo", str(error))
                )
                continue
            created.append(page)
            page_number += 1

    return created, rejected
