"""Vistas del proyecto que no pertenecen a ninguna app de negocio."""

import functools

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from accounts.access import private_view


def debug_only(view_func):
    """Hace que una vista solo exista cuando DEBUG está activado.

    Se aplica por fuera de private_view a propósito. Si se aplicara por
    dentro, en producción un visitante anónimo recibiría una redirección al
    inicio de sesión en lugar de un 404, y esa diferencia ya revela que la
    ruta existe. Con este orden, fuera de desarrollo la página sencillamente
    no existe para nadie.
    """

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404("Esta página solo existe en desarrollo.")
        return view_func(request, *args, **kwargs)

    return wrapper


# Muestrario de color de la página de referencia. Los valores replican los de
# static/css/tokens.css; se listan aquí solo para poder rotularlos.
DESIGN_SYSTEM_COLORS = [
    ("--brand", "#4c3fd9"),
    ("--brand-hover", "#3f34bb"),
    ("--brand-tint", "#eef0ff"),
    ("--accent", "#f2765a"),
    ("--surface-navy", "#1b1836"),
    ("--ink-900", "#191821"),
    ("--ink-600", "#4a463d"),
    ("--muted", "#6f6a60"),
    ("--bg", "#f7f6f3"),
    ("--surface", "#ffffff"),
    ("--surface-muted", "#f2f0ea"),
    ("--border", "#e7e3db"),
    ("--success", "#2f7d4f"),
    ("--warning", "#f2b23a"),
    ("--danger", "#b13c22"),
    ("--track", "#eeebe3"),
]


@debug_only
@private_view
def design_system(request):
    """Página de referencia del sistema de diseño, solo para desarrollo.

    Muestra todos los componentes y sus estados juntos, para poder compararlos
    con las capturas de design/screenshots/. Responde 404 cuando DEBUG es
    False, para que nunca quede expuesta en producción.

    Exige sesión iniciada además de la comprobación de DEBUG. No contiene
    datos de ningún usuario, pero el fallo realista no es que alguien la
    encuentre en desarrollo, sino desplegar con DEBUG activado por descuido.
    """
    return render(request, "design_system.html", {"colors": DESIGN_SYSTEM_COLORS})
