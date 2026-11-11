"""Pruebas de servidor de la maquetación sobre la imagen (HU-89, ADR-003)."""

import io
from types import SimpleNamespace
from unittest import mock

from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image, ImageChops, ImageDraw

from albums.cleaning import replace_cleaned_image, start_cleaning
from albums.corrections import correct_region, restore_region
from albums.manual_regions import add_manual_region
from albums.models import ComicPage, TextRegion
from albums.ocr.base import DetectedRegion
from albums.ocr.fake import FakeOcrProvider
from albums.processing import save_regions, start_processing
from albums.region_management import set_translation_skipped
from albums.tests.test_processing import MEDIA_ROOT, ProcessingTestCase
from albums.translating import apply_translations
from albums.translation_review import (
    approve_translation,
    leave_page_approval,
    unapprove_translation,
)
from albums.typesetting import (
    FONTS,
    MAX_FIXED_FONT_SIZE,
    layout_for_region,
    load_font,
    render_page,
)
from albums.views import timestamp_version

PAGE_SIZE = (400, 560)
WHITE = (255, 255, 255)
INK = (30, 30, 30)
LAYOUT_FIELDS = (
    "layout_x",
    "layout_y",
    "layout_width",
    "layout_height",
    "font_family",
    "font_size",
    "text_align",
    "text_color",
    "layout_updated_at",
)


def png_bytes(image):
    """Codifica una imagen como PNG en memoria."""
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


@override_settings(MEDIA_ROOT=MEDIA_ROOT, OCR_PROVIDER="fake")
class TypesettingTestCase(ProcessingTestCase):
    """Base: una página limpia con dos traducciones aprobadas."""

    BOXES = {
        1: (40, 60, 160, 80),
        2: (200, 300, 160, 100),
    }

    def setUp(self):
        """Prepara la página propia lista para maquetar."""
        super().setUp()
        self.first, self.second = self.make_ready_page(self.page)

    def write_original(self, page):
        """Página blanca con un bloque de texto original en cada caja."""
        image = Image.new("RGB", PAGE_SIZE, WHITE)
        draw = ImageDraw.Draw(image)
        for x, y, width, height in self.BOXES.values():
            draw.rectangle((x + 10, y + 10, x + width - 10, y + height - 10), fill=INK)
        content = png_bytes(image)
        with page.image.open("wb") as image_file:
            image_file.write(content)
        page.width, page.height = PAGE_SIZE
        page.file_size = len(content)

    def make_ready_page(self, page):
        """Deja la página aprobada, limpia y con dos traducciones aprobadas."""
        self.write_original(page)
        page.cleaned_image.save(
            "cleaned.png",
            ContentFile(png_bytes(Image.new("RGB", PAGE_SIZE, WHITE))),
            save=False,
        )
        page.status = ComicPage.Status.APPROVED
        page.save(
            update_fields=["width", "height", "file_size", "status", "cleaned_image"]
        )
        page.regions.all().delete()
        texts = {1: "¡Hola, mundo!", 2: "Mientras tanto, en la ciudad..."}
        kinds = {1: TextRegion.Kind.BALLOON, 2: TextRegion.Kind.NARRATION}
        regions = []
        for number, (x, y, width, height) in self.BOXES.items():
            regions.append(
                TextRegion.objects.create(
                    page=page,
                    reading_order=number,
                    kind=kinds[number],
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    source_text=f"原文{number}",
                    confidence=0.97,
                    cleaning_status=TextRegion.CleaningStatus.FILLED,
                    translation=texts[number],
                    translation_status=TextRegion.TranslationStatus.APPROVED,
                    translated_at=timezone.now(),
                    approved_at=timezone.now(),
                )
            )
        return regions

    def mark_typeset(self, page):
        """Marca la página como maquetada sin pasar por save()."""
        stamp = timezone.now()
        ComicPage.objects.filter(pk=page.pk).update(typeset_approved_at=stamp)
        page.typeset_approved_at = stamp

    def typeset_stamp(self, page):
        """Lee de la base de datos la fecha de maquetación de la página."""
        return ComicPage.objects.get(pk=page.pk).typeset_approved_at

    def post_layout(self, region, data, version=None):
        """Envía un cambio de maquetación con la versión vigente."""
        region.refresh_from_db()
        payload = {"version": timestamp_version(region.layout_updated_at)}
        if version is not None:
            payload["version"] = version
        payload.update(data)
        return self.client.post(
            reverse("albums:region_layout", kwargs={"pk": region.pk}), payload
        )

    def post_reset(self, region):
        """Pide "Restablecer" con la versión vigente."""
        region.refresh_from_db()
        return self.client.post(
            reverse("albums:region_layout_reset", kwargs={"pk": region.pk}),
            {"version": timestamp_version(region.layout_updated_at)},
        )

    def post_approve(self, page, as_json=True):
        """Pide "Aprobar página" en la pestaña Maquetación."""
        headers = {"X-Autosave": "1"} if as_json else {}
        return self.client.post(
            reverse("albums:page_typeset_approve", kwargs={"pk": page.pk}),
            headers=headers,
        )

    def layout_values(self, region):
        """Valores de maquetación guardados, para comprobar que nada cambió."""
        region.refresh_from_db()
        return {name: getattr(region, name) for name in LAYOUT_FIELDS}


