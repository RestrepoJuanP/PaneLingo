"""Rutas de la app albums."""

from django.urls import path

from albums.views import (
    AlbumCoverView,
    AlbumCreateView,
    AlbumDetailView,
    AlbumListView,
    AlbumRenameView,
    AlbumUpdateView,
    PageDeleteView,
    PageDetailView,
    PageImageView,
    PageProcessView,
    PageStatusView,
    PageUploadView,
    UploadChooseView,
)

app_name = "albums"

urlpatterns = [
    path("", AlbumListView.as_view(), name="list"),
    path("albumes/nuevo/", AlbumCreateView.as_view(), name="create"),
    path("albumes/cargar/", UploadChooseView.as_view(), name="upload_choose"),
    path("albumes/<int:pk>/", AlbumDetailView.as_view(), name="detail"),
    path("albumes/<int:pk>/cargar/", PageUploadView.as_view(), name="upload"),
    path("paginas/<int:pk>/", PageDetailView.as_view(), name="page_detail"),
    path(
        "paginas/<int:pk>/procesar/",
        PageProcessView.as_view(),
        name="page_process",
    ),
    path(
        "paginas/<int:pk>/imagen/",
        PageImageView.as_view(variant="image"),
        name="page_image",
    ),
    path(
        "paginas/<int:pk>/miniatura/",
        PageImageView.as_view(variant="thumbnail"),
        name="page_thumbnail",
    ),
    path(
        "albumes/<int:pk>/portada/",
        AlbumCoverView.as_view(),
        name="album_cover",
    ),
    path(
        "paginas/<int:pk>/estado/",
        PageStatusView.as_view(),
        name="page_status",
    ),
    path(
        "paginas/<int:pk>/eliminar/",
        PageDeleteView.as_view(),
        name="page_delete",
    ),
    path("albumes/<int:pk>/editar/", AlbumUpdateView.as_view(), name="edit"),
    path(
        "albumes/<int:pk>/renombrar/",
        AlbumRenameView.as_view(),
        name="rename",
    ),
]
