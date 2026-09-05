"""Vistas de la app albums."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.access import PrivateViewMixin
from albums.forms import AlbumForm, AlbumRenameForm
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


class AlbumRenameView(PrivateViewMixin, UpdateView):
    """Renombrado rápido de un álbum desde la biblioteca (HU-06).

    Se ofrece como modal ligero sobre la biblioteca. Esta página propia es la
    degradación para cuando el JavaScript no está disponible, y el destino
    donde aterrizan los errores de validación.
    """

    model = Album
    form_class = AlbumRenameForm
    template_name = "albums/album_rename.html"
    success_url = reverse_lazy("albums:list")

    def get_queryset(self):
        """Restringe el renombrado a los álbumes de quien hace la petición.

        Al filtrar aquí, un álbum ajeno no se encuentra y la vista responde
        404, no 403: un 403 confirmaría que ese álbum existe.
        """
        return Album.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        """Marca el destino activo de la navegación lateral."""
        context = super().get_context_data(**kwargs)
        context["nav_current"] = "albums"
        return context

    def form_valid(self, form):
        """Guarda el nuevo título y confirma el cambio."""
        response = super().form_valid(form)
        messages.success(
            self.request, f"El álbum ahora se llama «{self.object.title}»."
        )
        return response


class OwnedAlbumMixin(PrivateViewMixin):
    """Restringe una vista a los álbumes de quien hace la petición.

    Al filtrar el queryset por propietario, un álbum ajeno sencillamente no se
    encuentra y la vista responde 404, no 403: un 403 confirmaría que ese
    álbum existe y a quién pertenece.
    """

    model = Album

    def get_queryset(self):
        """Devuelve solo los álbumes del usuario autenticado."""
        return Album.objects.filter(owner=self.request.user).select_related(
            "source_language", "target_language"
        )

    def get_context_data(self, **kwargs):
        """Marca el destino activo de la navegación lateral."""
        context = super().get_context_data(**kwargs)
        context["nav_current"] = "albums"
        return context


class AlbumDetailView(OwnedAlbumMixin, DetailView):
    """Detalle de un álbum (HU-08).

    Del mockup quedan fuera el panel de progreso de traducción, los estados de
    página, los filtros de página y los botones de workspace y exportación:
    todos dependen de funcionalidad que no entra en el Sprint 1. El área de
    páginas muestra su estado vacío hasta que HU-09 permita cargarlas.
    """

    template_name = "albums/album_detail.html"


class AlbumUpdateView(OwnedAlbumMixin, UpdateView):
    """Edición de la información de un álbum (HU-08).

    Reutiliza AlbumForm, así que los campos editables son los que definieron
    HU-06 y HU-07: título, idioma de origen e idioma de destino. El estado
    queda fuera a propósito; el motivo está en el cuerpo del pull request.

    Cancelar es un enlace de vuelta al detalle, no un envío: al no haber POST
    no se escribe nada, ni siquiera updated_at.
    """

    form_class = AlbumForm
    template_name = "albums/album_edit.html"

    def get_success_url(self):
        """Vuelve al detalle del álbum recién actualizado."""
        return self.object.get_absolute_url()

    def form_valid(self, form):
        """Guarda los cambios y confirma con un mensaje."""
        response = super().form_valid(form)
        messages.success(self.request, "Álbum actualizado correctamente.")
        return response
