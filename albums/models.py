"""Modelos de dominio de la app albums: catálogo de idiomas y álbumes."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


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
        """Número de páginas cargadas en el álbum.

        Devuelve 0 mientras no exista el modelo Page, que llega con HU-09.
        """
        return 0

    @property
    def progress_percentage(self):
        """Porcentaje de traducción aprobada, de 0 a 100.

        Devuelve 0 en el Sprint 1: la traducción llega en un sprint posterior.
        La guarda contra la división por cero queda escrita porque un álbum
        recién creado siempre tiene cero páginas, y es el caso que romperá en
        cuanto el numerador deje de ser constante.
        """
        total = self.page_count
        if not total:
            return 0
        translated = 0
        return round(translated / total * 100)
