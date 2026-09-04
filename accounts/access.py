"""Control de acceso a las vistas privadas de PaneLingo.

Toda vista que muestre datos de un usuario debe usar uno de los dos ayudantes
de este módulo, según sea una función o una clase. Ambos combinan las dos
protecciones que necesita una vista privada:

- Exigir sesión iniciada, redirigiendo al inicio de sesión si no la hay.
- Impedir que el navegador guarde la respuesta en caché, para que al pulsar
  "atrás" después de cerrar sesión no se reexponga contenido privado.

Se agrupan aquí a propósito. Aplicadas por separado en cada vista, olvidar la
segunda no rompe ninguna prueba: el contenido sigue mostrándose bien y el
fallo solo aparece en el navegador de un usuario real que ya cerró sesión.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


def private_view(view_func):
    """Marca una vista basada en función como privada.

    Exige sesión iniciada e impide el almacenamiento en caché de la respuesta.
    """
    return never_cache(login_required(view_func))


class PrivateViewMixin(LoginRequiredMixin):
    """Marca una vista basada en clase como privada.

    Equivale a private_view para vistas basadas en clase. Debe declararse
    primero en la lista de bases para que su dispatch envuelva al de la vista.
    """

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """Comprueba la sesión y marca la respuesta como no almacenable."""
        return super().dispatch(request, *args, **kwargs)
