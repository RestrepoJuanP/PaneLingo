"""Progreso y resúmenes de trabajo calculados a partir de los datos reales.

Alimentan los elementos del mockup que en el Sprint 1 no tenían datos: el
estado de cada álbum (HU-26), las barras de progreso, las estadísticas de la
biblioteca, la banda "Continuar donde lo dejaste" y la tarjeta de cuota de
la barra lateral. Todo sale de páginas y regiones; aquí no se inventa cifra
alguna.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db.models import Avg, Count, Q
from django.utils import timezone

from albums.models import Album, ComicPage, TextRegion

# Páginas cuya detección ya terminó.
DONE_STATUSES = (
    ComicPage.Status.PROCESSED,
    ComicPage.Status.NEEDS_REVIEW,
    ComicPage.Status.APPROVED,
)
# Páginas en las que todavía queda procesar algo.
WORK_STATUSES = (
    ComicPage.Status.PENDING,
    ComicPage.Status.PROCESSING,
    ComicPage.Status.FAILED,
)


@dataclass(frozen=True)
class StatusChip:
    """Estado mostrado como chip: clave, texto y variante de color."""

    key: str
    label: str
    variant: str


# Estado del álbum derivado de sus páginas (HU-26, CA-26.1).
ALBUM_STATUSES = {
    "draft": StatusChip("draft", "Borrador", "neutral"),
    "in_progress": StatusChip("in_progress", "En progreso", "progress"),
    "in_review": StatusChip("in_review", "En revisión", "warning"),
    "completed": StatusChip("completed", "Completado", "success"),
}

# Filtros de la biblioteca, en el orden del mockup.
LIBRARY_FILTERS = (
    ("todos", "Todos", None),
    ("en-progreso", "En progreso", "in_progress"),
    ("por-revisar", "Por revisar", "in_review"),
    ("completados", "Completados", "completed"),
    ("borradores", "Borradores", "draft"),
)

# Filtros de páginas del detalle del álbum (HU-22, CA-22.4).
PAGE_FILTERS = (
    ("todas", "Todas", None),
    ("por-revisar", "Por revisar", (ComicPage.Status.NEEDS_REVIEW,)),
    ("sin-procesar", "Sin procesar", WORK_STATUSES),
    ("listas", "Listas", (ComicPage.Status.PROCESSED, ComicPage.Status.APPROVED)),
)


def with_progress(albums):
    """Añade a un queryset de álbumes los recuentos que necesita el progreso."""
    return albums.annotate(
        page_total=Count("pages", distinct=True),
        page_work=Count(
            "pages", filter=Q(pages__status__in=WORK_STATUSES), distinct=True
        ),
        page_done=Count(
            "pages", filter=Q(pages__status__in=DONE_STATUSES), distinct=True
        ),
        region_total=Count("pages__regions", distinct=True),
        region_review=Count(
            "pages__regions",
            filter=Q(pages__regions__needs_review=True),
            distinct=True,
        ),
        region_corrected=Count(
            "pages__regions",
            filter=Q(pages__regions__is_corrected=True),
            distinct=True,
        ),
    )


def derive_status(page_total, page_work, region_review):
    """Devuelve el estado del álbum según sus páginas (HU-26, CA-26.1).

    Sin páginas, borrador; con páginas por procesar, en progreso; con
    regiones por revisar, en revisión; y si todo está procesado y revisado,
    completado. La aprobación explícita de HU-19 afinará este último paso.
    """
    if not page_total:
        return ALBUM_STATUSES["draft"]
    if page_work:
        return ALBUM_STATUSES["in_progress"]
    if region_review:
        return ALBUM_STATUSES["in_review"]
    return ALBUM_STATUSES["completed"]


def percent(part, whole):
    """Porcentaje entero de part sobre whole, 0 si whole es 0."""
    return round(part / whole * 100) if whole else 0


@dataclass(frozen=True)
class AlbumProgress:
    """Progreso de un álbum anotado con with_progress()."""

    page_total: int
    page_done: int
    page_work: int
    region_total: int
    region_review: int
    region_corrected: int

    @classmethod
    def of(cls, album):
        """Construye el progreso a partir de las anotaciones del álbum."""
        return cls(
            album.page_total,
            album.page_done,
            album.page_work,
            album.region_total,
            album.region_review,
            album.region_corrected,
        )

    @property
    def region_ready(self):
        """Regiones que no necesitan revisión."""
        return self.region_total - self.region_review

    @property
    def percent_ready(self):
        """Porcentaje de regiones listas."""
        return percent(self.region_ready, self.region_total)

    @property
    def percent_review(self):
        """Porcentaje de regiones por revisar."""
        return percent(self.region_review, self.region_total)

    @property
    def status(self):
        """Estado derivado del álbum (HU-26)."""
        return derive_status(self.page_total, self.page_work, self.region_review)


def library_for(user):
    """Álbumes del usuario con su progreso, más recientes primero."""
    return with_progress(
        Album.objects.filter(owner=user).select_related(
            "source_language", "target_language"
        )
    ).order_by("-updated_at")


# Color de la barra de cada página en la rejilla, como en el mockup. El chip
# usa las etiquetas y variantes del propio modelo (ComicPage).
PAGE_BARS = {
    ComicPage.Status.PROCESSING: "brand",
    ComicPage.Status.PROCESSED: "success",
    ComicPage.Status.NEEDS_REVIEW: "warning",
    ComicPage.Status.APPROVED: "success",
    ComicPage.Status.FAILED: "danger",
}


def pages_with_progress(album):
    """Páginas del álbum con el recuento de regiones listas y por revisar."""
    return album.pages.annotate(
        region_total=Count("regions"),
        region_review=Count("regions", filter=Q(regions__needs_review=True)),
    ).order_by("page_number")


def page_card(page):
    """Datos de la miniatura de una página: color y porcentaje de la barra.

    El porcentaje es el de regiones que no necesitan revisión; una página
    sin procesar se queda en 0 y una procesada sin texto, en 100.
    """
    ready = page.region_total - page.region_review
    if page.region_total:
        value = percent(ready, page.region_total)
    else:
        value = 100 if page.status in DONE_STATUSES else 0
    return {
        "page": page,
        "bar": PAGE_BARS.get(page.status, "muted"),
        "percent": value,
    }


def time_greeting(now=None):
    """Saludo según la hora local: buenos días, buenas tardes o noches."""
    hour = timezone.localtime(now).hour
    if 5 <= hour < 12:
        return "Buenos días"
    if 12 <= hour < 19:
        return "Buenas tardes"
    return "Buenas noches"


def processed_since(user, since):
    """Páginas del usuario cuya detección terminó desde la fecha indicada."""
    return ComicPage.objects.filter(
        album__owner=user, status__in=DONE_STATUSES, updated_at__gte=since
    ).count()


def library_stats(user, progress_list):
    """Las cuatro tarjetas de estadísticas de la biblioteca."""
    now = timezone.now()
    this_week = processed_since(user, now - timedelta(days=7))
    last_week = processed_since(user, now - timedelta(days=14)) - this_week
    active = sum(1 for item in progress_list if item.status.key == "in_progress")
    in_review = sum(item.region_review for item in progress_list)
    recent = TextRegion.objects.filter(
        page__album__owner=user, confidence__isnull=False
    ).order_by("-created_at")[:500]
    average = TextRegion.objects.filter(pk__in=recent).aggregate(
        value=Avg("confidence")
    )["value"]
    delta = this_week - last_week
    return [
        {
            "label": "Álbumes en progreso",
            "value": active,
            "hint": f"de {len(progress_list)}",
            "tone": "ink",
        },
        {
            "label": "Páginas procesadas esta semana",
            "value": this_week,
            "hint": f"{delta:+d} frente a la anterior",
            "tone": "ink",
        },
        {
            "label": "Regiones por revisar",
            "value": in_review,
            "hint": "en todos los álbumes",
            "tone": "warning",
        },
        {
            "label": "Confianza media del OCR",
            "value": f"{round(average * 100)} %" if average is not None else "—",
            "hint": "últimas 500 regiones",
            "tone": "brand",
        },
    ]


def resume_page(user):
    """Página por la que seguir: la última tocada que aún tiene trabajo.

    Si no queda trabajo pendiente en ninguna, la última procesada.
    """
    pages = ComicPage.objects.filter(album__owner=user).select_related(
        "album__source_language", "album__target_language"
    )
    return (
        pages.filter(
            status__in=(ComicPage.Status.NEEDS_REVIEW, ComicPage.Status.FAILED)
        )
        .order_by("-updated_at")
        .first()
        or pages.filter(status=ComicPage.Status.PENDING).order_by("-updated_at").first()
        or pages.order_by("-updated_at").first()
    )


def monthly_quota(user):
    """Páginas procesadas este mes frente a la cuota mensual del OCR."""
    now = timezone.localtime()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (start + timedelta(days=32)).replace(day=1)
    used = processed_since(user, start)
    quota = settings.OCR_MONTHLY_PAGE_QUOTA
    return {
        "used": used,
        "quota": quota,
        "percent": min(percent(used, quota), 100),
        "resets": next_month,
    }


def review_total(user):
    """Regiones del usuario que necesitan revisión."""
    return TextRegion.objects.filter(page__album__owner=user, needs_review=True).count()
