"""Pruebas de la carga de páginas de un álbum (HU-09)."""

import io
import shutil
import struct
import tempfile
import zlib

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import User
from albums.models import Album, ComicPage, Language

PASSWORD = "TraduccionSegura42"

MEDIA_ROOT = tempfile.mkdtemp(prefix="panelingo-test-media-")


def make_image_bytes(width=1600, height=2200, image_format="PNG"):
    """Genera una imagen real en memoria y devuelve sus bytes."""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color=(70, 60, 200)).save(
        buffer, format=image_format
    )
    return buffer.getvalue()


def make_upload(name="pagina.png", width=1600, height=2200, image_format="PNG"):
    """Devuelve un archivo cargado con una imagen real dentro."""
    content_types = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "WEBP": "image/webp",
    }
    return SimpleUploadedFile(
        name,
        make_image_bytes(width, height, image_format),
        content_type=content_types[image_format],
    )


def make_png_declaring_size(width, height):
    """Construye un PNG cuya cabecera declara unas dimensiones enormes.

    Pesa unos pocos bytes pero anuncia una imagen gigantesca. Es la forma que
    toma una "decompression bomb": Pillow lee las dimensiones de la cabecera
    al abrir, antes de decodificar, y ahí es donde debe detenerse.
    """

    def chunk(kind, data):
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b"")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PageUploadTestCase(TestCase):
    """Base común: dos cuentas, un álbum de cada una y media/ temporal."""

    def setUp(self):
        """Crea las cuentas, los idiomas y los dos álbumes."""
        self.owner = User.objects.create_user(
            email="mira@estudio.test",
            password=PASSWORD,
            display_name="Mira Okonkwo",
        )
        self.other = User.objects.create_user(
            email="ajena@estudio.test",
            password=PASSWORD,
            display_name="Cuenta ajena",
        )
        self.japanese = Language.objects.get(code="ja")
        self.spanish = Language.objects.get(code="es")
        self.album = self.make_album(self.owner, "Neon Yokai Bureau")
        self.foreign_album = self.make_album(self.other, "Álbum ajeno")

    def tearDown(self):
        """Borra los archivos que la prueba haya dejado en media/."""
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def make_album(self, owner, title):
        """Crea un álbum a nombre de la cuenta indicada."""
        return Album.objects.create(
            owner=owner,
            title=title,
            source_language=self.japanese,
            target_language=self.spanish,
        )

    def sign_in(self, user=None):
        """Inicia la sesión del usuario indicado."""
        self.client.login(email=(user or self.owner).email, password=PASSWORD)

    def upload(self, album=None, files=None):
        """Envía un lote de archivos a la pantalla de carga de un álbum."""
        target = album or self.album
        return self.client.post(
            target.get_upload_url(), data={"pages": files or [make_upload()]}
        )


class PageUploadSuccessTests(PageUploadTestCase):
    """CP-09.1 — Cargar imágenes válidas en un álbum propio — Happy Path."""

    def test_a_valid_png_creates_a_page_in_the_album(self):
        """CP-09.1 — Un PNG válido crea la página y queda asociada al álbum."""
        self.sign_in()

        response = self.upload()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ComicPage.objects.count(), 1)
        page = ComicPage.objects.get()
        self.assertEqual(page.album, self.album)
        self.assertEqual(page.page_number, 1)
        self.assertEqual(page.status, ComicPage.Status.PENDING)
        self.assertEqual((page.width, page.height), (1600, 2200))

    def test_a_valid_jpeg_is_accepted(self):
        """CP-09.1 — Un JPEG válido también se acepta."""
        self.sign_in()

        self.upload(files=[make_upload("pagina.jpg", image_format="JPEG")])

        self.assertEqual(ComicPage.objects.count(), 1)

    def test_the_stored_file_is_a_complete_image(self):
        """CP-09.1 — El archivo guardado se puede abrir y no está truncado.

        Es la prueba del fallo silencioso: si el puntero del archivo no se
        rebobina tras validarlo con Pillow, la validación pasa y en disco
        queda un archivo vacío o cortado. Nada lo delataría salvo intentar
        abrir lo guardado, que es lo que se hace aquí.
        """
        self.sign_in()

        self.upload()

        page = ComicPage.objects.get()
        with Image.open(page.image.path) as stored:
            self.assertEqual(stored.size, (1600, 2200))
            stored.load()

    def test_a_thumbnail_is_generated(self):
        """CP-09.1 — Se genera la miniatura para la rejilla del álbum."""
        self.sign_in()

        self.upload()

        page = ComicPage.objects.get()
        self.assertTrue(page.thumbnail)
        with Image.open(page.thumbnail.path) as thumb:
            self.assertLessEqual(max(thumb.size), settings.THUMBNAIL_MAX_SIDE)
        self.assertLess(page.thumbnail.size, page.image.size)

    def test_the_page_appears_in_the_album_detail(self):
        """CP-09.1 — La página queda visible en el detalle del álbum."""
        self.sign_in()
        self.upload()

        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(response, "Página 1")
        self.assertContains(response, ComicPage.objects.get().thumbnail.url)
        self.assertNotContains(response, "Este álbum aún no tiene páginas")

    def test_the_grid_serves_the_thumbnail_and_not_the_original(self):
        """La rejilla sirve la miniatura, no la imagen original."""
        self.sign_in()
        self.upload()
        page = ComicPage.objects.get()

        content = self.client.get(self.album.get_absolute_url()).content.decode()

        self.assertIn(page.thumbnail.url, content)
        self.assertNotIn(page.image.url, content)
        self.assertIn('loading="lazy"', content)


