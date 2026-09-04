"""Pruebas de la página de referencia del sistema de diseño."""

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User


class DesignSystemViewTests(TestCase):
    """La página de estilos solo existe en desarrollo y exige sesión."""

    def setUp(self):
        """Crea la cuenta con la que se consulta la página."""
        self.url = reverse("design_system")
        self.password = "TraduccionSegura42"
        self.user = User.objects.create_user(
            email="mira@estudio.test",
            password=self.password,
            display_name="Mira Okonkwo",
        )

    @override_settings(DEBUG=True)
    def test_available_to_an_authenticated_user_in_development(self):
        """Humo — La referencia de estilos responde con DEBUG y sesión."""
        self.client.login(email=self.user.email, password=self.password)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "design_system.html")

    @override_settings(DEBUG=True)
    def test_requires_a_session_even_in_development(self):
        """Un visitante anónimo no accede a la referencia de estilos."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    @override_settings(DEBUG=False)
    def test_hidden_when_debug_is_disabled(self):
        """Humo — La referencia de estilos no existe fuera de desarrollo."""
        self.client.login(email=self.user.email, password=self.password)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=False)
    def test_hidden_from_anonymous_visitors_without_revealing_the_route(self):
        """Fuera de desarrollo responde 404, no una redirección al login.

        Una redirección revelaría que la ruta existe; el 404 no.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
