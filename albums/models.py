"""Modelos de dominio de la app albums: catálogo de idiomas y álbumes."""

import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from albums.validators import is_low_resolution


class Language(models.Model):
    """Idioma disponible como origen o destino de una traducción.

    El catálogo se rellena mediante una migración de datos, no desde la
    interfaz: en el Sprint 1 no existe ninguna historia de usuario que permita
    añadir o retirar idiomas.
    """

    code = models.CharField(
        _("código"),
        max_length=10,
        unique=True,
        help_text=_("Código corto del idioma, por ejemplo ja o pt-br."),
    )
    name = models.CharField(_("nombre"), max_length=60)

    class Meta:
        verbose_name = _("idioma")
        verbose_name_plural = _("idiomas")
        ordering = ["name"]

    def __str__(self):
        """Devuelve el nombre del idioma."""
        return self.name


class Album(models.Model):
    """Álbum: conjunto de páginas de un mismo cómic, manga o webtoon.

    El título NO es único por propietario, y es una decisión deliberada. Un
    traductor puede trabajar la misma obra hacia dos idiomas distintos —por
    ejemplo "Neon Yokai Bureau" de japonés a inglés y de japonés a español—, y
    una restricción de unicidad le obligaría a inventar nombres artificiales
    para esquivarla. Ningún criterio de aceptación del Sprint 1 pide unicidad.
    Las tarjetas de la biblioteca muestran el par de idiomas, así que dos
    álbumes homónimos se distinguen a simple vista.
    """

    class Status(models.TextChoices):
        """Estados por los que pasa un álbum a lo largo de su traducción."""

        DRAFT = "draft", _("Borrador")
        IN_PROGRESS = "in_progress", _("En progreso")
        IN_REVIEW = "in_review", _("En revisión")
        COMPLETED = "completed", _("Completado")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="albums",
        verbose_name=_("propietario"),
    )
    title = models.CharField(_("título"), max_length=120)
    source_language = models.ForeignKey(
        Language,
        # PROTECT y no CASCADE: retirar un idioma del catálogo no puede
        # llevarse por delante los álbumes que lo usan.
        on_delete=models.PROTECT,
        related_name="albums_as_source",
        verbose_name=_("idioma de origen"),
    )
    target_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="albums_as_target",
        verbose_name=_("idioma de destino"),
    )
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(_("creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("álbum")
        verbose_name_plural = _("álbumes")
        ordering = ["-updated_at"]
        indexes = [
            models.Index(
                fields=["owner", "-updated_at"],
                name="album_owner_recent_idx",
            ),
            models.Index(fields=["status"], name="album_status_idx"),
        ]

    def __str__(self):
        """Devuelve el título del álbum."""
        return self.title

    def get_absolute_url(self):
        """Devuelve la dirección del detalle de este álbum."""
        return reverse("albums:detail", kwargs={"pk": self.pk})

    def get_edit_url(self):
        """Devuelve la dirección para editar este álbum."""
        return reverse("albums:edit", kwargs={"pk": self.pk})

    def get_upload_url(self):
        """Devuelve la dirección para cargar páginas en este álbum."""
        return reverse("albums:upload", kwargs={"pk": self.pk})

    def get_rename_url(self):
        """Devuelve la dirección para renombrar este álbum."""
        return reverse("albums:rename", kwargs={"pk": self.pk})

    @property
    def language_pair(self):
        """Devuelve el par de idiomas en formato corto, como JA → ES."""
        source = self.source_language.code.upper()
        target = self.target_language.code.upper()
        return f"{source} → {target}"

    @property
    def page_count(self):
        """Número de páginas cargadas en el álbum."""
        return self.pages.count()

    @property
    def progress_percentage(self):
        """Porcentaje de páginas aprobadas, de 0 a 100.

        En el Sprint 1 devuelve siempre 0, porque ninguna página llega a
        aprobarse: eso ocurre tras la revisión de la traducción, que es de un
        sprint posterior. La guarda contra la división por cero protege el
        caso de un álbum sin páginas, que es el habitual nada más crearlo.
        """
        total = self.page_count
        if not total:
            return 0
        approved = self.pages.filter(status=ComicPage.Status.APPROVED).count()
        return round(approved / total * 100)


def page_image_path(instance, filename):
    """Devuelve la ruta en disco de la imagen de una página.

    El nombre del archivo lo genera ENTERAMENTE el servidor; el que envió el
    cliente se descarta. No se sanea, se sustituye, y la diferencia importa:
    sanear obliga a acertar con una lista de casos —recorrido de rutas,
    nombres reservados de Windows como CON o NUL, longitudes desmesuradas,
    unicode ambiguo, doble extensión— y basta fallar en uno. Generando el
    nombre completo, ninguno de esos casos llega al sistema de archivos.

    El identificador aleatorio evita además que dos usuarios que suban
    "pagina1.png" colisionen, y que el nombre en disco delate el orden de
    carga o el número de páginas de un álbum.

    El nombre original se conserva en ComicPage.original_filename para poder
    mostrarlo, que es otra cosa distinta de escribirlo en disco.
    """
    extension = instance.image_extension or ".jpg"
    return (
        f"albums/user_{instance.album.owner_id}"
        f"/album_{instance.album_id}"
        f"/{uuid.uuid4().hex}{extension}"
    )


def page_thumbnail_path(instance, filename):
    """Devuelve la ruta en disco de la miniatura de una página."""
    return (
        f"albums/user_{instance.album.owner_id}"
        f"/album_{instance.album_id}"
        f"/thumbs/{uuid.uuid4().hex}.jpg"
    )


class ComicPage(models.Model):
    """Página de un álbum: la imagen completa de una plancha del cómic.

    En el Sprint 1 las páginas se cargan y se listan, nada más. El estado
    queda en PENDING; los demás valores existen para el OCR y la revisión de
    sprints posteriores, y ninguna historia de este sprint los alcanza.
    """

    class Status(models.TextChoices):
        """Estados por los que pasa una página desde que se carga."""

        PENDING = "pending", _("Pendiente de procesamiento")
        PROCESSING = "processing", _("Procesando")
        PROCESSED = "processed", _("Procesada")
        NEEDS_REVIEW = "needs_review", _("Necesita revisión")
        APPROVED = "approved", _("Aprobada")

    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name="pages",
        verbose_name=_("álbum"),
    )
    page_number = models.PositiveIntegerField(_("número de página"))
    image = models.ImageField(_("imagen"), upload_to=page_image_path)
    thumbnail = models.ImageField(
        _("miniatura"),
        upload_to=page_thumbnail_path,
        blank=True,
        help_text=_("Versión reducida para la rejilla del álbum. Se genera al cargar."),
    )
    status = models.CharField(
        _("estado"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    original_filename = models.CharField(_("nombre original"), max_length=255)
    width = models.PositiveIntegerField(_("ancho en píxeles"))
    height = models.PositiveIntegerField(_("alto en píxeles"))
    file_size = models.PositiveIntegerField(_("tamaño en bytes"))
    created_at = models.DateTimeField(_("creada"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizada"), auto_now=True)

    # No es un campo: lo fija el servicio de carga antes de guardar, para que
    # page_image_path conozca la extensión del formato realmente detectado.
    image_extension = None

    class Meta:
        verbose_name = _("página")
        verbose_name_plural = _("páginas")
        ordering = ["page_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["album", "page_number"],
                name="unique_page_number_per_album",
            )
        ]
        indexes = [
            models.Index(fields=["album", "page_number"], name="page_album_order_idx"),
        ]

    def __str__(self):
        """Devuelve la página identificada por su número."""
        return f"Página {self.page_number}"

    @property
    def has_low_resolution(self):
        """Indica si la página lleva advertencia de baja resolución.

        Delega en el validador para que la regla viva en un único sitio: si el
        umbral se recalibra cuando exista el OCR, no puede quedar una copia
        con el valor antiguo.
        """
        return is_low_resolution(self.width, self.height)

    @property
    def display_image(self):
        """Devuelve la miniatura si existe, y si no la imagen original."""
        return self.thumbnail if self.thumbnail else self.image
