"""Configuración de la app albums."""

from django.apps import AppConfig


class AlbumsConfig(AppConfig):
    """App de álbumes y páginas de cómic."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "albums"

    def ready(self):
        """Conecta las señales de la app.

        El import tiene efecto por sí mismo: registra el receptor que borra
        los archivos de una página eliminada.
        """
        from albums import signals  # noqa: F401
