"""Enrutamiento raíz del proyecto PaneLingo.

Las rutas de negocio se incorporan a medida que avanzan las historias de
usuario. La raíz es la biblioteca de álbumes.
"""

from django.contrib import admin
from django.urls import include, path

from config import views

urlpatterns = [
    path("", include("albums.urls")),
    path("cuentas/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    # Página de referencia del sistema de diseño. Solo responde con DEBUG=True.
    path("design-system/", views.design_system, name="design_system"),
]

# MEDIA_URL no se sirve ni siquiera en desarrollo: las imágenes de los usuarios
# solo se entregan por las vistas protegidas de albums (HU-11, deuda DT-02).