class LayoutStyleTests(TypesettingTestCase):
    """CP-89.4 (servidor) — Cambiar fuente, tamaño, alineación, color y caja."""

    def test_each_valid_style_is_saved(self):
        """CP-89.4 — Cada valor válido se guarda y se devuelve recalculado."""
        cases = [
            ({"font_family": "bangers"}, "font_family", "bangers"),
            ({"font_family": "comic-neue-bold"}, "font_family", "comic-neue-bold"),
            ({"font_family": ""}, "font_family", ""),
            ({"font_size": "28"}, "font_size", 28),
            ({"font_size": "auto"}, "font_size", None),
            ({"text_align": "left"}, "text_align", "left"),
            ({"text_align": "right"}, "text_align", "right"),
            ({"text_color": "#ffffff"}, "text_color", "#FFFFFF"),
            ({"x": "50", "y": "70", "width": "150", "height": "90"}, "layout_x", 50),
            ({"x": "60"}, "layout_x", 60),
        ]
        for data, field, expected in cases:
            with self.subTest(data=data):
                response = self.post_layout(self.first, data)
                self.assertEqual(response.status_code, 200)
                self.first.refresh_from_db()
                self.assertEqual(getattr(self.first, field), expected)
                payload = response.json()
                for key in ("x", "y", "width", "height", "font_size", "lines"):
                    self.assertIn(key, payload)
                self.assertIn("fits", payload)

    def test_the_panel_style_of_the_scenario_is_applied(self):
        """CP-89.4 — Bangers, 28 px fijo, izquierda y #FFFFFF; luego automático."""
        response = self.post_layout(
            self.first,
            {
                "font_family": "bangers",
                "font_size": "28",
                "text_align": "left",
                "text_color": "#FFFFFF",
            },
        )
        payload = response.json()
        self.assertEqual(payload["font_family"], "bangers")
        self.assertEqual(payload["font_size"], 28)
        self.assertFalse(payload["is_auto_size"])
        self.assertEqual(payload["text_align"], "left")
        self.assertEqual(payload["text_color"], "#FFFFFF")

        payload = self.post_layout(self.first, {"font_size": ""}).json()
        self.assertTrue(payload["is_auto_size"])
        self.first.refresh_from_db()
        self.assertIsNone(self.first.font_size)

    def test_each_invalid_value_is_rejected_and_nothing_changes(self):
        """CP-89.4 — Cada valor inválido responde 400 con su campo y no guarda."""
        cases = [
            ({"font_family": "comic-sans"}, "font_family"),
            ({"font_size": "7"}, "font_size"),
            ({"font_size": str(MAX_FIXED_FONT_SIZE + 1)}, "font_size"),
            ({"font_size": "grande"}, "font_size"),
            ({"text_align": "justify"}, "text_align"),
            ({"text_color": "#FFF"}, "text_color"),
            ({"text_color": "blanco"}, "text_color"),
            ({"x": "uno"}, "x"),
            ({"width": "10"}, "width"),
            ({"height": "15"}, "height"),
            ({"font_size": "30", "text_color": "rojo"}, "text_color"),
        ]
        before = self.layout_values(self.first)
        for data, field in cases:
            with self.subTest(data=data):
                response = self.post_layout(self.first, data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()["errors"])
                self.assertEqual(self.layout_values(self.first), before)

    def test_a_box_outside_the_image_is_rejected(self):
        """CA-89.3 — La caja no puede salir de los bordes de la imagen."""
        cases = [
            {"x": "-5"},
            {"y": "-1"},
            {"x": "300", "width": "120"},
            {"y": "500", "height": "61"},
        ]
        before = self.layout_values(self.first)
        for data in cases:
            with self.subTest(data=data):
                response = self.post_layout(self.first, data)
                self.assertEqual(response.status_code, 400)
                self.assertIn("box", response.json()["errors"])
                self.assertEqual(self.layout_values(self.first), before)

    def test_a_box_touching_the_edges_is_accepted(self):
        """CA-89.3 — Una caja que llega justo al borde es válida."""
        response = self.post_layout(
            self.first, {"x": "0", "y": "0", "width": "400", "height": "560"}
        )
        self.assertEqual(response.status_code, 200)

    def test_a_fixed_size_that_does_not_fit_is_kept(self):
        """ADR-003 P2 — Un tamaño fijo que no cabe no se reduce: fits=false."""
        payload = self.post_layout(self.first, {"font_size": "200"}).json()
        self.assertEqual(payload["font_size"], 200)
        self.assertFalse(payload["fits"])
        self.first.refresh_from_db()
        self.assertEqual(self.first.font_size, 200)

    def test_a_stale_version_is_a_conflict_and_nothing_changes(self):
        """HU-23 aplicado a HU-89 — Otra pestaña guardó antes: 409 sin pisar."""
        self.post_layout(self.first, {"text_align": "left"})
        before = self.layout_values(self.first)
        response = self.post_layout(self.first, {"text_align": "right"}, version="")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["status"], "conflict")
        self.assertEqual(response.json()["layout"]["text_align"], "left")
        self.assertEqual(self.layout_values(self.first), before)

        response = self.client.post(
            reverse("albums:region_layout_reset", kwargs={"pk": self.first.pk}),
            {"version": ""},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.layout_values(self.first), before)

    def test_get_is_not_allowed(self):
        """Las rutas de maquetación solo aceptan POST."""
        url = reverse("albums:region_layout", kwargs={"pk": self.first.pk})
        self.assertEqual(self.client.get(url).status_code, 405)


