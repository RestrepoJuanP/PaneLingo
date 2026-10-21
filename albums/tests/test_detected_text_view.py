"""Pruebas de la vista del texto detectado de una página (HU-14)."""

from albums.ocr.base import DetectedRegion
from albums.ocr.fake import FakeOcrProvider
from albums.tests.test_processing import ProcessingTestCase, use_provider

# Dos globos en la misma fila: en japonés, el de la derecha es el n.º 1.
DOUBTFUL = DetectedRegion(260, 50, 120, 80, "たぶん", 0.42)
RELIABLE = DetectedRegion(40, 40, 120, 80, "たしかに", 0.98)


class DetectedTextTestCase(ProcessingTestCase):
    """Base: la página procesada con una región dudosa y otra fiable."""

    def setUp(self):
        """Procesa la página con las dos regiones."""
        super().setUp()
        with use_provider(FakeOcrProvider(regions=[DOUBTFUL, RELIABLE])):
            self.process()

    def workspace(self, query=""):
        """Devuelve el HTML del espacio de trabajo de la página."""
        response = self.client.get(self.page.get_absolute_url() + query)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()


class SplitViewTests(DetectedTextTestCase):
    """CP-14.1 — Vista dividida de imagen y texto — Happy Path."""

    def test_image_and_text_panels_are_shown(self):
        """CP-14.1 — La imagen con sus regiones y el panel de texto."""
        content = self.workspace()

        self.assertIn("data-region-workspace", content)
        self.assertIn('class="region-canvas"', content)
        self.assertIn("Texto detectado", content)

    def test_texts_follow_the_reading_order(self):
        """CP-14.1 — El texto aparece en orden de lectura, con tipo y confianza."""
        content = self.workspace()

        self.assertLess(content.index("たぶん"), content.index("たしかに"))
        self.assertIn("Globo de diálogo", content)
        self.assertIn("42 % baja", content)
        self.assertIn("98 % alta", content)


class LinkedSelectionTests(DetectedTextTestCase):
    """CP-14.2 — Relacionar la región con su texto."""

    def test_each_region_links_to_its_text_and_back(self):
        """CP-14.2 — La caja enlaza con su texto y el texto con su caja."""
        content = self.workspace()

        self.assertIn('id="region-box-1"', content)
        self.assertIn('href="#region-1"', content)
        self.assertIn('id="region-1"', content)
        self.assertIn('href="#region-box-1"', content)

    def test_both_halves_share_the_region_number(self):
        """CP-14.2 — Caja y texto llevan el mismo número para resaltarse juntos."""
        content = self.workspace()

        self.assertEqual(content.count('data-region="1"'), 2)
        self.assertIn('data-region-item="1"', content)


class ReviewHighlightTests(DetectedTextTestCase):
    """CP-14.3 — Destacar lo que conviene revisar."""

    def test_doubtful_regions_are_marked_beyond_colour(self):
        """CP-14.3 — La región dudosa se distingue con forma y texto."""
        content = self.workspace()

        self.assertIn("region-box--review", content)
        self.assertIn("1 !", content)
        self.assertIn("necesita revisión", content)
        self.assertIn("block-card--review", content)

    def test_only_pending_regions_can_be_shown(self):
        """CP-14.3 — El filtro "Por revisar" deja solo las regiones dudosas."""
        content = self.workspace("?filtro=revisar")

        self.assertIn("たぶん", content)
        self.assertNotIn("たしかに", content)
        self.assertIn("Por revisar (1)", content)
        self.assertIn('ws-group__option is-active"', content)

    def test_without_doubtful_regions_there_is_no_filter(self):
        """CP-14.3 — Flujo alternativo: si nada necesita revisión, no hay filtro."""
        self.process(confirm="1")

        self.assertNotIn("Por revisar", self.workspace())


class UnprocessedPageTests(ProcessingTestCase):
    """CP-14.4 — La página aún no se ha procesado — Flujo alternativo."""

    def test_the_page_invites_to_process_it(self):
        """CP-14.4 — Se indica que no se ha procesado y se ofrece hacerlo."""
        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, "Esta página aún no se ha procesado.")
        self.assertContains(response, "Procesar página")


class KeyboardAndScreenReaderTests(DetectedTextTestCase):
    """CP-14.5 — Uso completo con teclado y lector de pantalla."""

    def test_regions_announce_number_type_and_text(self):
        """CP-14.5 — Cada región anuncia su número, su tipo y su texto."""
        content = self.workspace()

        self.assertIn(
            'aria-label="Región 1: globo de diálogo, necesita revisión. '
            'Texto: たぶん"',
            content,
        )
        self.assertIn(
            'aria-label="Región 2: globo de diálogo. Texto: たしかに"', content
        )

    def test_regions_and_texts_are_real_links(self):
        """CP-14.5 — Cajas y textos son enlaces, así que se recorren con Tab."""
        content = self.workspace()

        self.assertEqual(content.count('class="block-card__head"'), 2)
        self.assertEqual(content.count('class="region-box region-box--'), 2)
