"""Rutas de la app albums."""

from django.urls import path

from albums.views import (
    AlbumCreateView,
    AlbumDetailView,
    AlbumListView,
    AlbumRenameView,
    AlbumUpdateView,
)

app_name = "albums"

urlpatterns = [
    path("", AlbumListView.as_view(), name="list"),
    path("albumes/nuevo/", AlbumCreateView.as_view(), name="create"),
    path("albumes/<int:pk>/", AlbumDetailView.as_view(), name="detail"),
    path("albumes/<int:pk>/editar/", AlbumUpdateView.as_view(), name="edit"),
    path(
        "albumes/<int:pk>/renombrar/",
        AlbumRenameView.as_view(),
        name="rename",
    ),
]