class LayoutAlgorithmTests(TypesettingTestCase):
    """CP-89.1 (servidor) — Maquetación automática de partida."""

    def test_default_layout_uses_the_ocr_box_and_the_kind_font(self):
        """CP-89.1 — Caja del OCR, fuente del tipo y tamaño automático."""
        balloon = layout_for_region(self.first)
        narration = layout_for_region(self.second)
        self.assertEqual(
            (balloon["x"], balloon["y"], balloon["width"], balloon["height"]),
            self.BOXES[1],
        )
        self.assertEqual(balloon["font_family"], "comic-neue")
        self.assertEqual(narration["font_family"], "comic-neue-italic")
        self.assertTrue(balloon["is_auto_size"])
        self.assertLessEqual(balloon["font_size"], 72)
        self.assertLessEqual(balloon["font_size"], round(80 * 0.7))
        self.assertTrue(balloon["fits"])
        self.assertEqual(balloon["text_align"], "center")
        self.assertEqual(balloon["text_color"], "#000000")

    def test_the_preview_uses_the_same_layout(self):
        """ADR-003 — La vista previa no tiene un segundo cálculo."""
        self.post_layout(self.first, {"font_family": "bangers", "font_size": "30"})
        response = self.client.get(self.page.get_absolute_url())
        preview = next(
            item
            for item in response.context["preview_regions"]
            if item["region_pk"] == self.first.pk
        )
        self.first.refresh_from_db()
        layout = layout_for_region(self.first)
        self.assertEqual(preview["lines"], layout["lines"])
        self.assertEqual(preview["font_size"], 30)
        self.assertIn("--preview-font-family: Bangers;", preview["style"])
        self.assertIn("--preview-line-ratio:", preview["style"])
        self.assertIn("--preview-padding-ratio:", preview["style"])
        self.assertContains(response, 'data-text-align="center"')


