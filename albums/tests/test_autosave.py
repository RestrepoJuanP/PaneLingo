"""Pruebas del autoguardado de trabajo (HU-23)."""

from pathlib import Path

from django.conf import settings

from albums.models import TextRegion
from albums.tests.test_translation_review import ReviewTestCase
from albums.views import timestamp_version

AUTOSAVE_HEADERS = {
    "HTTP_ACCEPT": "application/json",
    "HTTP_X_AUTOSAVE": "1",
}


class AutosaveTestCase(ReviewTestCase):
    """Base para guardar como lo hace el navegador, sin redirecciones."""

    def autosave(self, region, url, text, version):
        """Envía texto y versión al endpoint de autoguardado indicado."""
        return self.client.post(
            url,
            {"text": text, "version": version},
            **AUTOSAVE_HEADERS,
        )


class AutosaveWorkTests(AutosaveTestCase):
    """CP-23.1 — Autoguardar después de una pausa o al cambiar de región."""

    def test_source_correction_is_saved_and_returns_its_time(self):
        """CP-23.1 — La corrección queda guardada y confirma hora y versión."""
        response = self.autosave(
            self.first,
            self.first.get_correct_url(),
            "Texto corregido",
            timestamp_version(self.first.corrected_at),
        )

        self.first.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.first.corrected_text, "Texto corregido")
        self.assertTrue(response.json()["message"].startswith("Guardado · "))
        self.assertEqual(
            response.json()["version"], timestamp_version(self.first.corrected_at)
        )

    def test_translation_is_saved_without_touching_another_region(self):
        """CP-23.1 — Cambiar de región conserva el texto en la región correcta."""
        second_translation = self.second.translation

        response = self.autosave(
            self.first,
            self.first.get_translation_url(),
            "¡Hola desde el autoguardado!",
            timestamp_version(self.first.translated_at),
        )

        self.reload_regions()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.first.translation, "¡Hola desde el autoguardado!")
        self.assertEqual(self.second.translation, second_translation)

    def test_workspace_exposes_autosave_controls_and_versions(self):
        """CP-23.1 — Los campos muestran estado accesible y control de reintento."""
        response = self.workspace()

        self.assertContains(response, "data-autosave-kind", count=4)
        self.assertContains(response, "data-autosave-version", count=4)
        self.assertContains(
            response,
            'class="autosave" aria-live="polite"',
            count=4,
        )
        self.assertContains(response, "data-autosave-retry", count=4)


class ConnectionFailureTests(AutosaveTestCase):
    """CP-23.2 — Error de conexión y recuperación."""

    def test_client_keeps_retry_and_online_recovery_behaviour(self):
        """CP-23.2 — Se informa el fallo y se reintenta al volver la conexión."""
        script = Path(settings.BASE_DIR, "static", "js", "app.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("var AUTOSAVE_DELAY_MS = 2000", script)
        self.assertIn('showState(state, "No se pudo guardar."', script)
        self.assertIn('window.addEventListener("online"', script)
        self.assertIn('retry.addEventListener("click"', script)


class PendingChangesTests(AutosaveTestCase):
    """CP-23.3 — Advertir antes de cerrar con cambios pendientes."""

    def test_client_warns_until_the_saved_value_becomes_the_default(self):
        """CP-23.3 — Solo un guardado exitoso desactiva el aviso de salida."""
        script = Path(settings.BASE_DIR, "static", "js", "app.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('window.addEventListener("beforeunload"', script)
        self.assertIn("field.value !== field.defaultValue", script)
        self.assertIn("state.field.defaultValue = sentText", script)


class AutosaveAssociationTests(AutosaveTestCase):
    """CP-23.4 — Asociar el cambio con usuario, álbum, página y región."""

    def test_foreign_region_is_not_found_by_autosave(self):
        """CP-23.4 — Una región de otra cuenta responde 404 y no cambia."""
        foreign = TextRegion.objects.create(
            page=self.foreign_page,
            reading_order=1,
            x=0,
            y=0,
            width=10,
            height=10,
            source_text="Texto ajeno",
        )

        response = self.autosave(
            foreign,
            foreign.get_correct_url(),
            "Intento de cambio",
            "",
        )

        foreign.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertFalse(foreign.is_corrected)
        self.assertEqual(foreign.corrected_text, "")


class ConcurrentAutosaveTests(AutosaveTestCase):
    """CP-23.5 — Dos pestañas editan la misma región."""

    def test_second_source_save_with_stale_version_does_not_overwrite(self):
        """CP-23.5 — La segunda pestaña conserva ambos textos y avisa conflicto."""
        initial_version = timestamp_version(self.first.corrected_at)
        first_response = self.autosave(
            self.first,
            self.first.get_correct_url(),
            "Versión de la primera pestaña",
            initial_version,
        )

        second_response = self.autosave(
            self.first,
            self.first.get_correct_url(),
            "Versión local de la segunda pestaña",
            initial_version,
        )

        self.first.refresh_from_db()
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(second_response.json()["status"], "conflict")
        self.assertIn("otra pestaña", second_response.json()["message"])
        self.assertEqual(
            second_response.json()["saved_text"],
            "Versión de la primera pestaña",
        )
        self.assertEqual(self.first.corrected_text, "Versión de la primera pestaña")

    def test_second_translation_save_with_stale_version_does_not_overwrite(self):
        """CP-23.5 — El conflicto también protege la traducción editada."""
        initial_version = timestamp_version(self.first.translated_at)
        first_response = self.autosave(
            self.first,
            self.first.get_translation_url(),
            "Traducción de la primera pestaña",
            initial_version,
        )

        second_response = self.autosave(
            self.first,
            self.first.get_translation_url(),
            "Traducción de la segunda pestaña",
            initial_version,
        )

        self.first.refresh_from_db()
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(
            self.first.translation,
            "Traducción de la primera pestaña",
        )
