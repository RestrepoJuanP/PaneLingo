"""Enrutamiento raíz del proyecto PaneLingo.

Las rutas de negocio se incorporan a medida que avanzan las historias de
usuario. La ruta raíz es una vista puente temporal hasta que exista la
biblioteca de álbumes.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config import views

urlpatterns = [
    path("", views.home, name="home"),
    path("cuentas/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    # Página de referencia del sistema de diseño. Solo responde con DEBUG=True.
    path("design-system/", views.design_system, name="design_system"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