class TranslationEditTests(TypesettingTestCase):
    """CP-89.5 — Editar el texto sobre la imagen reutiliza HU-18."""

    def test_editing_updates_the_translation_and_removes_approval(self):
        """CP-89.5 — Actualiza la traducción y la región vuelve a "Editada"."""
        self.mark_typeset(self.page)
        response = self.client.post(
            self.first.get_translation_url(),
            {
                "text": "¡Hola, mundo entero!",
                "version": timestamp_version(self.first.translated_at),
            },
            headers={"X-Autosave": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            " ".join(response.json()["layout"]["lines"]), "¡Hola, mundo entero!"
        )
        self.first.refresh_from_db()
        self.page.refresh_from_db()
        self.assertEqual(self.first.translation, "¡Hola, mundo entero!")
        self.assertEqual(
            self.first.translation_status, TextRegion.TranslationStatus.EDITED
        )
        self.assertNotEqual(self.page.status, ComicPage.Status.APPROVED)
        self.assertIsNone(self.page.typeset_approved_at)


class LayoutResetTests(TypesettingTestCase):
    """CP-89.6 (servidor) — "Restablecer" vuelve a la caja y al estilo base."""

    def test_reset_restores_the_ocr_box_and_the_default_style(self):
        """CP-89.6 — Caja del OCR, fuente del tipo, automático, centro, negro."""
        self.post_layout(
            self.first,
            {
                "x": "10",
                "y": "10",
                "width": "100",
                "height": "50",
                "font_family": "bangers",
                "font_size": "40",
                "text_align": "right",
                "text_color": "#FF0000",
            },
        )
        response = self.post_reset(self.first)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            (payload["x"], payload["y"], payload["width"], payload["height"]),
            self.BOXES[1],
        )
        self.assertEqual(payload["font_family"], "comic-neue")
        self.assertTrue(payload["is_auto_size"])
        self.first.refresh_from_db()
        self.assertIsNone(self.first.layout_x)
        self.assertIsNone(self.first.layout_width)
        self.assertEqual(self.first.font_family, "")
        self.assertIsNone(self.first.font_size)
        self.assertEqual(self.first.text_align, "center")
        self.assertEqual(self.first.text_color, "#000000")


