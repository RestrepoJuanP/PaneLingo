"""Modelos de dominio de la app albums: idiomas, álbumes, páginas y regiones."""

import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
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


def album_cover_path(instance, filename):
    """Devuelve la ruta en disco de la portada de un álbum.

    Igual que con las páginas, el nombre lo genera el servidor; solo se
    conserva la extensión, que el formulario ya normalizó según el formato
    real de la imagen. Cuelga del usuario y no del álbum porque, al crear,
    el álbum aún no tiene identificador.
    """
    extension = Path(filename).suffix.lower() or ".jpg"
    return f"albums/user_{instance.owner_id}/covers/{uuid.uuid4().hex}{extension}"


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
    cover_image = models.ImageField(
        _("portada"),
        upload_to=album_cover_path,
        blank=True,
        help_text=_("Opcional. Sin portada se muestra la predeterminada."),
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
    def cover_url(self):
        """Dirección de la portada subida, o cadena vacía si usa la predeterminada.

        Apunta a la vista protegida, no a MEDIA_URL: la portada es una imagen
        del usuario y solo la puede descargar su propietario (DT-02).
        """
        if not self.cover_image:
            return ""
        return reverse("albums:album_cover", kwargs={"pk": self.pk})

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

    Al cargarse queda en PENDING. HU-12 la lleva a PROCESSING mientras se
    detectan sus regiones de texto, a PROCESSED cuando termina y a FAILED si
    la detección falla. NEEDS_REVIEW y APPROVED los alcanzan el OCR y la
    revisión de historias posteriores.
    """

    class Status(models.TextChoices):
        """Estados por los que pasa una página desde que se carga."""

        PENDING = "pending", _("Pendiente de procesamiento")
        PROCESSING = "processing", _("Procesando")
        PROCESSED = "processed", _("Procesada")
        NEEDS_REVIEW = "needs_review", _("Necesita revisión")
        APPROVED = "approved", _("Aprobada")
        # Decisión del equipo del 2026-10-20 sobre la pregunta abierta de
        # HU-12: un fallo de la detección se distingue de una página que
        # nunca se procesó, en lugar de devolverla a PENDING.
        FAILED = "failed", _("Error")

    class TranslationState(models.TextChoices):
        """Estado de la tarea de traducción de la página (HU-16, ADR-002).

        Va aparte de Status para no mezclar el OCR con la traducción: una
        página puede estar "Procesada" y, a la vez, traduciéndose.
        """

        IDLE = "idle", _("En reposo")
        TRANSLATING = "translating", _("Traduciendo")
        FAILED = "failed", _("Error de traducción")

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
    processing_started_at = models.DateTimeField(
        _("inicio del procesamiento"),
        null=True,
        blank=True,
        help_text=_("Permite detectar un procesamiento que quedó colgado."),
    )
    processing_error = models.CharField(
        _("error del último procesamiento"),
        max_length=255,
        blank=True,
        help_text=_("Motivo del último fallo, para mostrarlo junto a Reintentar."),
    )
    translation_state = models.CharField(
        _("estado de la traducción"),
        max_length=20,
        choices=TranslationState.choices,
        default=TranslationState.IDLE,
        help_text=_("Tarea de traducción de la página (HU-16), aparte del OCR."),
    )
    translation_started_at = models.DateTimeField(
        _("inicio de la traducción"),
        null=True,
        blank=True,
        help_text=_("Permite detectar una traducción que quedó colgada."),
    )
    translation_error = models.CharField(
        _("error de la última traducción"),
        max_length=255,
        blank=True,
        help_text=_("Motivo del último fallo, para mostrarlo junto a Reintentar."),
    )
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

    # Etiqueta breve para el chip de la rejilla. La celda mide 146 px y la
    # etiqueta larga de PENDING, "Pendiente de procesamiento", no cabe: con
    # white-space: nowrap se desbordaba y pisaba las acciones de la miniatura.
    # El mockup usa etiquetas de entre ocho y doce caracteres por el mismo
    # motivo. La forma larga se sigue usando donde hay sitio, como la cola de
    # carga.
    SHORT_STATUS_LABELS = {
        "pending": _("Pendiente"),
        "processing": _("Procesando"),
        "processed": _("Procesada"),
        "needs_review": _("Revisar"),
        "approved": _("Aprobada"),
        "failed": _("Error"),
    }

    # Variante del chip de estado para cada estado de la página.
    STATUS_VARIANTS = {
        "pending": "neutral",
        "processing": "progress",
        "processed": "success",
        "needs_review": "warning",
        "approved": "success",
        "failed": "danger",
    }

    @property
    def status_variant(self):
        """Devuelve la variante de color del chip de estado."""
        return self.STATUS_VARIANTS.get(self.status, "neutral")

    @property
    def short_status_display(self):
        """Devuelve la etiqueta breve del estado, para la rejilla."""
        return self.SHORT_STATUS_LABELS.get(self.status, self.get_status_display())

    def get_absolute_url(self):
        """Devuelve la dirección de la vista de esta página."""
        return reverse("albums:page_detail", kwargs={"pk": self.pk})

    def get_delete_url(self):
        """Devuelve la dirección para eliminar esta página."""
        return reverse("albums:page_delete", kwargs={"pk": self.pk})

    def get_process_url(self):
        """Devuelve la dirección para procesar esta página."""
        return reverse("albums:page_process", kwargs={"pk": self.pk})

    def get_status_url(self):
        """Devuelve la dirección del estado de procesamiento, en JSON."""
        return reverse("albums:page_status", kwargs={"pk": self.pk})

    # Las imágenes se piden por estas direcciones protegidas y nunca por
    # MEDIA_URL: así una página ajena responde 404 aunque se conozca su
    # dirección (HU-11, CA-11.4, deuda DT-02).

    def get_image_url(self):
        """Devuelve la dirección protegida de la imagen original."""
        return reverse("albums:page_image", kwargs={"pk": self.pk})

    def get_thumbnail_url(self):
        """Devuelve la dirección protegida de la miniatura."""
        return reverse("albums:page_thumbnail", kwargs={"pk": self.pk})

    @property
    def display_image_url(self):
        """Dirección de la miniatura, que cae en el original si no la hay."""
        return self.get_thumbnail_url()

    @property
    def is_processing(self):
        """Indica si la página se está procesando y aún no se dio por perdida."""
        return self.status == self.Status.PROCESSING and not self.is_processing_stale

    @property
    def is_processing_stale(self):
        """Indica si el procesamiento lleva demasiado tiempo sin terminar.

        Si el trabajador de tareas se cae a mitad de una página, nadie la saca
        de PROCESSING. Pasado PROCESSING_STALE_AFTER se trata como un fallo y
        se ofrece reintentar, en lugar de dejarla bloqueada para siempre.
        """
        if self.status != self.Status.PROCESSING or not self.processing_started_at:
            return False
        limit = timedelta(seconds=settings.PROCESSING_STALE_AFTER)
        return timezone.now() - self.processing_started_at > limit

    @property
    def was_processed(self):
        """Indica si la última detección de regiones terminó bien."""
        return self.status in (
            self.Status.PROCESSED,
            self.Status.NEEDS_REVIEW,
            self.Status.APPROVED,
        )

    @property
    def has_failed(self):
        """Indica si la última detección falló."""
        return self.status == self.Status.FAILED

    def get_translate_url(self):
        """Devuelve la dirección para traducir la página con IA (HU-16)."""
        return reverse("albums:page_translate", kwargs={"pk": self.pk})

    @property
    def is_translating(self):
        """Indica si la página se está traduciendo y aún no se dio por perdida."""
        return (
            self.translation_state == self.TranslationState.TRANSLATING
            and not self.is_translation_stale
        )

    @property
    def is_translation_stale(self):
        """Indica si la traducción lleva demasiado tiempo sin terminar.

        Mismo criterio que el OCR (ADR-001): si el trabajador se cae, la
        página no puede quedarse "Traduciendo" para siempre.
        """
        if (
            self.translation_state != self.TranslationState.TRANSLATING
            or not self.translation_started_at
        ):
            return False
        limit = timedelta(seconds=settings.PROCESSING_STALE_AFTER)
        return timezone.now() - self.translation_started_at > limit

    @property
    def translation_failed(self):
        """Indica si la última traducción falló."""
        return self.translation_state == self.TranslationState.FAILED

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


class TextRegion(models.Model):
    """Región de una página que contiene texto.

    HU-12 la detecta con su posición y su tipo; HU-13 le añade el texto
    reconocido, la confianza del OCR y si necesita revisión.

    La posición se guarda en píxeles de la imagen original, no en
    porcentajes: así no depende del tamaño con que se muestre la página.
    """

    class Kind(models.TextChoices):
        """Tipos de región que distingue la interfaz."""

        BALLOON = "balloon", _("Globo de diálogo")
        NARRATION = "narration", _("Cuadro narrativo")

    class TranslationStatus(models.TextChoices):
        """Estados de la traducción de una región (HU-16 a HU-19, ADR-002)."""

        UNTRANSLATED = "untranslated", _("Sin traducir")
        GENERATED = "generated", _("Generada")
        EDITED = "edited", _("Editada")
        APPROVED = "approved", _("Aprobada")

    # Variante del chip de estado de la traducción, como en el mockup.
    TRANSLATION_VARIANTS = {
        "untranslated": "neutral",
        "generated": "progress",
        "edited": "warning",
        "approved": "success",
    }

    page = models.ForeignKey(
        ComicPage,
        on_delete=models.CASCADE,
        related_name="regions",
        verbose_name=_("página"),
    )
    reading_order = models.PositiveIntegerField(_("orden de lectura"))
    kind = models.CharField(
        _("tipo"), max_length=20, choices=Kind.choices, default=Kind.BALLOON
    )
    x = models.PositiveIntegerField(_("posición horizontal"))
    y = models.PositiveIntegerField(_("posición vertical"))
    width = models.PositiveIntegerField(_("ancho"))
    height = models.PositiveIntegerField(_("alto"))
    source_text = models.TextField(
        _("texto de origen"),
        blank=True,
        help_text=_("Texto que reconoció el OCR, en orden de lectura (HU-13)."),
    )
    confidence = models.FloatField(
        _("confianza"),
        null=True,
        blank=True,
        help_text=_("De 0 a 1. Vacía si el proveedor no la informó."),
    )
    needs_review = models.BooleanField(
        _("necesita revisión"),
        default=False,
        help_text=_("Texto vacío, de baja confianza o en otro alfabeto."),
    )
    corrected_text = models.TextField(
        _("texto corregido"),
        blank=True,
        help_text=_("Corrección del usuario (HU-15). Vacía y corregida: sin texto."),
    )
    is_corrected = models.BooleanField(
        _("revisada por el usuario"),
        default=False,
        help_text=_("Distingue una corrección vacía de una región sin corregir."),
    )
    corrected_at = models.DateTimeField(_("corregida"), null=True, blank=True)
    machine_translation = models.TextField(
        _("propuesta de la IA"),
        blank=True,
        help_text=_("Última traducción que propuso la IA. Se conserva al editar."),
    )
    translation = models.TextField(
        _("traducción"),
        blank=True,
        help_text=_("Texto de trabajo: el que se revisa, edita y aprueba."),
    )
    translation_status = models.CharField(
        _("estado de la traducción"),
        max_length=20,
        choices=TranslationStatus.choices,
        default=TranslationStatus.UNTRANSLATED,
    )
    translated_at = models.DateTimeField(_("traducida"), null=True, blank=True)
    approved_at = models.DateTimeField(_("aprobada"), null=True, blank=True)
    created_at = models.DateTimeField(_("detectada"), auto_now_add=True)

    class Meta:
        verbose_name = _("región de texto")
        verbose_name_plural = _("regiones de texto")
        ordering = ["reading_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["page", "reading_order"],
                name="unique_reading_order_per_page",
            )
        ]

    def __str__(self):
        """Devuelve la región identificada por su número de orden."""
        return f"Región {self.reading_order}"

    @property
    def final_text(self):
        """Texto que vale para traducir: el corregido si lo hay, si no el del OCR.

        Es el que debe usar la traducción de HU-16 (CA-15.2).
        """
        return self.corrected_text if self.is_corrected else self.source_text

    @property
    def has_nothing_to_translate(self):
        """Indica si el usuario vació la región a propósito (CA-15.5)."""
        return self.is_corrected and not self.corrected_text

    def get_correct_url(self):
        """Devuelve la dirección para corregir o restaurar esta región."""
        return reverse("albums:region_correct", kwargs={"pk": self.pk})

    def get_translation_url(self):
        """Devuelve la dirección para guardar la traducción editada (HU-18)."""
        return reverse("albums:region_translation_edit", kwargs={"pk": self.pk})

    def get_retranslate_url(self):
        """Devuelve la dirección para volver a traducir solo esta región."""
        return reverse("albums:region_retranslate", kwargs={"pk": self.pk})

    @property
    def needs_translation(self):
        """Indica si la región tiene texto que traducir (ADR-002, T5).

        Las regiones que el usuario vació a propósito (CA-15.5) y las que el
        OCR dejó sin texto no se traducen ni cuentan como pendientes.
        """
        return bool(self.final_text.strip())

    @property
    def is_translation_approved(self):
        """Indica si la traducción está aprobada (HU-19)."""
        return self.translation_status == self.TranslationStatus.APPROVED

    @property
    def translation_variant(self):
        """Devuelve la variante de color del chip de la traducción."""
        return self.TRANSLATION_VARIANTS.get(self.translation_status, "neutral")

    @property
    def confidence_percent(self):
        """Devuelve la confianza como porcentaje entero, o None si no hay."""
        if self.confidence is None:
            return None
        return round(self.confidence * 100)

    @property
    def overlay_style(self):
        """Devuelve la posición de la región en porcentajes, como estilo CSS.

        Se formatea aquí y no en la plantilla porque el idioma de la interfaz
        escribe los decimales con coma, y CSS solo entiende el punto.
        """
        page_width = self.page.width or 1
        page_height = self.page.height or 1
        left = self.x / page_width * 100
        top = self.y / page_height * 100
        width = self.width / page_width * 100
        height = self.height / page_height * 100
        return (
            f"left: {left:.3f}%; top: {top:.3f}%; "
            f"width: {width:.3f}%; height: {height:.3f}%;"
        )