class PageNumberingTests(PageUploadTestCase):
    """La numeración continúa la secuencia y no se repite."""

    def test_numbers_are_consecutive_within_a_batch(self):
        """Los page_number de un lote quedan consecutivos."""
        self.sign_in()

        self.upload(files=[make_upload(f"p{index}.png") for index in range(3)])

        numbers = list(self.album.pages.values_list("page_number", flat=True))
        self.assertEqual(numbers, [1, 2, 3])

    def test_a_second_batch_continues_the_sequence(self):
        """Un lote posterior continúa donde terminó el anterior."""
        self.sign_in()
        self.upload(files=[make_upload("a.png"), make_upload("b.png")])

        self.upload(files=[make_upload("c.png")])

        numbers = list(self.album.pages.values_list("page_number", flat=True))
        self.assertEqual(numbers, [1, 2, 3])
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_numbering_is_independent_per_album(self):
        """Cada álbum lleva su propia numeración desde uno."""
        second_album = self.make_album(self.owner, "Salt & Static")
        self.sign_in()

        self.upload(files=[make_upload("a.png")])
        self.upload(album=second_album, files=[make_upload("b.png")])

        self.assertEqual(self.album.pages.get().page_number, 1)
        self.assertEqual(second_album.pages.get().page_number, 1)


class PageRejectionTests(PageUploadTestCase):
    """CP-09.2 — Archivos no permitidos o inválidos — Flujo alternativo."""

    def assert_nothing_was_stored(self):
        """Comprueba que no quedó ni registro ni archivo."""
        self.assertEqual(ComicPage.objects.count(), 0)

    def test_an_unsupported_format_is_rejected(self):
        """CP-09.2 — Un formato no admitido no crea página ni archivo."""
        self.sign_in()
        bad_file = SimpleUploadedFile(
            "documento.pdf",
            b"%PDF-1.4 no soy una imagen",
            content_type="application/pdf",
        )

        response = self.upload(files=[bad_file])

        self.assert_nothing_was_stored()
        self.assertContains(response, "El formato no está admitido")

    def test_a_fake_png_is_rejected(self):
        """CP-09.2 — Extensión .png con contenido que no es imagen.

        Es el caso que demuestra por qué no basta con mirar la extensión ni el
        content_type: ambos dicen PNG y el contenido es texto plano.
        """
        self.sign_in()
        fake = SimpleUploadedFile(
            "trampa.png", b"esto no es una imagen, es texto", content_type="image/png"
        )

        response = self.upload(files=[fake])

        self.assert_nothing_was_stored()
        self.assertContains(response, "no es una imagen")

    def test_a_file_over_the_size_limit_is_rejected(self):
        """CP-09.2 — Un archivo que supera el máximo se rechaza."""
        self.sign_in()
        oversized = SimpleUploadedFile(
            "enorme.png",
            b"x" * (settings.MAX_FILE_SIZE + 1),
            content_type="image/png",
        )

        response = self.upload(files=[oversized])

        self.assert_nothing_was_stored()
        self.assertContains(response, "el máximo por archivo")

    def test_an_empty_file_is_rejected(self):
        """CP-09.2 — Un archivo vacío se rechaza."""
        self.sign_in()
        empty = SimpleUploadedFile("vacio.png", b"", content_type="image/png")

        response = self.upload(files=[empty])

        self.assert_nothing_was_stored()
        self.assertContains(response, "vacío")

    def test_a_decompression_bomb_is_rejected(self):
        """CP-09.2 — Una imagen que declara dimensiones desmesuradas se rechaza.

        El archivo pesa unos pocos bytes pero su cabecera anuncia 60.000 x
        60.000 píxeles: decodificarla agotaría la memoria. Pillow solo avisa
        por encima de su umbral, así que el aviso se eleva a rechazo.
        """
        self.sign_in()
        bomb = SimpleUploadedFile(
            "bomba.png",
            make_png_declaring_size(60000, 60000),
            content_type="image/png",
        )

        response = self.upload(files=[bomb])

        self.assert_nothing_was_stored()
        self.assertContains(response, "dimensiones desproporcionadas")

    def test_a_batch_with_one_bad_file_still_loads_the_good_ones(self):
        """CP-09.2 — Un archivo malo no aborta el lote entero."""
        self.sign_in()
        bad_file = SimpleUploadedFile(
            "trampa.png", b"texto plano", content_type="image/png"
        )

        response = self.upload(files=[make_upload("buena.png"), bad_file])

        self.assertEqual(ComicPage.objects.count(), 1)
        self.assertEqual(ComicPage.objects.get().original_filename, "buena.png")
        self.assertContains(response, "Se cargó 1 página")
        self.assertContains(response, "trampa.png")