class TypesetApprovalTests(TypesettingTestCase):
    """CP-89.7 — Aprobar la maquetación de la página (ADR-003, P7)."""

    def test_approving_with_everything_ready(self):
        """CP-89.7 — Con imagen limpia y todo aprobado, queda "Maquetada"."""
        response = self.post_approve(self.page)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "approved")
        self.assertEqual(response.json()["warnings"], [])
        self.page.refresh_from_db()
        self.assertIsNotNone(self.page.typeset_approved_at)
        self.assertTrue(self.page.is_typeset)

    def test_the_grid_shows_the_typeset_chip(self):
        """CP-89.7 — La rejilla del álbum muestra el chip "Maquetada"."""
        response = self.client.get(self.album.get_absolute_url())
        self.assertNotContains(response, "Maquetada")
        self.post_approve(self.page)
        response = self.client.get(self.album.get_absolute_url())
        self.assertContains(response, "Maquetada")

    def test_rejected_without_a_cleaned_image(self):
        """CP-89.7 — Sin imagen limpia no se aprueba y se explica el motivo."""
        ComicPage.objects.filter(pk=self.page.pk).update(cleaned_image="")
        response = self.post_approve(self.page)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Limpia la página", response.json()["message"])
        self.assertIsNone(self.typeset_stamp(self.page))

    def test_rejected_with_translations_not_approved(self):
        """CP-89.7 — Con una traducción sin aprobar, no está disponible."""
        unapprove_translation(self.first)
        response = self.post_approve(self.page)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["message"], "Falta 1 traducción por aprobar.")
        self.assertIsNone(self.typeset_stamp(self.page))

    def test_manual_cleaning_warns_without_blocking(self):
        """ADR-003 P7 — Regiones en "Limpieza manual": aviso, no bloqueo."""
        TextRegion.objects.filter(pk=self.first.pk).update(
            cleaning_status=TextRegion.CleaningStatus.MANUAL
        )
        response = self.post_approve(self.page)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["warnings"]), 1)
        self.assertIn("limpieza manual", response.json()["warnings"][0])
        self.assertIsNotNone(self.typeset_stamp(self.page))

    def test_without_javascript_it_redirects_with_a_message(self):
        """CP-89.7 — Como formulario normal vuelve a la página con un mensaje."""
        response = self.post_approve(self.page, as_json=False)
        target = f"{self.page.get_absolute_url()}?paso=maquetacion"
        self.assertRedirects(response, target, fetch_redirect_response=False)
        response = self.client.get(target)
        self.assertContains(response, "Página maquetada.")

    def test_a_later_change_removes_the_typeset_state(self):
        """CP-89.7 — Cualquier cambio posterior deja de estar "Maquetada"."""
        self.post_approve(self.page)
        self.post_layout(self.second, {"text_color": "#333333"})
        self.assertIsNone(self.typeset_stamp(self.page))

    def test_approving_does_not_clear_itself(self):
        """ADR-003 P1 — Aprobar no dispara el borrado de la propia aprobación."""
        self.post_approve(self.page)
        stamp = self.typeset_stamp(self.page)
        self.assertIsNotNone(stamp)
        self.post_approve(self.page)
        self.assertIsNotNone(self.typeset_stamp(self.page))
        self.page.refresh_from_db()
        self.assertTrue(self.page.is_typeset)


