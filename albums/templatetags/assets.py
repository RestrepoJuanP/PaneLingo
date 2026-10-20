"""Enlaces a los archivos estáticos propios con su versión en la dirección.

Sin versión, el navegador reutiliza de su caché el CSS y el JavaScript
anteriores a un cambio: el servidor de desarrollo no envía Cache-Control y el
navegador estima por su cuenta cuánto tiempo puede reutilizarlos. Añadir la
fecha de modificación del archivo cambia la dirección en cuanto cambia el
archivo, y el navegador pide la versión nueva.
"""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def versioned_static(path):
    """Devuelve la dirección estática de path con ?v=<fecha de modificación>.

    Si el archivo no se encuentra, devuelve la dirección sin versión: un
    enlace sin versión es preferible a romper la página.
    """
    url = static(path)
    absolute_path = finders.find(path)
    if not absolute_path:
        return url
    return f"{url}?v={int(os.path.getmtime(absolute_path))}"
