"""Rutas de la app albums."""

from django.urls import path

from albums.views import AlbumCreateView, AlbumListView, AlbumRenameView

app_name = "albums"

urlpatterns = [
    path("", AlbumListView.as_view(), name="list"),
    path("albumes/nuevo/", AlbumCreateView.as_view(), name="create"),
    path(
        "albumes/<int:pk>/renombrar/",
        AlbumRenameView.as_view(),
        name="rename",
    ),
]