class TypesetInvalidationTests(TypesettingTestCase):
    """ADR-003 P1 — Cada camino que cambia la página borra "Maquetada".

    Una prueba por camino de la lista del Módulo 1: si una función nueva
    toca regiones y olvida clear_typeset_approval(), esta clase lo detecta.
    """

    def fresh_typeset_page(self):
        """Página nueva del álbum, lista y marcada como maquetada."""
        page = self.make_page(self.album)
        regions = self.make_ready_page(page)
        self.mark_typeset(page)
        return page, regions

    def run_path(self, action):
        """Ejecuta un camino sobre una página maquetada y devuelve la página."""
        page, regions = self.fresh_typeset_page()
        self.assertIsNotNone(self.typeset_stamp(page))
        action(page, regions)
        return page

    def path_layout(self, page, regions):
        """Camino 1: guardar un cambio de maquetación."""
        self.post_layout(regions[0], {"text_align": "left"})

    def path_layout_reset(self, page, regions):
        """Camino 2: "Restablecer"."""
        self.post_reset(regions[0])

    def path_edit_form(self, page, regions):
        """Camino 3: editar la traducción desde el formulario actual (HU-18)."""
        self.client.post(regions[0].get_translation_url(), {"text": "Otra"})

    def path_edit_autosave(self, page, regions):
        """Camino 3: autoguardado de la traducción (HU-23)."""
        self.client.post(
            regions[0].get_translation_url(),
            {"text": "Otra", "version": timestamp_version(regions[0].translated_at)},
            headers={"X-Autosave": "1"},
        )

    def path_approve_with_text(self, page, regions):
        """Camino 3: aprobar enviando un texto nuevo (save_posted_translation)."""
        self.client.post(regions[0].get_approve_url(), {"text": "Texto nuevo"})

    def path_correct(self, page, regions):
        """Camino 4: corregir el texto de origen (HU-17)."""
        correct_region(regions[0], "原文修正")

    def path_restore_source(self, page, regions):
        """Camino 4: restaurar el texto del OCR (HU-17)."""
        restore_region(regions[0])

    def path_apply_translations(self, page, regions):
        """Camino 5: la IA guarda una propuesta (HU-16)."""
        TextRegion.objects.filter(pk=regions[0].pk).update(
            translation_status=TextRegion.TranslationStatus.GENERATED
        )
        regions[0].refresh_from_db()
        apply_translations(
            page, regions, [SimpleNamespace(number=1, translation="Propuesta")]
        )

    def path_delete(self, page, regions):
        """Camino 6: eliminar una región (HU-86)."""
        self.client.post(regions[0].get_delete_url())

    def path_restore_deleted(self, page, regions):
        """Camino 7: deshacer la eliminación de una región (HU-86)."""
        self.client.post(regions[0].get_delete_url())
        self.mark_typeset(page)
        self.client.post(reverse("albums:region_restore", args=[regions[0].pk]))

    def path_skip(self, page, regions):
        """Camino 8: marcar "No traducir" (HU-86)."""
        set_translation_skipped(regions[0], True)

    def path_enable(self, page, regions):
        """Camino 8: volver a traducir una región "No traducir" (HU-86)."""
        set_translation_skipped(regions[0], True)
        self.mark_typeset(page)
        set_translation_skipped(regions[0], False)

    def path_manual_region(self, page, regions):
        """Camino 9: añadir una región a mano (HU-85)."""
        detected = DetectedRegion(
            x=2, y=2, width=40, height=20, text="手書き", confidence=0.96
        )
        with mock.patch(
            "albums.manual_regions.get_provider",
            return_value=FakeOcrProvider(regions=[detected]),
        ):
            add_manual_region(page, 10, 420, 120, 80)

    def path_unapprove(self, page, regions):
        """Camino 10: retirar la aprobación de una traducción (HU-19)."""
        unapprove_translation(regions[0])

    def path_leave_approval(self, page, regions):
        """Camino 11: la página sale de "Aprobada"."""
        leave_page_approval(page)

    def path_start_cleaning(self, page, regions):
        """Camino 14: "Limpiar de nuevo"."""
        start_cleaning(page)

    def path_replace_cleaned(self, page, regions):
        """Camino 15: cualquier escritura de la capa limpia."""
        replace_cleaned_image(page, Image.new("RGB", PAGE_SIZE, WHITE))

    def path_restore_cleaning(self, page, regions):
        """Camino 15: restaurar la zona original de una región (HU-88)."""
        self.client.post(regions[0].get_restore_cleaning_url())

    def path_start_processing(self, page, regions):
        """Camino 16: volver a procesar la página."""
        start_processing(page)

    def path_save_regions(self, page, regions):
        """Camino 17: el OCR reemplaza las regiones (y deja la página aprobada)."""
        save_regions(page, [])

    def test_every_path_clears_the_typeset_state(self):
        """ADR-003 P1 — Tras cada camino, typeset_approved_at queda en None."""
        paths = [
            self.path_layout,
            self.path_layout_reset,
            self.path_edit_form,
            self.path_edit_autosave,
            self.path_approve_with_text,
            self.path_correct,
            self.path_restore_source,
            self.path_apply_translations,
            self.path_delete,
            self.path_restore_deleted,
            self.path_skip,
            self.path_enable,
            self.path_manual_region,
            self.path_unapprove,
            self.path_leave_approval,
            self.path_start_cleaning,
            self.path_replace_cleaned,
            self.path_restore_cleaning,
            self.path_start_processing,
            self.path_save_regions,
        ]
        for action in paths:
            with self.subTest(path=action.__name__):
                page = self.run_path(action)
                self.assertIsNone(self.typeset_stamp(page))

    def test_reapproving_an_approved_region_keeps_the_typeset_state(self):
        """ADR-003 P1 — Volver a aprobar sin cambios no desmaqueta la página."""
        page, regions = self.fresh_typeset_page()
        approve_translation(regions[0])
        self.assertIsNotNone(self.typeset_stamp(page))


