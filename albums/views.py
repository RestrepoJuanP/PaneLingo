"""Vistas de la app albums."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from accounts.access import PrivateViewMixin
from albums.forms import AlbumForm
from albums.models import Album


class AlbumListView(PrivateViewMixin, ListView):
    """Biblioteca de álbumes del usuario autenticado (HU-05).

    Los filtros por estado del mockup no se implementan todavía: en el Sprint
    1 todos los álbumes están en borrador, porque ninguna historia cambia el
    estado, y cuatro de los cinco filtros devolverían siempre lista vacía.
    """

    model = Album
    template_name = "albums/album_list.html"
    context_object_name = "albums"

    def get_queryset(self):
        """Devuelve solo los álbumes de quien hace la petición.

        El filtrado por propietario ocurre aquí, en el servidor. Es la única
        barrera que impide ver la biblioteca de otra cuenta.
        """
        return (
            Album.objects.filter(owner=self.request.user)
            .select_related("source_language", "target_language")
            .order_by("-updated_at")
        )

    def get_context_data(self, **kwargs):
        """Añade el formulario de creación para el modal de la biblioteca."""
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or AlbumForm()
        context["nav_current"] = "albums"
        return context


class AlbumCreateView(PrivateViewMixin, CreateView):
    """Creación de un álbum (HU-05).

    Se ofrece como modal sobre la biblioteca. Esta página propia es la
    degradación para cuando el JavaScript no está disponible, y también el
    destino donde aterrizan los errores de validación.
    """

    model = Album
    form_class = AlbumForm
    template_name = "albums/album_form.html"
    success_url = reverse_lazy("albums:list")

    def get_context_data(self, **kwargs):
        """Marca el destino activo de la navegación lateral."""
        context = super().get_context_data(**kwargs)
        context["nav_current"] = "albums"
        return context

    def form_valid(self, form):
        """Asigna el propietario en el servidor y confirma la creación.

        El propietario sale de request.user, nunca de los datos enviados: así
        un POST con un campo owner manipulado no puede crear un álbum a nombre
        de otra cuenta.
        """
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, f"Álbum «{self.object.title}» creado correctamente."
        )
        return response