class LowResolutionWarningTests(PageUploadTestCase):
    """La baja resolución advierte, no bloquea."""

    def test_a_low_resolution_image_is_loaded_with_a_warning(self):
        """Una imagen de baja resolución se carga y queda advertida."""
        self.sign_in()

        response = self.upload(files=[make_upload("pequena.png", 860, 1220)])

        self.assertEqual(ComicPage.objects.count(), 1)
        self.assertTrue(ComicPage.objects.get().has_low_resolution)
        self.assertContains(response, "Resolución baja")

    def test_a_high_resolution_image_carries_no_warning(self):
        """Una imagen de buena resolución no lleva advertencia."""
        self.sign_in()

        self.upload(files=[make_upload("grande.png", 2150, 3035)])

        self.assertFalse(ComicPage.objects.get().has_low_resolution)

    def test_a_tall_narrow_webtoon_is_not_warned(self):
        """Una tira de webtoon estrecha pero muy alta no se marca.

        Los webtoons se publican a 800 px de ancho. Un umbral por ancho los
        marcaría todos; contando píxeles totales, no.
        """
        self.sign_in()

        self.upload(files=[make_upload("webtoon.png", 800, 6000)])

        self.assertFalse(ComicPage.objects.get().has_low_resolution)


class StoredFilenameTests(PageUploadTestCase):
    """El nombre en disco lo genera el servidor, no el cliente."""

    def test_a_path_traversal_name_cannot_escape_the_album_directory(self):
        """Un nombre con recorrido de rutas no sale del directorio del álbum.

        El nombre original no se sanea: se descarta y se genera uno nuevo. La
        prueba comprueba que el archivo acabó dentro de la carpeta del usuario
        y del álbum, y que ni el nombre en disco ni la ruta conservan rastro
        del intento.
        """
        self.sign_in()
        malicious = SimpleUploadedFile(
            "../../../etc/passwd.png",
            make_image_bytes(),
            content_type="image/png",
        )

        self.upload(files=[malicious])

        page = ComicPage.objects.get()
        expected_dir = f"albums/user_{self.owner.pk}/album_{self.album.pk}/"
        self.assertTrue(page.image.name.startswith(expected_dir), page.image.name)
        self.assertNotIn("..", page.image.name)
        self.assertNotIn("passwd", page.image.name)
        self.assertNotIn("etc", page.image.name.replace(expected_dir, ""))

    def test_django_strips_path_components_from_the_uploaded_name(self):
        """Django recorta la ruta del nombre antes de que llegue a la vista.

        UploadedFile aplica os.path.basename al asignar el nombre, así que un
        "../../../etc/passwd.png" llega ya como "passwd.png". Es una capa de
        defensa adicional a la nuestra, no la que nos protege: quedarse solo
        con ella dejaría el nombre del cliente decidiendo el del disco.
        """
        self.sign_in()
        malicious = SimpleUploadedFile(
            "../../../etc/passwd.png",
            make_image_bytes(),
            content_type="image/png",
        )

        self.upload(files=[malicious])

        self.assertEqual(ComicPage.objects.get().original_filename, "passwd.png")

    def test_the_original_filename_is_shown_escaped(self):
        """El nombre original se muestra escapado en la cola de resultados.

        El nombre se elige sin barras a propósito: Django ya recorta la ruta
        con basename, de modo que una etiqueta de cierre como </script> se
        partiría antes de llegar aquí y la prueba no estaría comprobando el
        escapado, sino el recorte.
        """
        self.sign_in()
        tricky = SimpleUploadedFile(
            "<img src=x onerror=alert(1)>.png",
            make_image_bytes(),
            content_type="image/png",
        )

        response = self.upload(files=[tricky])
        content = response.content.decode()

        self.assertNotIn("<img src=x onerror=alert(1)>", content)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;.png", content)

    def test_two_files_with_the_same_name_do_not_collide(self):
        """Dos archivos con el mismo nombre acaban en rutas distintas."""
        self.sign_in()

        self.upload(files=[make_upload("pagina1.png"), make_upload("pagina1.png")])

        names = list(ComicPage.objects.values_list("image", flat=True))
        self.assertEqual(len(names), 2)
        self.assertNotEqual(names[0], names[1])

    def test_the_extension_comes_from_the_real_format(self):
        """La extensión en disco sale del formato real, no del nombre."""
        self.sign_in()
        mislabelled = SimpleUploadedFile(
            "pagina.png",
            make_image_bytes(image_format="JPEG"),
            content_type="image/png",
        )

        self.upload(files=[mislabelled])

        self.assertTrue(ComicPage.objects.get().image.name.endswith(".jpg"))


