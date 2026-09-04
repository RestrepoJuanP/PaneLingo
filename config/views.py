"""Vistas del proyecto que no pertenecen a ninguna app de negocio."""

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

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


def design_system(request):
    """Página de referencia del sistema de diseño, solo para desarrollo.

    Muestra todos los componentes y sus estados juntos, para poder compararlos
    con las capturas de design/screenshots/. Responde 404 cuando DEBUG es
    False, para que nunca quede expuesta en producción.
    """
    if not settings.DEBUG:
        raise Http404("La página de sistema de diseño solo existe en desarrollo.")
    return render(request, "design_system.html", {"colors": DESIGN_SYSTEM_COLORS})