class RenderPageTests(TypesettingTestCase):
    """CP-89.8 (servidor) — Lo que se ve es lo que se exporta."""

    def cleaned_base(self):
        """Capa limpia de la página como RGB."""
        with (
            self.page.cleaned_image.open("rb") as image_file,
            Image.open(image_file) as source,
        ):
            return source.convert("RGB")

    def expected_text_block(self, layout):
        """Bloque de líneas que describe layout_for_region, en la página."""
        font = load_font(FONTS[layout["font_family"]].path, layout["font_size"])
        padding = layout["padding"]
        content_width = layout["width"] - 2 * padding
        content_height = layout["height"] - 2 * padding
        block_width = max(font.getlength(line) for line in layout["lines"])
        block_height = layout["line_height"] * len(layout["lines"])
        left = layout["x"] + padding + (content_width - block_width) / 2
        top = layout["y"] + padding + (content_height - block_height) / 2
        return left, top, left + block_width, top + block_height

    def test_the_render_keeps_resolution_and_mode(self):
        """CP-89.8 — Misma resolución que la original, en RGB."""
        rendered = render_page(self.page)
        self.assertEqual(rendered.size, PAGE_SIZE)
        self.assertEqual(rendered.mode, "RGB")

    def test_pixels_change_inside_each_box_and_nowhere_else(self):
        """CP-89.8 — Cambian píxeles en cada caja traducida y en ningún otro sitio."""
        rendered = render_page(self.page)
        difference = ImageChops.difference(rendered, self.cleaned_base())
        outside = difference.copy()
        for region in (self.first, self.second):
            layout = layout_for_region(region)
            box = (
                layout["x"],
                layout["y"],
                layout["x"] + layout["width"],
                layout["y"] + layout["height"],
            )
            with self.subTest(region=region.reading_order):
                self.assertIsNotNone(difference.crop(box).getbbox())
            outside.paste((0, 0, 0), box)
        self.assertIsNone(outside.getbbox())

    def test_the_drawn_text_matches_the_layout_within_two_pixels(self):
        """CP-89.8 — La tinta dibujada coincide con el bloque de líneas ±2 px."""
        rendered = render_page(self.page)
        difference = ImageChops.difference(rendered, self.cleaned_base())
        for region in (self.first, self.second):
            layout = layout_for_region(region)
            left, top, right, bottom = self.expected_text_block(layout)
            ink = difference.crop(
                (
                    layout["x"],
                    layout["y"],
                    layout["x"] + layout["width"],
                    layout["y"] + layout["height"],
                )
            ).getbbox()
            ink_left = layout["x"] + ink[0]
            ink_top = layout["y"] + ink[1]
            ink_right = layout["x"] + ink[2]
            ink_bottom = layout["y"] + ink[3]
            with self.subTest(region=region.reading_order):
                self.assertGreaterEqual(ink_left, left - 2)
                self.assertGreaterEqual(ink_top, top - 2)
                self.assertLessEqual(ink_right, right + 2)
                self.assertLessEqual(ink_bottom, bottom + 2)
                ink_center = (ink_left + ink_right) / 2
                self.assertAlmostEqual(ink_center, (left + right) / 2, delta=2)

    def test_the_stored_style_is_drawn(self):
        """CP-89.8 — El color y la caja guardados son los que se dibujan."""
        self.post_layout(
            self.first,
            {
                "x": "20",
                "y": "200",
                "width": "200",
                "height": "60",
                "text_color": "#FF0000",
                "text_align": "left",
            },
        )
        rendered = render_page(self.page)
        drawn = rendered.crop((20, 200, 220, 260))
        colors = {color for _count, color in drawn.getcolors(maxcolors=100000)}
        self.assertIn((255, 0, 0), colors)
        self.assertEqual(rendered.getpixel((self.BOXES[1][0] + 20, 100)), WHITE)

    def test_regions_without_an_approved_translation_keep_the_original(self):
        """ADR-003 P6 — Sin aprobar, "No traducir" o aprobada vacía: original."""
        cases = {
            "sin aprobar": {
                "translation_status": TextRegion.TranslationStatus.EDITED,
            },
            "no traducir": {"skip_translation": True},
            "aprobada vacía": {"translation": ""},
        }
        x, y, width, height = self.BOXES[1]
        center = (x + width // 2, y + height // 2)
        for name, changes in cases.items():
            with self.subTest(case=name):
                TextRegion.objects.filter(pk=self.first.pk).update(**changes)
                rendered = render_page(self.page)
                self.assertEqual(rendered.getpixel(center), INK)
                TextRegion.objects.filter(pk=self.first.pk).update(
                    translation="¡Hola, mundo!",
                    translation_status=TextRegion.TranslationStatus.APPROVED,
                    skip_translation=False,
                )

    def test_without_a_cleaned_image_it_starts_from_the_original(self):
        """HU-90 — Sin capa limpia, la base es la imagen original."""
        ComicPage.objects.filter(pk=self.page.pk).update(cleaned_image="")
        self.page.refresh_from_db()
        rendered = render_page(self.page)
        self.assertEqual(rendered.size, PAGE_SIZE)
        x, y, width, height = self.BOXES[2]
        self.assertEqual(rendered.getpixel((x + 12, y + 12)), INK)


class ForeignResourceTests(TypesettingTestCase):
    """CP-89.9 — Región y página de otra cuenta: 404 y nada cambia."""

    def setUp(self):
        """Prepara también la página ajena con sus regiones."""
        super().setUp()
        self.foreign_regions = self.make_ready_page(self.foreign_page)

    def test_every_endpoint_answers_404_without_changes(self):
        """CP-89.9 — Maquetar, restablecer, editar y aprobar algo ajeno → 404."""
        region = self.foreign_regions[0]
        before = self.layout_values(region)
        requests = {
            "maquetación": (
                reverse("albums:region_layout", kwargs={"pk": region.pk}),
                {"text_align": "left", "version": ""},
            ),
            "restablecer": (
                reverse("albums:region_layout_reset", kwargs={"pk": region.pk}),
                {"version": ""},
            ),
            "texto": (region.get_translation_url(), {"text": "Intrusión"}),
            "aprobar página": (
                reverse(
                    "albums:page_typeset_approve", kwargs={"pk": self.foreign_page.pk}
                ),
                {},
            ),
        }
        for name, (url, data) in requests.items():
            with self.subTest(endpoint=name):
                response = self.client.post(url, data, headers={"X-Autosave": "1"})
                self.assertEqual(response.status_code, 404)
        self.assertEqual(self.layout_values(region), before)
        region.refresh_from_db()
        self.assertEqual(region.translation, "¡Hola, mundo!")
        self.assertIsNone(self.typeset_stamp(self.foreign_page))
