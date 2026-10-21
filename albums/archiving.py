"""Archivar y desarchivar álbumes (HU-69).

Archivar no borra nada ni cambia el estado derivado del álbum (HU-26): solo
lo aparta de la biblioteca, de los filtros, de la búsqueda y de los
resúmenes. Por eso se guarda en un campo propio, archived_at.

Se usa update() y no save() para no tocar updated_at: archivar no es editar
el álbum, y no debe cambiar su posición en la biblioteca (CA-21.5).
"""

from django.utils import timezone

from albums.models import Album


def archive_album(album):
    """Archiva el álbum (CA-69.1)."""
    album.archived_at = timezone.now()
    Album.objects.filter(pk=album.pk).update(archived_at=album.archived_at)


def unarchive_album(album):
    """Devuelve el álbum a la biblioteca (CA-69.3)."""
    album.archived_at = None
    Album.objects.filter(pk=album.pk).update(archived_at=None)
