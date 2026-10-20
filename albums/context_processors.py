"""Datos de la barra lateral, disponibles en todas las plantillas."""

from django.utils.functional import SimpleLazyObject

from albums.insights import monthly_quota, resume_page, review_total
from albums.models import Album


def sidebar_summary(user):
    """Destino del espacio de trabajo, regiones por revisar, cuota del mes y
    si hay álbumes (sin ellos no se muestra el buscador)."""
    page = resume_page(user)
    return {
        "has_albums": Album.objects.filter(owner=user).exists(),
        "workspace_url": page.get_absolute_url() if page else "",
        "review_total": review_total(user),
        "quota": monthly_quota(user),
    }


def sidebar(request):
    """Expone el resumen de la barra lateral solo con sesión iniciada.

    Es perezoso: las consultas se hacen solo si la plantilla lo usa, así que
    las respuestas que no pintan la barra lateral no las pagan.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    return {"sidebar": SimpleLazyObject(lambda: sidebar_summary(user))}
