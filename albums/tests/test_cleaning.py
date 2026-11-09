"""Pruebas de la limpieza del texto original de una página (HU-88)."""

import io
from unittest import mock

from PIL import Image, ImageDraw

from albums.cleaning import clean_region_incrementally
from albums.models import ComicPage, TextRegion
from albums.tests.test_processing import ProcessingTestCase


class PageCleaningTests(ProcessingTestCase):
    """Escenarios CP-88.1 a CP-88.8 sobre imágenes sintéticas."""

    COLORS = (
        (245, 235, 225),
        (220, 238, 250),
        (236, 225, 248),
        (225, 244, 230),
        (250, 238, 210),
        (228, 232, 245),
        (242, 225, 232),
        (230, 240, 220),
    )

    def setUp(self):
        """Prepara ocho globos uniformes con texto y contorno sintéticos."""
        super().setUp()
        self.regions = self.prepare_scene(self.page)

    def prepare_scene(self, page):
        """Escribe la escena sintética y devuelve sus ocho regiones."""
        image = Image.new("RGB", (160, 120), (190, 190, 190))
        draw = ImageDraw.Draw(image)
        coordinates = []
        for index, color in enumerate(self.COLORS):
            column = index % 4
            row = index // 4
            x = 15 + column * 35
            y = 20 + row * 50
            width = 18
            height = 10
            coordinates.append((x, y, width, height))
            draw.rectangle(
                (x - 7, y - 7, x + width + 6, y + height + 6),
                fill=color,
            )
            draw.rectangle(
                (x - 8, y - 8, x + width + 7, y + height + 7),
                outline=(20, 20, 20),
            )
            draw.line((x + 2, y + 5, x + width - 3, y + 5), fill=(0, 0, 0))

        output = io.BytesIO()
        image.save(output, format="PNG")
        with page.image.open("wb") as image_file:
            image_file.write(output.getvalue())
        page.width = image.width
        page.height = image.height
        page.file_size = len(output.getvalue())
        page.status = ComicPage.Status.PROCESSED
        page.save(update_fields=["width", "height", "file_size", "status"])
        page.regions.all().delete()
        return [
            TextRegion.objects.create(
                page=page,
                reading_order=index,
                x=x,
                y=y,
                width=width,
                height=height,
                source_text=f"Texto {index}",
            )
            for index, (x, y, width, height) in enumerate(coordinates, start=1)
        ]

    def clean(self, page=None):
        """Solicita la limpieza y ejecuta la tarea encolada por la petición."""
        page = page or self.page
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(page.get_clean_url())
        page.refresh_from_db()
        return response

    def cleaned_image(self, page=None):
        """Abre una copia RGB de la capa limpia guardada."""
        page = page or self.page
        page.refresh_from_db()
        with (
            page.cleaned_image.open("rb") as image_file,
            Image.open(image_file) as image,
        ):
            return image.convert("RGB")

    def original_bytes(self, page=None):
        """Lee los bytes de la imagen original para comprobar su inmutabilidad."""
        page = page or self.page
        with page.image.open("rb") as image_file:
            return image_file.read()

    def test_eight_uniform_regions_are_filled_without_touching_original(self):
        """CP-88.1 — Limpia ocho globos uniformes y conserva original y contornos."""
        original = self.original_bytes()

        response = self.clean()

        self.assertRedirects(response, self.page.get_absolute_url())
        self.assertEqual(self.original_bytes(), original)
        cleaned = self.cleaned_image()
        for region, color in zip(self.regions, self.COLORS, strict=True):
            region.refresh_from_db()
            self.assertEqual(region.cleaning_status, TextRegion.CleaningStatus.FILLED)
            self.assertEqual(cleaned.getpixel((region.x + 5, region.y + 5)), color)
            self.assertEqual(
                cleaned.getpixel((region.x - 8, region.y - 8)),
                (20, 20, 20),
            )

    @mock.patch("albums.tasks.clean_page_task")
    def test_cleaning_is_queued_and_shown_as_in_progress(self, task):
        """CP-88.1 — El botón inicia una tarea asíncrona con estado visible."""
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.page.get_clean_url())
        self.page.refresh_from_db()

        self.assertEqual(self.page.cleaning_state, ComicPage.CleaningState.CLEANING)
        task.assert_called_once_with(self.page.pk)
        status = self.client.get(self.page.get_status_url()).json()
        self.assertTrue(status["is_cleaning"])
        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, "Limpiando la página…")

    def test_non_uniform_region_is_left_for_manual_cleaning(self):
        """CP-88.2 — Un anillo no uniforme conserva el texto y muestra el aviso."""
        region = self.regions[0]
        with self.page.image.open("rb") as image_file, Image.open(image_file) as source:
            image = source.convert("RGB")
        draw = ImageDraw.Draw(image)
        for x in range(region.x - 5, region.x + region.width + 5):
            color = (0, 0, 0) if x % 2 else (255, 255, 255)
            draw.point((x, region.y - 5), fill=color)
            draw.point((x, region.y + region.height + 4), fill=color)
        for y in range(region.y - 2, region.y + region.height + 2):
            color = (0, 0, 0) if y % 2 else (255, 255, 255)
            draw.point((region.x - 5, y), fill=color)
            draw.point((region.x + region.width + 4, y), fill=color)
        output = io.BytesIO()
        image.save(output, format="PNG")
        with self.page.image.open("wb") as image_file:
            image_file.write(output.getvalue())
        before = image.getpixel((region.x + 5, region.y + 5))

        self.clean()
        region.refresh_from_db()

        self.assertEqual(region.cleaning_status, TextRegion.CleaningStatus.MANUAL)
        self.assertEqual(
            self.cleaned_image().getpixel((region.x + 5, region.y + 5)), before
        )
        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, "1 región necesita limpieza manual o con IA")
        self.assertContains(response, "Limpieza manual")

    def test_skipped_region_remains_identical(self):
        """CP-88.3 — «No traducir» conserva intacta la zona original."""
        region = self.regions[0]
        region.skip_translation = True
        region.save(update_fields=["skip_translation"])
        with self.page.image.open("rb") as image_file, Image.open(image_file) as source:
            original = source.convert("RGB")

        self.clean()
        region.refresh_from_db()

        self.assertEqual(region.cleaning_status, TextRegion.CleaningStatus.KEPT)
        box = (
            region.x - 2,
            region.y - 2,
            region.x + region.width + 2,
            region.y + region.height + 2,
        )
        self.assertEqual(
            self.cleaned_image().crop(box).tobytes(), original.crop(box).tobytes()
        )

    def test_workspace_offers_original_clean_and_translated_views(self):
        """CP-88.4 — Ofrece tres vistas y reserva el overlay para traducida."""
        self.clean()

        response = self.client.get(self.page.get_absolute_url())

        self.assertContains(response, 'data-preview-mode="original"')
        self.assertContains(response, 'data-preview-mode="cleaned"')
        self.assertContains(response, 'data-preview-mode="translated"')
        self.assertContains(
            response, f'data-cleaned-src="{self.page.get_cleaned_image_url()}"'
        )
        self.assertContains(response, "data-page-overlay hidden")

    def test_restore_puts_back_original_pixels_and_pending_status(self):
        """CP-88.5 — Restaurar devuelve la zona original y marca «Sin limpiar»."""
        self.clean()
        region = self.regions[0]
        response = self.client.post(region.get_restore_cleaning_url())
        region.refresh_from_db()
        with self.page.image.open("rb") as image_file, Image.open(image_file) as source:
            original = source.convert("RGB")
        box = (
            region.x - 2,
            region.y - 2,
            region.x + region.width + 2,
            region.y + region.height + 2,
        )

        self.assertRedirects(
            response,
            f"{self.page.get_absolute_url()}#region-{region.reading_order}",
            fetch_redirect_response=False,
        )
        self.assertEqual(region.cleaning_status, TextRegion.CleaningStatus.PENDING)
        self.assertEqual(
            self.cleaned_image().crop(box).tobytes(), original.crop(box).tobytes()
        )

    @mock.patch("albums.cleaning.build_cleaned_image", side_effect=OSError("fallo"))
    def test_failure_keeps_original_and_offers_retry(self, _build):
        """CP-88.6 — Un fallo conserva el original y ofrece volver a intentar."""
        original = self.original_bytes()

        self.clean()

        self.assertEqual(self.original_bytes(), original)
        self.assertEqual(self.page.cleaning_state, ComicPage.CleaningState.FAILED)
        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, "No se pudo limpiar la página")
        self.assertContains(response, "Reintentar")

    def test_region_actions_update_only_their_area(self):
        """CP-88.7 — No traducir, habilitar y eliminar actualizan solo esa región."""
        self.clean()
        first = self.regions[0]
        second = self.regions[1]
        marker = (255, 0, 255)
        cleaned = self.cleaned_image()
        cleaned.putpixel((second.x + 1, second.y + 1), marker)
        output = io.BytesIO()
        cleaned.save(output, format="PNG")
        with self.page.cleaned_image.open("wb") as image_file:
            image_file.write(output.getvalue())

        self.client.post(first.get_skip_translation_url())
        first.refresh_from_db()
        self.assertEqual(first.cleaning_status, TextRegion.CleaningStatus.KEPT)
        self.assertEqual(
            self.cleaned_image().getpixel((second.x + 1, second.y + 1)), marker
        )

        self.client.post(first.get_enable_translation_url())
        first.refresh_from_db()
        self.assertEqual(first.cleaning_status, TextRegion.CleaningStatus.FILLED)
        self.assertEqual(
            self.cleaned_image().getpixel((second.x + 1, second.y + 1)), marker
        )

        self.client.post(first.get_delete_url())
        self.assertFalse(TextRegion.objects.filter(pk=first.pk).exists())
        self.assertEqual(
            self.cleaned_image().getpixel((second.x + 1, second.y + 1)), marker
        )

    def test_new_region_is_cleaned_without_rebuilding_the_page(self):
        """CP-88.7 — Una región nueva modifica solo su zona de la capa existente."""
        self.clean()
        marker_position = (2, 2)
        marker = (255, 0, 255)
        cleaned = self.cleaned_image()
        cleaned.putpixel(marker_position, marker)
        output = io.BytesIO()
        cleaned.save(output, format="PNG")
        with self.page.cleaned_image.open("wb") as image_file:
            image_file.write(output.getvalue())
        region = TextRegion.objects.create(
            page=self.page,
            reading_order=9,
            x=140,
            y=100,
            width=10,
            height=8,
            source_text="Nuevo",
        )

        clean_region_incrementally(region)
        region.refresh_from_db()

        self.assertEqual(region.cleaning_status, TextRegion.CleaningStatus.FILLED)
        self.assertEqual(self.cleaned_image().getpixel(marker_position), marker)

    def test_foreign_cleaning_resources_and_actions_return_not_found(self):
        """CP-88.8 — Página, región e imagen limpia ajenas responden 404."""
        foreign_regions = self.prepare_scene(self.foreign_page)
        clean_region_incrementally(foreign_regions[0])

        self.assertEqual(
            self.client.post(self.foreign_page.get_clean_url()).status_code, 404
        )
        self.assertEqual(
            self.client.get(self.foreign_page.get_cleaned_image_url()).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(foreign_regions[0].get_restore_cleaning_url()).status_code,
            404,
        )
