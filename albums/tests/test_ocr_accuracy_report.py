"""Pruebas del comando de medición de precisión del OCR (HU-13, CA-13.4)."""

import io
import json
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings
from PIL import Image

from albums.ocr.base import DetectedRegion
from albums.ocr.fake import FakeOcrProvider

COMMAND_MODULE = "albums.management.commands.ocr_accuracy_report"

# Dos globos en la misma fila de una página de 400 x 560. En japonés se leen
# de derecha a izquierda: primero "右側", después "左側".
LEFT = DetectedRegion(40, 40, 120, 80, "左側", 0.9)
RIGHT = DetectedRegion(260, 50, 120, 80, "右 側", 0.9)


def write_page(folder, name, expected):
    """Guarda una página de prueba y su texto esperado."""
    folder.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (400, 560), "white").save(folder / f"{name}.png")
    (folder / f"{name}.json").write_text(
        json.dumps({"regions": expected}, ensure_ascii=False), encoding="utf-8"
    )


class AccuracyReportTests(SimpleTestCase):
    """CP-13.4 — Informe de precisión por idioma sobre el juego de prueba."""

    def setUp(self):
        """Crea una carpeta temporal para el juego de prueba."""
        self.folder = Path(tempfile.mkdtemp(prefix="panelingo-ocr-set-"))

    def tearDown(self):
        """Borra el juego de prueba temporal."""
        shutil.rmtree(self.folder, ignore_errors=True)

    def run_report(self, provider, **options):
        """Ejecuta el comando con el proveedor indicado y devuelve su salida."""
        output = io.StringIO()
        with mock.patch(f"{COMMAND_MODULE}.get_provider", return_value=provider):
            call_command(
                "ocr_accuracy_report", str(self.folder), stdout=output, **options
            )
        return output.getvalue()

    def test_text_and_order_are_measured_per_language(self):
        """CP-13.4 — Cuenta las regiones con su texto exacto y en su orden."""
        write_page(self.folder / "ja", "pagina-01", ["右側", "左側"])

        report = self.run_report(FakeOcrProvider(regions=[LEFT, RIGHT]))

        # Los espacios no cuentan y el orden de lectura es el japonés.
        self.assertIn("| ja | 1 | 2 | 2 | 100.0 % |", report)

    def test_wrong_order_lowers_the_accuracy(self):
        """CP-13.4 — Flujo alternativo: el texto en desorden no cuenta."""
        write_page(self.folder / "ja", "pagina-01", ["左側", "右側"])

        report = self.run_report(FakeOcrProvider(regions=[LEFT, RIGHT]))

        self.assertIn("| ja | 1 | 2 | 0 | 0.0 % |", report)

    @override_settings(OCR_ACCURACY_THRESHOLDS={"ja": 90})
    def test_the_result_is_compared_with_the_agreed_threshold(self):
        """CP-13.4 — Con umbral acordado, el informe dice si se cumple."""
        write_page(self.folder / "ja", "pagina-01", ["右側", "左側"])

        report = self.run_report(FakeOcrProvider(regions=[RIGHT]))

        self.assertIn("| 50.0 % |", report)
        self.assertIn("| 90 % | No cumple |", report)

    def test_without_threshold_the_report_says_so(self):
        """CP-13.4 — Mientras el PO no fije el umbral, se indica."""
        write_page(self.folder / "ko", "pagina-01", ["안녕"])

        report = self.run_report(
            FakeOcrProvider(regions=[DetectedRegion(10, 10, 50, 20, "안녕", 0.9)])
        )

        self.assertIn("Umbral por definir", report)

    def test_failed_pages_are_listed(self):
        """CP-13.4 — Una página que el proveedor no procesa queda anotada."""
        write_page(self.folder / "ja", "pagina-01", ["右側"])

        report = self.run_report(FakeOcrProvider(error="Servicio caído"))

        self.assertIn("pagina-01.png: Servicio caído", report)

    def test_the_report_can_be_saved_as_evidence(self):
        """CP-13.4 — El informe se guarda en Markdown para la evidencia."""
        write_page(self.folder / "ja", "pagina-01", ["右側"])
        output_path = self.folder / "informe.md"

        self.run_report(FakeOcrProvider(regions=[RIGHT]), output=str(output_path))

        self.assertIn("Informe de precisión del OCR", output_path.read_text("utf-8"))

    def test_a_missing_folder_is_an_error(self):
        """CP-13.4 — Flujo alternativo: carpeta inexistente."""
        with self.assertRaises(CommandError):
            call_command("ocr_accuracy_report", str(self.folder / "no-existe"))
