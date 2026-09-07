"""Ninguna plantilla puede filtrar sintaxis de plantilla al HTML final.

Red de seguridad de BUG-046. Los comentarios `{# ... #}` de Django solo
funcionan en una línea: escritos en varias, no se interpretan y se renderizan
literalmente como texto visible. El fallo no rompe nada, no lanza ninguna
excepción y ninguna prueba de contenido lo detecta, porque esas comprueban que
aparezca lo que debe aparecer, no que no aparezca lo que no debe.

Se comprueban DOS cosas, y buscar la cadena "{#" es solo la primera:

1. Que no llegue ningún delimitador de plantilla sin interpretar. Se buscan
   los cuatro: "{#", "#}", "{%" y "{{". Los dos últimos amplían la red a
   fallos distintos del de este bug —una etiqueta mal cerrada, una variable
   escrita dentro de un bloque `verbatim` por descuido, un `{% comment %}` sin
   su cierre— que también dejarían sintaxis a la vista.

2. Que no aparezca el texto de los comentarios. Es la comprobación que de
   verdad ata el fallo: un comentario podría filtrarse con su delimitador
   comido por el escapado y seguir mostrando la prosa. Se toma la primera
   frase real de cada comentario de cada plantilla y se verifica que no está
   en ninguna respuesta.

La segunda comprobación se construye leyendo las plantillas del repositorio,
así que cubre las que existan en cada momento sin tener que mantener una lista
a mano.
"""

import pathlib
import re
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from albums.models import Album, Language
from albums.tests.test_pages import make_image_bytes

PASSWORD = "TraduccionSegura42"

MEDIA_ROOT = tempfile.mkdtemp(prefix="panelingo-hygiene-media-")

TEMPLATES_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "templates"

# Delimitadores que nunca deben llegar al navegador.
TEMPLATE_DELIMITERS = ["{#", "#}", "{%", "{{"]


def comment_openings():
    """Devuelve la primera frase de cada comentario de cada plantilla.

    Sirve para detectar un comentario filtrado aunque sus delimitadores no
    aparezcan en la salida. Se descartan los fragmentos muy cortos, que
    podrían coincidir con texto legítimo de la interfaz.
    """
    fragments = {}
    pattern = re.compile(
        r"\{#(.*?)#\}|\{%\s*comment\s*%\}(.*?)\{%\s*endcomment\s*%\}", re.S
    )

    for template in sorted(TEMPLATES_DIR.rglob("*.html")):
        for match in pattern.finditer(template.read_text(encoding="utf-8")):
            body = (match.group(1) or match.group(2) or "").strip()
            first_line = body.split("\n")[0].strip()
            if len(first_line) >= 25:
                fragments[first_line] = str(template.relative_to(TEMPLATES_DIR))
    return fragments


@override_settings(MEDIA_ROOT=MEDIA_ROOT, DEBUG=True)
class TemplateHygieneTests(TestCase):
    """Ninguna pantalla principal filtra sintaxis ni prosa de comentario."""

    def setUp(self):
        """Crea una cuenta con un álbum y una página cargada."""
        self.user = User.objects.create_user(
            email="mira@estudio.test",
            password=PASSWORD,
            display_name="Mira Okonkwo",
        )
        self.album = Album.objects.create(
            owner=self.user,
            title="Neon Yokai Bureau",
            source_language=Language.objects.get(code="ja"),
            target_language=Language.objects.get(code="es"),
        )
        self.client.login(email=self.user.email, password=PASSWORD)
        self.client.post(
            self.album.get_upload_url(),
            data={
                "pages": [
                    SimpleUploadedFile(
                        "pagina.png", make_image_bytes(400, 560), "image/png"
                    )
                ]
            },
        )
        self.page = self.album.pages.get()

    def tearDown(self):
        """Borra los archivos que la prueba haya dejado en media/."""
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def rendered_pages(self):
        """Devuelve el HTML de cada pantalla principal, con su nombre."""
        authenticated = {
            "biblioteca": reverse("albums:list"),
            "crear álbum": reverse("albums:create"),
            "detalle de álbum": self.album.get_absolute_url(),
            "editar álbum": self.album.get_edit_url(),
            "renombrar álbum": self.album.get_rename_url(),
            "cargar páginas": self.album.get_upload_url(),
            "elegir álbum": reverse("albums:upload_choose"),
            "eliminar página": self.page.get_delete_url(),
            "sistema de diseño": reverse("design_system"),
        }
        public = {
            "iniciar sesión": reverse("accounts:login"),
            "crear cuenta": reverse("accounts:register"),
            "recuperar contraseña": reverse("accounts:password_reset"),
            "revisa tu correo": reverse("accounts:password_reset_done"),
            "contraseña actualizada": reverse("accounts:password_reset_complete"),
        }

        pages = {}
        for name, url in authenticated.items():
            pages[name] = self.client.get(url).content.decode()

        self.client.logout()
        for name, url in public.items():
            pages[name] = self.client.get(url).content.decode()
        return pages

    def test_no_template_delimiter_reaches_the_browser(self):
        """Ninguna pantalla contiene sintaxis de plantilla sin interpretar."""
        for name, html in self.rendered_pages().items():
            for delimiter in TEMPLATE_DELIMITERS:
                with self.subTest(pantalla=name, delimitador=delimiter):
                    self.assertNotIn(
                        delimiter,
                        html,
                        f"La pantalla «{name}» filtra {delimiter} al HTML. "
                        f"Suele ser un comentario de varias líneas escrito "
                        f"con {{# #}}, que solo funciona en una línea: usa "
                        f"{{% comment %}} … {{% endcomment %}}.",
                    )

    def test_no_comment_text_reaches_the_browser(self):
        """Ningún comentario de desarrollo aparece como texto en la página."""
        fragments = comment_openings()
        self.assertGreater(len(fragments), 20, "No se leyó ningún comentario.")

        pages = self.rendered_pages()
        for fragment, template in fragments.items():
            for name, html in pages.items():
                with self.subTest(pantalla=name, plantilla=template):
                    self.assertNotIn(
                        fragment,
                        html,
                        f"El comentario de «{template}» se está renderizando "
                        f"en la pantalla «{name}».",
                    )


class CommentSyntaxTests(TestCase):
    """Los comentarios de varias líneas usan la etiqueta, no la sintaxis breve.

    Complementa a las anteriores: las de arriba miran el HTML renderizado de
    las pantallas principales, y esta mira el código fuente de TODAS las
    plantillas, incluidas las que ninguna vista sirva todavía.
    """

    def test_no_template_uses_a_multiline_short_comment(self):
        """Ninguna plantilla escribe {# … #} repartido en varias líneas."""
        offenders = []
        for template in sorted(TEMPLATES_DIR.rglob("*.html")):
            content = template.read_text(encoding="utf-8")
            for match in re.finditer(r"\{#(.*?)#\}", content, re.S):
                if "\n" in match.group(0):
                    line = content[: match.start()].count("\n") + 1
                    offenders.append(f"{template.relative_to(TEMPLATES_DIR)}:{line}")

        self.assertEqual(
            offenders,
            [],
            "Estos comentarios ocupan varias líneas con {# #}, que solo "
            "funciona en una: se renderizarían como texto visible. Usa "
            "{% comment %} … {% endcomment %}. " + ", ".join(offenders),
        )
