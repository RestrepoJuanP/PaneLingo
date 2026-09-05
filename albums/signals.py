"""Señales de la app albums: limpieza de archivos al borrar páginas (HU-10)."""

import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from albums.models import ComicPage

logger = logging.getLogger(__name__)


def delete_stored_file(field):
    """Borra del almacenamiento el archivo de un campo, si lo hay.

    Es deliberadamente tolerante a fallos. Esta función corre dentro de la
    transacción del borrado, así que dejar escapar una excepción revertiría la
    eliminación del registro: quedarían la fila Y el archivo, y el usuario
    vería que la página que acaba de eliminar sigue ahí.

    De los dos desenlaces posibles, un archivo huérfano sin registro es
    recuperable —se puede localizar y limpiar más tarde— y un borrado que
    falla a medias no. Así que el error se registra y se sigue.
    """
    if not field or not field.name:
        return
    try:
        field.storage.delete(field.name)
    except OSError:
        logger.warning(
            "No se pudo borrar del disco el archivo %s. El registro sí se "
            "eliminó; el archivo queda huérfano y habrá que limpiarlo.",
            field.name,
            exc_info=True,
        )


@receiver(post_delete, sender=ComicPage)
def delete_page_files(sender, instance, **kwargs):
    """Borra la imagen y la miniatura de una página eliminada.

    Se usa una señal post_delete y NO se sobrescribe ComicPage.delete(), y la
    diferencia importa: al eliminar un álbum, el recolector de Django borra
    sus páginas en bloque sin llamar al método delete() de cada instancia, de
    modo que los archivos quedarían huérfanos. Las señales post_delete sí se
    disparan en cascada.

    Registrar este receptor desactiva además la optimización de borrado rápido
    de Django para ComicPage, que es precisamente la que se saltaría la señal.

    Quedan cubiertos los cuatro caminos: borrar una página, borrar por
    queryset, borrar el álbum y borrar la cuenta de usuario.
    """
    delete_stored_file(instance.image)
    delete_stored_file(instance.thumbnail)
