"""Pruebas de las páginas de error de producción (BUG-071)."""

from unittest import mock

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from albums.views import AlbumListView


@override_settings(DEBUG=False)
class ErrorPageTests(TestCase):
    """BUG-071 — Los errores 404 y 500 usan la interfaz en español."""

    def test_not_found_page_is_branded_and_offers_a_way_back(self):
        """BUG-071 — El 404 está en español y enlaza con Mis álbumes."""
        response = self.client.get("/esta-direccion-no-existe/")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(
            response,
            "No encontramos esta página",
            status_code=404,
        )
        self.assertContains(response, "Volver a Mis álbumes", status_code=404)
        self.assertContains(response, "css/app.css", status_code=404)
        self.assertNotContains(response, "Not Found", status_code=404)

    def test_internal_error_page_is_safe_and_does_not_need_context(self):
        """BUG-071 — El 500 está en español y no muestra la excepción."""
        user = User.objects.create_user(
            email="mira@estudio.test",
            password="TraduccionSegura42",
            display_name="Mira Okonkwo",
        )
        client = Client(raise_request_exception=False)
        client.force_login(user)

        with mock.patch.object(
            AlbumListView,
            "get_context_data",
            side_effect=RuntimeError("detalle interno secreto"),
        ):
            response = client.get(reverse("albums:list"))

        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "500.html")
        self.assertContains(response, "Algo salió mal", status_code=500)
        self.assertContains(response, "Volver a Mis álbumes", status_code=500)
        self.assertContains(response, "css/app.css", status_code=500)
        self.assertNotContains(response, "detalle interno secreto", status_code=500)
        self.assertNotContains(response, "Server Error", status_code=500)
