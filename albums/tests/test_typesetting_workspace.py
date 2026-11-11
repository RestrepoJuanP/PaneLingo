"""Pruebas del marcado del editor de maquetación (HU-89, parte B).

El cliente de Django no ejecuta JavaScript: aquí se comprueba lo que el
servidor entrega al navegador. CP-89.2, CP-89.3, la parte de teclado de
CP-89.6 y la parte visual de CP-89.8 son verificación manual (ver el PR).
"""

import re
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.utils.html import escape

from albums.models import ComicPage, TextRegion
from albums.tests.test_typesetting_editor import TypesettingTestCase
from albums.translation_review import unapprove_translation
from albums.typesetting import (
    FONTS,
    MAX_FIXED_FONT_SIZE,
    MAX_FONT_SIZE,
    MIN_BOX_SIZE,
    MIN_FONT_SIZE,
    layout_for_region,
)
from albums.views import timestamp_version

EDITOR_SCRIPT = Path(settings.BASE_DIR) / "static" / "js" / "typesetting.js"


class TypesettingWorkspaceTestCase(TypesettingTestCase):
    """Base: abre la pestaña Maquetación de la página propia."""

    def open_step(self, page=None):
        """Pide la página con ?paso=maquetacion."""
        page = page or self.page
        return self.client.get(f"{page.get_absolute_url()}?paso=maquetacion")


class InitialLayoutTests(TypesettingWorkspaceTestCase):
    """CP-89.1 — Al abrir la pestaña, cada texto llega ajustado del servidor."""

    def test_each_region_carries_the_server_lines_and_size(self):
        """CP-89.1 — Líneas, tamaño y estilo de layout_for_region en el marcado."""
        response = self.open_step()
        self.assertContains(response, "data-typesetting-editor")
        for region in (self.first, self.second):
            layout = layout_for_region(region)
            with self.subTest(region=region.reading_order):
                lines = "".join(
                    f"<span>{escape(line)}</span>" for line in layout["lines"]
                )
                self.assertContains(response, lines)
                self.assertContains(response, f'data-font-size="{layout["font_size"]}"')
                self.assertContains(response, f'data-x="{layout["x"]}"')
                self.assertContains(response, f'data-width="{layout["width"]}"')
        item = next(
            item
            for item in response.context["typeset_items"]
            if item["region"].pk == self.first.pk
        )
        self.assertIn("--preview-line-ratio:", item["preview"]["style"])
        self.assertContains(response, escape(item["preview"]["style"]))

    def test_the_editor_starts_from_the_cleaned_image(self):
        """CA-89.1 — La base del editor es la imagen limpia."""
        response = self.open_step()
        self.assertContains(response, self.page.get_cleaned_image_url())

    def test_skipped_regions_are_not_editable_boxes(self):
        """ADR-003 P6 — Las regiones "No traducir" no se maquetan."""
        TextRegion.objects.filter(pk=self.second.pk).update(skip_translation=True)
        response = self.open_step()
        self.assertEqual(len(response.context["typeset_items"]), 1)
        self.assertNotContains(response, f'data-number="{self.second.reading_order}"')

    def test_regions_without_approval_announce_the_export(self):
        """ADR-003 P6 — Sin aprobar: aviso de que se exportará el original."""
        unapprove_translation(self.first)
        response = self.open_step()
        self.assertContains(
            response, "Sin aprobar: se exportará con el texto original."
        )


