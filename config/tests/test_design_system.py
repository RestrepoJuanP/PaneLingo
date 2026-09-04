"""Pruebas de la página de referencia del sistema de diseño."""

from django.test import TestCase, override_settings
from django.urls import reverse


class DesignSystemViewTests(TestCase):
    """La página de estilos solo debe existir en desarrollo."""

    @override_settings(DEBUG=True)
    def test_available_when_debug_is_enabled(self):
        """Humo — La referencia de estilos responde con DEBUG activo."""
        response = self.client.get(reverse("design_system"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "design_system.html")

    @override_settings(DEBUG=False)
    def test_hidden_when_debug_is_disabled(self):
        """Humo — La referencia de estilos no existe fuera de desarrollo."""
        response = self.client.get(reverse("design_system"))

        self.assertEqual(response.status_code, 404)
