"""Vistas de la app albums."""

import unicodedata

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.access import PrivateViewMixin, private_view
from albums.corrections import correct_region, restore_region
from albums.forms import AlbumForm, AlbumRenameForm
from albums.insights import (
    LIBRARY_FILTERS,
    PAGE_FILTERS,
    AlbumProgress,
    library_for,
    library_stats,
    page_card,
    pages_with_progress,
    percent,
    resume_page,
    time_greeting,
    with_progress,
)
from albums.models import Album, ComicPage, TextRegion
from albums.processing import expire_if_stale, start_processing
from albums.services import create_pages_from_upload
from albums.translating import (
    can_translate,
    expire_translation_if_stale,
    start_translation,
)

# Longitud máxima del texto de búsqueda; el título admite 120 caracteres.
SEARCH_MAX_LENGTH = 120


def normalize_search_text(text):
    """Pasa a minúsculas y quita las tildes, para comparar sin distinguirlas."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


class AlbumListView(PrivateViewMixin, ListView):
    """Biblioteca de álbumes del usuario autenticado (HU-05, HU-26, HU-50).

    Como en el mockup: saludo, estadísticas, banda para seguir trabajando,
    filtros por estado y tarjetas con su progreso. El estado de cada álbum se
    deriva de sus páginas (HU-26), y el filtro (?estado=) se combina con la
    búsqueda por título (?q=, HU-50).
    """

    model = Album
    template_name = "albums/album_list.html"
    context_object_name = "albums"

    def get_queryset(self):
        """Devuelve solo los álbumes de quien hace la petición, con su progreso.

        El filtrado por propietario ocurre aquí, en el servidor. Es la única
        barrera que impide ver la biblioteca de otra cuenta.
        """
        albums = library_for(self.request.user)
        search_text = self.get_search_text()
        if not search_text:
            return albums
        # Se compara en Python, no en SQL: icontains de SQLite no ignora las
        # tildes. El conjunto es el de un solo usuario, así que es pequeño.
        needle = normalize_search_text(search_text)
        matching_ids = [
            album.pk for album in albums if needle in normalize_search_text(album.title)
        ]
        return albums.filter(pk__in=matching_ids)

    def get_search_text(self):
        """Devuelve el texto buscado (parámetro q), recortado y acotado."""
        return self.request.GET.get("q", "").strip()[:SEARCH_MAX_LENGTH]

    def get_status_filter(self):
        """Devuelve el filtro de estado elegido (parámetro estado)."""
        chosen = self.request.GET.get("estado", "")
        valid = {slug for slug, _label, _status in LIBRARY_FILTERS}
        return chosen if chosen in valid else "todos"

    def is_live_request(self):
        """Indica si la petición viene de la búsqueda automática."""
        return self.request.headers.get("X-Live-Search") == "1"

    def get_template_names(self):
        """Devuelve solo el bloque de resultados a la búsqueda automática.

        El script de la biblioteca marca sus peticiones con la cabecera
        X-Live-Search. Responderle con el bloque, y no con la página entera,
        acorta la descarga y el procesado de cada pulsación. El filtrado y el
        aislamiento por propietario son exactamente los mismos.
        """
        if self.is_live_request():
            return ["albums/_album_results.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        """Añade progreso, filtros y, en la página completa, el resumen."""
        context = super().get_context_data(**kwargs)
        albums = list(context["albums"])
        for album in albums:
            album.progress = AlbumProgress.of(album)

        chosen = self.get_status_filter()
        status_by_slug = {slug: status for slug, _label, status in LIBRARY_FILTERS}
        wanted = status_by_slug[chosen]
        context["albums"] = [
            album
            for album in albums
            if wanted is None or album.progress.status.key == wanted
        ]
        context["status_filters"] = [
            {
                "slug": slug,
                "label": label,
                "count": sum(
                    1
                    for album in albums
                    if status is None or album.progress.status.key == status
                ),
                "active": slug == chosen,
            }
            for slug, label, status in LIBRARY_FILTERS
        ]
        context["status_filter"] = chosen
        context["search_text"] = self.get_search_text()
        context["live_search"] = True
        context["total_album_count"] = Album.objects.filter(
            owner=self.request.user
        ).count()
        if not self.is_live_request():
            context.update(self.get_summary(albums))
        context["form"] = kwargs.get("form") or AlbumForm()
        context["nav_current"] = "albums"
        return context

    def get_summary(self, albums):
        """Saludo, estadísticas y página por la que seguir (cabecera)."""
        user = self.request.user
        progress = [album.progress for album in albums]
        resume = resume_page(user)
        return {
            "greeting": time_greeting(),
            "stats": library_stats(user, progress),
            "resume": resume,
            "resume_review": (
                resume.regions.filter(needs_review=True).count() if resume else 0
            ),
            "review_regions": sum(item.region_review for item in progress),
            "active_albums": sum(
                1 for item in progress if item.status.key != "completed"
            ),
        }


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


class PageUploadView(OwnedAlbumMixin, DetailView):
    """Carga de páginas de un álbum propio (HU-09).

    Del mockup queda fuera todo el panel de ajustes de escaneo, el orden de
    lectura y el botón de traducir: pertenecen al OCR y a la traducción. Aquí
    solo se cargan archivos y se informa del resultado de cada uno.

    Hereda de OwnedAlbumMixin, así que cargar en un álbum ajeno responde 404:
    la comprobación ocurre en el servidor y no depende de que la interfaz
    oculte el enlace.
    """

    template_name = "albums/page_upload.html"

    def post(self, request, *args, **kwargs):
        """Procesa el lote y vuelve a mostrar la pantalla con el resultado."""
        self.object = self.get_object()
        uploaded_files = request.FILES.getlist("pages")

        if not uploaded_files:
            messages.error(request, "No seleccionaste ningún archivo.")
            return redirect(self.object.get_upload_url())

        created, rejected = create_pages_from_upload(self.object, uploaded_files)

        if created:
            if len(created) == 1:
                messages.success(request, "Se cargó 1 página.")
            else:
                messages.success(request, f"Se cargaron {len(created)} páginas.")
        for rejection in rejected:
            messages.error(request, f"«{rejection.filename}»: {rejection.reason}")

        context = self.get_context_data(object=self.object)
        context["created_pages"] = created
        context["rejected_uploads"] = rejected
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        """Añade los límites de carga para poder mostrarlos en la pantalla."""
        context = super().get_context_data(**kwargs)
        context["max_file_size_mb"] = settings.MAX_FILE_SIZE // 1_000_000
        context["allowed_extensions"] = ", ".join(
            extension.lstrip(".").upper()
            for extension in settings.ALLOWED_IMAGE_EXTENSIONS
        )
        # Los límites viajan también en crudo, para emitirlos como atributos
        # de datos en el input. El aviso temprano del navegador los lee de
        # ahí en lugar de llevarlos escritos, de modo que settings sigue
        # siendo la única fuente y cliente y servidor no pueden divergir.
        context["max_file_size_bytes"] = settings.MAX_FILE_SIZE
        context["allowed_extensions_raw"] = ",".join(settings.ALLOWED_IMAGE_EXTENSIONS)
        context["nav_current"] = "upload"
        return context


class UploadChooseView(PrivateViewMixin, TemplateView):
    """Elección del álbum al que cargar páginas (HU-09).

    Es el destino de "Cargar páginas" de la navegación, que no puede saber a
    qué álbum se refiere. Se descartó adivinarlo —el único que existe, o el
    último editado— porque acertaría a veces y el resto serían cargas en el
    álbum equivocado, caras de deshacer mientras no exista eliminar páginas.
    """

    template_name = "albums/upload_choose.html"

    def get_context_data(self, **kwargs):
        """Lista los álbumes del usuario para escoger destino."""
        context = super().get_context_data(**kwargs)
        context["albums"] = Album.objects.filter(
            owner=self.request.user
        ).select_related("source_language", "target_language")
        context["nav_current"] = "upload"
        return context


class AlbumDetailView(OwnedAlbumMixin, DetailView):
    """Detalle de un álbum (HU-08, HU-22, HU-26).

    Como en el mockup: estado derivado, acciones con "Abrir espacio de
    trabajo" (HU-11) como principal, tarjeta de progreso, filtros de página
    (?estado=) y miniaturas con su estado y su barra.
    """

    template_name = "albums/album_detail.html"

    # Estados de una página en la que todavía queda trabajo por hacer.
    PENDING_WORK = (
        ComicPage.Status.PENDING,
        ComicPage.Status.FAILED,
        ComicPage.Status.NEEDS_REVIEW,
    )

    def get_page_filter(self):
        """Devuelve el filtro de páginas elegido (parámetro estado)."""
        chosen = self.request.GET.get("estado", "")
        valid = {slug for slug, _label, _statuses in PAGE_FILTERS}
        return chosen if chosen in valid else "todas"

    def get_context_data(self, **kwargs):
        """Añade progreso, filtros, miniaturas y la página de trabajo.

        La página con la que abrir el espacio de trabajo es la primera con
        trabajo pendiente y, si no queda ninguna, la primera del álbum,
        igual que "Open workspace" en el mockup.
        """
        context = super().get_context_data(**kwargs)
        album = self.object
        pages = list(pages_with_progress(album))
        context["workspace_page"] = next(
            (page for page in pages if page.status in self.PENDING_WORK),
            pages[0] if pages else None,
        )
        context["progress"] = AlbumProgress.of(
            with_progress(Album.objects.filter(pk=album.pk)).get()
        )
        context["page_progress"] = self.page_progress(pages)

        chosen = self.get_page_filter()
        statuses_by_slug = {slug: statuses for slug, _l, statuses in PAGE_FILTERS}
        wanted = statuses_by_slug[chosen]
        context["page_filters"] = [
            {
                "slug": slug,
                "label": label,
                "count": sum(
                    1 for page in pages if statuses is None or page.status in statuses
                ),
                "active": slug == chosen,
            }
            for slug, label, statuses in PAGE_FILTERS
        ]
        context["page_filter"] = chosen
        context["page_cards"] = [
            page_card(page) for page in pages if wanted is None or page.status in wanted
        ]
        context["page_total"] = len(pages)
        return context

    @staticmethod
    def page_progress(pages):
        """Reparto de páginas para la tarjeta de progreso del mockup."""
        total = len(pages)
        ready = sum(
            1
            for page in pages
            if page.status in (ComicPage.Status.PROCESSED, ComicPage.Status.APPROVED)
        )
        review = sum(
            1 for page in pages if page.status == ComicPage.Status.NEEDS_REVIEW
        )
        pending = total - ready - review
        return {
            "ready": ready,
            "review": review,
            "pending": pending,
            "ready_percent": percent(ready, total),
            "review_percent": percent(review, total),
            "pending_percent": percent(pending, total),
        }


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


class PageDeleteView(PrivateViewMixin, DeleteView):
    """Eliminación de una página de un álbum propio (HU-10).

    Solo el POST elimina. Un GET muestra la página de confirmación sin tocar
    nada, que es además la degradación del modal cuando no hay JavaScript.

    El queryset filtra por album__owner, de modo que una página de otra cuenta
    responde 404 tanto en la confirmación como en el POST.
    """

    model = ComicPage
    template_name = "albums/page_confirm_delete.html"
    context_object_name = "page"

    def get_queryset(self):
        """Restringe el borrado a las páginas de álbumes del usuario."""
        return ComicPage.objects.filter(album__owner=self.request.user).select_related(
            "album"
        )

    def get_context_data(self, **kwargs):
        """Marca el destino activo de la navegación lateral."""
        context = super().get_context_data(**kwargs)
        context["nav_current"] = "albums"
        return context

    def get_success_url(self):
        """Vuelve al detalle del álbum del que se eliminó la página."""
        return self.album.get_absolute_url()

    def form_valid(self, form):
        """Elimina la página y confirma con un mensaje.

        Las páginas restantes NO se renumeran: un hueco en la secuencia dice
        la verdad, que a la obra le falta esa página, y renumerar movería la
        etiqueta de las demás. El mensaje lo explica en el momento en que el
        salto podría parecer un error.
        """
        page_number = self.object.page_number
        self.album = self.object.album

        response = super().form_valid(form)

        if self.album.pages.exists():
            messages.success(
                self.request,
                f"Se eliminó la página {page_number}. "
                f"Las demás conservan su número.",
            )
        else:
            messages.success(
                self.request,
                f"Se eliminó la página {page_number}. "
                f"El álbum se quedó sin páginas.",
            )
        return response


class OwnedPageMixin(PrivateViewMixin):
    """Restringe una vista a las páginas de álbumes de quien hace la petición.

    Una página de otra cuenta no se encuentra y la vista responde 404, no 403,
    para no confirmar que existe (CA-12.6).
    """

    model = ComicPage
    context_object_name = "page"

    def get_queryset(self):
        """Devuelve solo las páginas de los álbumes del usuario autenticado."""
        return ComicPage.objects.filter(album__owner=self.request.user).select_related(
            "album__source_language", "album__target_language"
        )

    def get_object(self, queryset=None):
        """Devuelve la página, pasando a "Error" la que quedó colgada.

        Vale para el OCR y para la traducción: ninguna de las dos tareas
        puede dejar la página bloqueada si el trabajador se cae.
        """
        page = super().get_object(queryset)
        expire_if_stale(page)
        expire_translation_if_stale(page)
        return page

    def get_context_data(self, **kwargs):
        """Marca el destino activo de la navegación lateral."""
        context = super().get_context_data(**kwargs)
        context["nav_current"] = "albums"
        return context


# Valor de ?filtro= que deja solo las regiones pendientes de revisar (HU-14).
REVIEW_FILTER = "revisar"


class PageDetailView(OwnedPageMixin, DetailView):
    """Espacio de trabajo de una página (HU-11, HU-12, HU-13 y HU-14).

    Muestra la página a tamaño completo con sus datos y la navegación a la
    anterior y a la siguiente (HU-11), sus regiones resaltadas (HU-12) y el
    texto reconocido de cada una (HU-13). Por decisión del 2026-10-20, la
    página seleccionada es directamente el espacio de trabajo: no hay un
    visor aparte.
    """

    template_name = "albums/page_detail.html"

    def get_context_data(self, **kwargs):
        """Añade las regiones, las páginas vecinas y la posición en el álbum."""
        context = super().get_context_data(**kwargs)
        page = self.object
        regions = list(page.regions.all())
        review_filter = self.request.GET.get("filtro") == REVIEW_FILTER
        context["regions"] = regions
        context["review_count"] = sum(region.needs_review for region in regions)
        context["corrected_count"] = sum(region.is_corrected for region in regions)
        ready_count = len(regions) - context["review_count"]
        context["ready_count"] = ready_count
        context["ready_percent"] = (
            round(ready_count / len(regions) * 100) if regions else 0
        )
        context["review_filter"] = review_filter
        context["visible_regions"] = (
            [region for region in regions if region.needs_review]
            if review_filter
            else regions
        )
        context.update(page_neighbours(page))
        context.update(translation_summary(page, regions))
        return context


def translation_summary(page, regions):
    """Datos de la traducción para el espacio de trabajo (HU-16)."""
    pending = [region for region in regions if region.needs_translation]
    translated = [
        region
        for region in pending
        if region.translation_status != TextRegion.TranslationStatus.UNTRANSLATED
    ]
    return {
        "can_translate": can_translate(page),
        "translatable_count": len(pending),
        "translated_count": len(translated),
        "has_translations": bool(translated),
    }


def page_neighbours(page):
    """Devuelve la página anterior, la siguiente y la posición en el álbum.

    Se ordena por número de página y no por posición en una lista: tras
    eliminar páginas hay huecos en la numeración (HU-10) y "anterior" debe
    saltarlos.
    """
    siblings = page.album.pages.order_by("page_number")
    number = page.page_number
    return {
        "previous_page": siblings.filter(page_number__lt=number).last(),
        "next_page": siblings.filter(page_number__gt=number).first(),
        "page_position": siblings.filter(page_number__lte=number).count(),
        "album_page_count": siblings.count(),
    }


class PageStatusView(OwnedPageMixin, DetailView):
    """Estado de procesamiento de una página, en JSON (HU-12).

    Lo consulta la vista de la página mientras está "Procesando", para
    recargarse sola en cuanto termina la detección. Hereda el filtro por
    propietario: una página ajena responde 404, igual que su vista.
    """

    def render_to_response(self, context, **response_kwargs):
        """Devuelve el estado como JSON en lugar de una plantilla."""
        page = self.object
        return JsonResponse(
            {
                "status": page.status,
                "is_processing": page.is_processing,
                "is_translating": page.is_translating,
                "region_count": page.regions.count(),
            }
        )


def processing_feedback(page):
    """Devuelve el nivel y el texto del mensaje tras pedir el procesamiento.

    Con el trabajador en marcha la página sigue "Procesando" al volver de la
    petición. En modo inmediato ya llega procesada o con error, y el mensaje
    tiene que decir lo que de verdad pasó.
    """
    if page.status == ComicPage.Status.PROCESSING:
        return messages.SUCCESS, (
            f"Procesando la página {page.page_number}. "
            "Puedes seguir usando PaneLingo mientras tanto."
        )
    if page.has_failed:
        return messages.ERROR, page.processing_error
    count = page.regions.count()
    if not count:
        return messages.SUCCESS, (
            f"Página {page.page_number} procesada. "
            "No se detectó texto en esta página."
        )
    noun = "región" if count == 1 else "regiones"
    return messages.SUCCESS, (
        f"Página {page.page_number} procesada: {count} {noun} de texto."
    )


class PageProcessView(OwnedPageMixin, DetailView):
    """Procesar una página para detectar sus regiones de texto (HU-12).

    Solo el POST procesa. Un GET muestra la confirmación de volver a
    procesar, que es además la degradación del modal sin JavaScript.

    Si la página ya tiene regiones, el POST exige confirm=1: reprocesar las
    reemplaza (CA-12.5), y la confirmación no puede depender solo de que la
    interfaz muestre el modal.
    """

    template_name = "albums/page_confirm_process.html"

    def post(self, request, *args, **kwargs):
        """Encola la detección y vuelve a la vista de la página."""
        page = self.get_object()
        if page.regions.exists() and request.POST.get("confirm") != "1":
            return redirect(page.get_process_url())

        if not start_processing(page):
            messages.info(request, "Esta página ya se está procesando.")
            return redirect(page.get_absolute_url())

        page.refresh_from_db()
        level, text = processing_feedback(page)
        messages.add_message(request, level, text)
        return redirect(page.get_absolute_url())


def stored_file_response(field):
    """Entrega un archivo guardado, o 404 si no existe.

    Si el archivo falta en disco se responde 404 y no 500: para quien lo pide
    es lo mismo que una imagen que no existe.
    """
    if not field:
        raise Http404("La imagen no existe.")
    try:
        handle = field.open("rb")
    except (FileNotFoundError, OSError) as error:
        raise Http404("La imagen no existe.") from error
    return FileResponse(handle)


class PageImageView(OwnedPageMixin, DetailView):
    """Imagen original o miniatura de una página propia (HU-11, CA-11.4).

    Sustituye al servicio directo de MEDIA_URL, que entregaba la imagen a
    cualquiera que conociera su dirección (deuda DT-02). Hereda el filtro por
    propietario, así que una página ajena responde 404, y PrivateViewMixin,
    que exige sesión e impide que el navegador guarde la imagen en caché.
    """

    variant = "image"

    def render_to_response(self, context, **response_kwargs):
        """Entrega el archivo en lugar de una plantilla."""
        page = self.object
        if self.variant == "thumbnail" and page.thumbnail:
            return stored_file_response(page.thumbnail)
        return stored_file_response(page.image)


class AlbumCoverView(OwnedAlbumMixin, DetailView):
    """Portada subida de un álbum propio (HU-49), con el mismo control (DT-02)."""

    def render_to_response(self, context, **response_kwargs):
        """Entrega la portada, o 404 si el álbum usa la predeterminada."""
        return stored_file_response(self.object.cover_image)


def translation_feedback(page):
    """Nivel y texto del mensaje tras pedir la traducción (HU-16).

    Con el trabajador en marcha la página sigue "Traduciendo"; en modo
    inmediato ya llega traducida o con error.
    """
    if page.is_translating:
        return messages.SUCCESS, (
            f"Traduciendo la página {page.page_number}. "
            "Puedes seguir usando PaneLingo mientras tanto."
        )
    if page.translation_failed:
        return messages.ERROR, page.translation_error
    return messages.SUCCESS, f"Página {page.page_number} traducida."


def owned_page_or_404(request, pk):
    """Página del usuario, o 404 si no existe o es de otra cuenta."""
    page = get_object_or_404(
        ComicPage.objects.select_related(
            "album__source_language", "album__target_language"
        ),
        pk=pk,
        album__owner=request.user,
    )
    expire_if_stale(page)
    expire_translation_if_stale(page)
    return page


def queue_translation(request, page, region=None):
    """Encola la traducción y deja el mensaje para el usuario."""
    if not start_translation(page, region):
        messages.info(request, "Esta página ya se está traduciendo.")
        return
    page.refresh_from_db()
    level, text = translation_feedback(page)
    messages.add_message(request, level, text)


@require_POST
@private_view
def page_translate(request, pk):
    """Traduce con IA las regiones sin aprobar de una página (HU-16).

    Solo acepta POST: un GET responde 405. Si no hay nada que traducir, por
    ejemplo porque la página no tiene texto (CA-16.5), no encola nada.
    """
    page = owned_page_or_404(request, pk)
    if not can_translate(page):
        messages.info(request, "Esta página no tiene texto pendiente de traducir.")
    else:
        queue_translation(request, page)
    return redirect(page.get_absolute_url())


@require_POST
@private_view
def region_retranslate(request, pk):
    """Vuelve a pedir a la IA la traducción de una sola región (HU-16).

    Es el "Retry AI" del mockup: viaja la página entera como contexto, pero
    solo se reemplaza esta región. Una región aprobada no se toca (CA-16.3).
    """
    region = get_object_or_404(
        TextRegion.objects.select_related("page"),
        pk=pk,
        page__album__owner=request.user,
    )
    page = owned_page_or_404(request, region.page_id)
    anchor = f"#region-{region.reading_order}"
    if region.is_translation_approved or not region.needs_translation:
        messages.info(request, "Esta región no tiene traducción pendiente.")
    elif page.is_processing:
        messages.info(request, "Espera a que termine el procesamiento de la página.")
    else:
        queue_translation(request, page, region)
    return redirect(f"{page.get_absolute_url()}{anchor}")


@require_POST
@private_view
def region_correct(request, pk):
    """Guarda la corrección del texto de una región, o la deshace (HU-15).

    Solo acepta POST: un GET responde 405 antes incluso de pedir sesión.
    La región se busca entre las de las páginas del usuario, así que una
    región ajena responde 404 (CLAUDE.md, aislamiento por propietario).
    """
    region = get_object_or_404(
        TextRegion.objects.select_related("page__album__source_language"),
        pk=pk,
        page__album__owner=request.user,
    )
    number = region.reading_order
    if request.POST.get("restore") == "1":
        restore_region(region)
        messages.success(
            request, f"Se restauró el texto del OCR de la región {number}."
        )
    else:
        correct_region(region, request.POST.get("text", ""))
        if region.has_nothing_to_translate:
            messages.success(
                request, f"La región {number} quedó sin texto que traducir."
            )
        else:
            messages.success(request, f"Se guardó la corrección de la región {number}.")
    return redirect(f"{region.page.get_absolute_url()}#region-{number}")