class StepTabsTests(TypesettingWorkspaceTestCase):
    """Pestañas "Detección y traducción" y "Maquetación" (?paso=)."""

    def test_detection_is_the_default_step(self):
        """Sin ?paso=, la pestaña activa es Detección y traducción."""
        response = self.client.get(self.page.get_absolute_url())
        self.assertContains(response, 'aria-label="Pasos de la página"')
        self.assertRegex(
            response.content.decode(),
            r'aria-current="page"\s*>Detección y traducción</a>',
        )
        self.assertContains(response, "?paso=maquetacion")
        self.assertNotContains(response, "data-typesetting-editor")
        self.assertNotContains(response, "js/typesetting.js")

    def test_the_step_survives_a_reload(self):
        """?paso=maquetacion abre directamente la maquetación."""
        response = self.open_step()
        content = response.content.decode()
        self.assertRegex(content, r'aria-current="page"\s*>Maquetación</a>')
        self.assertContains(response, "js/typesetting.js")
        self.assertNotContains(response, "data-region-workspace")

    def test_the_pager_keeps_the_step(self):
        """Pasar de página desde la maquetación conserva ?paso=."""
        following = self.make_page(self.album)
        response = self.open_step()
        self.assertContains(
            response, f'href="{following.get_absolute_url()}?paso=maquetacion"'
        )

    def test_the_tab_is_disabled_without_a_cleaned_image(self):
        """Sin imagen limpia, la pestaña se deshabilita con su motivo."""
        ComicPage.objects.filter(pk=self.page.pk).update(cleaned_image="")
        response = self.open_step()
        self.assertContains(response, 'aria-disabled="true"')
        self.assertContains(response, "Limpia la página para maquetarla.")
        self.assertNotContains(response, "data-typesetting-editor")

    def test_the_tab_is_disabled_without_regions(self):
        """Sin regiones de texto, la pestaña se deshabilita con su motivo."""
        self.page.regions.all().delete()
        response = self.open_step()
        self.assertContains(response, "Esta página no tiene regiones de texto.")
        self.assertNotContains(response, "data-typesetting-editor")


class EditorMarkupTests(TypesettingWorkspaceTestCase):
    """Marcado del editor: URLs, versiones, nombres accesibles y límites."""

    def test_each_box_carries_urls_versions_and_an_accessible_name(self):
        """CA-89.2 — Caja enfocable, role="button" y "Región N, texto: …"."""
        self.post_layout(self.first, {"text_align": "left"})
        self.first.refresh_from_db()
        response = self.open_step()
        self.assertContains(response, 'role="button"', count=2)
        self.assertContains(response, 'aria-label="Región 1, texto: ¡Hola, mundo!"')
        self.assertContains(
            response, f'data-layout-url="{self.first.get_layout_url()}"'
        )
        self.assertContains(
            response, f'data-reset-url="{self.first.get_layout_reset_url()}"'
        )
        self.assertContains(
            response, f'data-translation-url="{self.first.get_translation_url()}"'
        )
        self.assertContains(
            response,
            f'data-layout-version="{timestamp_version(self.first.layout_updated_at)}"',
        )
        self.assertContains(
            response,
            "data-translation-version="
            f'"{timestamp_version(self.first.translated_at)}"',
        )
        self.assertContains(response, 'data-text-align="left"')

    def test_fonts_come_from_the_registry(self):
        """BUG-043 — Las fuentes del panel salen del registro del servidor."""
        response = self.open_step()
        self.assertContains(response, 'name="font_family"', count=len(FONTS) + 1)
        for value in FONTS:
            with self.subTest(font=value):
                self.assertContains(response, f'value="{value}"')

    def test_limits_come_from_the_server(self):
        """BUG-043 — Tamaños, caja mínima y formato del color los emite el servidor."""
        response = self.open_step()
        self.assertContains(response, f'min="{MIN_FONT_SIZE}"')
        self.assertContains(response, f'max="{MAX_FIXED_FONT_SIZE}"')
        self.assertContains(response, f'data-min-box="{MIN_BOX_SIZE}"')
        self.assertContains(response, 'pattern="#[0-9A-Fa-f]{6}"')

    def test_changing_a_limit_changes_the_markup(self):
        """BUG-043 — Cambiar el límite en el servidor cambia lo que ve el navegador."""
        with (
            mock.patch("albums.typesetting.MAX_FIXED_FONT_SIZE", 150),
            mock.patch("albums.typesetting.MIN_BOX_SIZE", 24),
        ):
            response = self.open_step()
        self.assertContains(response, 'max="150"')
        self.assertContains(response, 'data-min-box="24"')

    def test_approve_is_disabled_with_its_reason(self):
        """CA-89.7 — Sin todas las traducciones aprobadas, deshabilitado y por qué."""
        unapprove_translation(self.first)
        response = self.open_step()
        content = response.content.decode()
        self.assertRegex(content, r"data-ts-approve\s[^>]*disabled")
        self.assertContains(response, "Falta 1 traducción por aprobar.")
        self.assertContains(response, 'aria-describedby="ts-approve-reason"')

    def test_an_approved_page_says_so_in_text(self):
        """CA-89.7 — Ya aprobada: "Página maquetada", deshabilitado, sin símbolos."""
        self.post_approve(self.page)
        response = self.open_step()
        content = response.content.decode()
        self.assertRegex(content, r"disabled\s*>Página maquetada</button>")
        self.assertContains(response, "Maquetada")

    def test_requirements_are_listed_as_text(self):
        """ADR-003 P7 — Los requisitos se dicen con texto, no solo con color."""
        TextRegion.objects.filter(pk=self.first.pk).update(
            cleaning_status=TextRegion.CleaningStatus.MANUAL
        )
        response = self.open_step()
        self.assertContains(response, "Imagen limpia")
        self.assertContains(response, "2 de 2 traducciones aprobadas")
        self.assertContains(response, "1 región necesita limpieza manual")

    def test_layout_responses_carry_the_page_status(self):
        """CA-89.7 — Tras un cambio, el servidor dice cómo queda "Aprobar página"."""
        self.post_approve(self.page)
        payload = self.post_layout(self.first, {"text_color": "#222222"}).json()
        self.assertFalse(payload["page"]["is_typeset"])
        self.assertEqual(payload["page"]["blocker"], "")
        self.assertIn("export_notice", payload["preview"])


