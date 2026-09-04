"""Enrutamiento raíz del proyecto PaneLingo.

Las rutas de negocio se incorporan en etapas posteriores; por ahora solo se
expone el panel de administración de Django.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from config import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Página de referencia del sistema de diseño. Solo responde con DEBUG=True.
    path("design-system/", views.design_system, name="design_system"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