class PageUploadIsolationTests(PageUploadTestCase):
    """Solo se carga en álbumes propios."""

    def test_uploading_to_someone_elses_album_returns_404(self):
        """Cargar en un álbum ajeno responde 404 y no crea nada."""
        self.sign_in()

        response = self.upload(album=self.foreign_album)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ComicPage.objects.count(), 0)

    def test_opening_the_upload_screen_of_a_foreign_album_returns_404(self):
        """Ni siquiera se abre la pantalla de carga de un álbum ajeno."""
        self.sign_in()

        response = self.client.get(self.foreign_album.get_upload_url())

        self.assertEqual(response.status_code, 404)

    def test_uploading_requires_a_session(self):
        """Un visitante anónimo no puede cargar páginas."""
        response = self.upload()

        self.assertEqual(ComicPage.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_the_chooser_lists_only_the_users_albums(self):
        """La pantalla de elección no muestra álbumes ajenos."""
        self.sign_in()

        response = self.client.get(reverse("albums:upload_choose"))

        self.assertContains(response, "Neon Yokai Bureau")
        self.assertNotContains(response, "Álbum ajeno")


class AlbumPageCountTests(PageUploadTestCase):
    """El álbum informa del número real de páginas."""

    def test_page_count_reflects_the_uploaded_pages(self):
        """page_count cuenta las páginas realmente cargadas."""
        self.sign_in()
        self.assertEqual(self.album.page_count, 0)

        self.upload(files=[make_upload("a.png"), make_upload("b.png")])

        self.assertEqual(self.album.page_count, 2)

    def test_progress_stays_at_zero_while_no_page_is_approved(self):
        """El avance es 0 mientras ninguna página esté aprobada."""
        self.sign_in()
        self.upload(files=[make_upload("a.png")])

        self.assertEqual(self.album.progress_percentage, 0)

    def test_deleting_the_album_deletes_its_pages(self):
        """Al borrar un álbum desaparecen sus páginas."""
        self.sign_in()
        self.upload()

        self.album.delete()

        self.assertEqual(ComicPage.objects.count(), 0)


class UploadQueueMarkupTests(PageUploadTestCase):
    """Marcado que necesita la cola de selección en cliente (BUG-043).

    El comportamiento es del navegador y las pruebas de Django no lo ejecutan.
    Lo que sí se puede custodiar desde el servidor es el contrato entre ambos:
    que los atributos existen y que los límites que emite el servidor son los
    de settings.
    """

    def test_the_input_carries_the_limits_from_settings(self):
        """Los límites del navegador salen de settings, no están escritos.

        Es la prueba que impide que cliente y servidor acaben con dos cifras
        distintas: si alguien cambia MAX_FILE_SIZE, el atributo lo sigue. Si
        en cambio alguien escribiera el número a mano en el JavaScript, esta
        prueba no lo vería, y por eso el propio archivo lleva la advertencia
        de no hacerlo.
        """
        self.sign_in()

        response = self.client.get(self.album.get_upload_url())
        content = response.content.decode()

        self.assertIn(f'data-max-size="{settings.MAX_FILE_SIZE}"', content)
        self.assertIn(
            f'data-allowed-extensions="{",".join(settings.ALLOWED_IMAGE_EXTENSIONS)}"',
            content,
        )

    @override_settings(MAX_FILE_SIZE=5_000_000)
    def test_changing_the_setting_changes_the_attribute(self):
        """Cambiar el ajuste cambia lo que ve el navegador."""
        self.sign_in()

        response = self.client.get(self.album.get_upload_url())

        self.assertContains(response, 'data-max-size="5000000"')

    def test_the_queue_container_is_present_and_announced(self):
        """La cola existe, arranca oculta y se anuncia a los lectores."""
        self.sign_in()

        response = self.client.get(self.album.get_upload_url())
        content = response.content.decode()

        self.assertIn("data-upload-selection", content)
        self.assertIn('aria-live="polite"', content)
        self.assertIn("data-upload-list", content)
        self.assertIn("data-upload-count", content)

    def test_the_dropzone_is_marked_for_drag_and_drop(self):
        """La zona de carga está marcada para recibir archivos arrastrados."""
        self.sign_in()

        response = self.client.get(self.album.get_upload_url())

        self.assertContains(response, "data-dropzone")

    def test_the_form_still_works_without_javascript(self):
        """El formulario sigue funcionando sin ejecutar ningún script.

        El cliente de pruebas de Django no ejecuta JavaScript, así que este
        POST recorre exactamente el camino de un navegador con los scripts
        desactivados. La cola es una mejora progresiva, no un requisito.
        """
        self.sign_in()

        response = self.upload(files=[make_upload("sin-scripts.png")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ComicPage.objects.count(), 1)
        self.assertEqual(ComicPage.objects.get().original_filename, "sin-scripts.png")

    def test_the_input_is_still_reachable_by_its_label(self):
        """El label sigue apuntando al input, que es lo que abre el selector."""
        self.sign_in()

        content = self.client.get(self.album.get_upload_url()).content.decode()

        self.assertIn('for="id_pages"', content)
        self.assertIn('id="id_pages"', content)
        self.assertIn('name="pages"', content)
        self.assertIn("multiple", content)


class ServerValidationIsUnchangedTests(PageUploadTestCase):
    """La retroalimentación en cliente no relajó la validación del servidor.

    El aviso del navegador es una comodidad; la autoridad sigue siendo el
    servidor. Estas pruebas repiten los rechazos de HU-09 para demostrar que
    un archivo enviado sin pasar por el JavaScript se rechaza igual.
    """

    def test_a_fake_image_is_still_rejected(self):
        """Un archivo que no es imagen se sigue rechazando."""
        self.sign_in()
        fake = SimpleUploadedFile(
            "trampa.png", b"texto plano", content_type="image/png"
        )

        response = self.upload(files=[fake])

        self.assertEqual(ComicPage.objects.count(), 0)
        self.assertContains(response, "no es una imagen")

    def test_an_oversized_file_is_still_rejected(self):
        """Un archivo por encima del límite se sigue rechazando."""
        self.sign_in()
        oversized = SimpleUploadedFile(
            "enorme.png",
            b"x" * (settings.MAX_FILE_SIZE + 1),
            content_type="image/png",
        )

        response = self.upload(files=[oversized])

        self.assertEqual(ComicPage.objects.count(), 0)
        self.assertContains(response, "el máximo por archivo")

    def test_a_decompression_bomb_is_still_rejected(self):
        """Una imagen de dimensiones desmesuradas se sigue rechazando."""
        self.sign_in()
        bomb = SimpleUploadedFile(
            "bomba.png",
            make_png_declaring_size(60000, 60000),
            content_type="image/png",
        )

        response = self.upload(files=[bomb])

        self.assertEqual(ComicPage.objects.count(), 0)
        self.assertContains(response, "dimensiones desproporcionadas")
