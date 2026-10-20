"""Pruebas de los enlaces versionados a los archivos estáticos."""

from django.template import Context, Template
from django.test import SimpleTestCase


def render(path):
    """Renderiza la etiqueta versioned_static para la ruta indicada."""
    template = Template("{% load assets %}{% versioned_static path %}")
    return template.render(Context({"path": path}))


class VersionedStaticTests(SimpleTestCase):
    """Los cambios en el CSS y el JavaScript llegan sin vaciar la caché."""

    def test_an_existing_file_carries_its_version(self):
        """La dirección de un archivo propio lleva ?v= con su versión."""
        url = render("js/app.js")

        self.assertRegex(url, r"^/static/js/app\.js\?v=\d+$")

    def test_an_unknown_file_keeps_a_plain_address(self):
        """Flujo alternativo: un archivo que no existe no rompe la página."""
        self.assertEqual(render("js/no-existe.js"), "/static/js/no-existe.js")