class WithoutJavascriptTests(TypesettingWorkspaceTestCase):
    """Paso 3 — Qué queda disponible sin JavaScript."""

    def test_editor_only_controls_start_hidden(self):
        """Panel, "Deshacer" y "Textos de la página" solo existen con JS."""
        content = self.open_step().content.decode()
        self.assertRegex(content, r"data-ts-undo data-ts-js-only hidden")
        hidden_panel = re.search(
            r'<div class="ts-editor-panel" data-ts-js-only hidden>(.*?)</ul>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(hidden_panel)
        self.assertIn("Textos de la página", hidden_panel.group(1))
        self.assertIn("data-ts-props", hidden_panel.group(1))

    def test_the_note_and_the_approve_form_work_without_javascript(self):
        """Sin JS: la nota visible y "Aprobar página" como formulario con CSRF."""
        response = self.open_step()
        self.assertContains(
            response,
            "Para mover y cambiar el estilo de los textos hace falta JavaScript.",
        )
        self.assertContains(response, f'action="{self.page.get_typeset_approve_url()}"')
        self.assertContains(response, "csrfmiddlewaretoken")


class EditorScriptTests(TypesettingWorkspaceTestCase):
    """El JavaScript no escribe fuentes ni límites a mano (patrón BUG-043)."""

    def script(self):
        """Contenido de static/js/typesetting.js."""
        return EDITOR_SCRIPT.read_text(encoding="utf-8")

    def test_the_script_has_no_font_list(self):
        """BUG-043 — Ninguna fuente del registro aparece en el JavaScript."""
        script = self.script()
        for value in FONTS:
            with self.subTest(font=value):
                self.assertNotIn(value, script)
        for name in ("Comic Neue", "Bangers"):
            with self.subTest(font=name):
                self.assertNotIn(name, script)

    def test_the_script_has_no_numeric_limits(self):
        """BUG-043 — Ni 8, ni 72, ni 200, ni la caja mínima escritos a mano."""
        script = self.script()
        limits = {MIN_FONT_SIZE, MAX_FONT_SIZE, MAX_FIXED_FONT_SIZE, MIN_BOX_SIZE}
        for limit in limits:
            with self.subTest(limit=limit):
                self.assertIsNone(
                    re.search(rf"(?<![\w.#-]){limit}(?![\w.])", script),
                    f"{limit} aparece escrito en typesetting.js",
                )

    def test_the_script_does_not_compute_lines(self):
        """ADR-003 — El navegador no mide texto: pinta lo que dice el servidor."""
        script = self.script()
        for forbidden in ("measureText", "getContext", "fit_text", "wrap"):
            with self.subTest(term=forbidden):
                self.assertNotIn(forbidden, script)
