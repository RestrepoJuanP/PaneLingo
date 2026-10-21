"""Mide la precisión del OCR sobre un juego de páginas de prueba (HU-13, CA-13.4).

Uso:
    python manage.py ocr_accuracy_report <carpeta> [--output informe.md]

La carpeta tiene una subcarpeta por idioma de origen, con el código del
catálogo (ja, ko, zh-hans, en…). Cada página es una imagen acompañada de un
JSON con el mismo nombre y el texto esperado de cada región, en orden de
lectura:

    juego-de-prueba/ja/pagina-01.png
    juego-de-prueba/ja/pagina-01.json   {"regions": ["こんにちは", "元気ですか"]}

Una región cuenta como correcta si el OCR devolvió exactamente su texto (sin
tener en cuenta espacios ni saltos de línea) y en su posición de lectura:
es lo que pide CA-13.4, "conserva el texto y el orden de sus caracteres".
Usa el proveedor configurado en OCR_PROVIDER y las mismas reglas de
agrupación y orden que el procesamiento real.
"""

import json
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from albums.ocr import OcrProviderError, get_provider
from albums.ocr.layout import arrange_regions

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")


def compact(text):
    """Quita espacios y saltos de línea, que el OCR reparte a su manera."""
    return "".join(text.split())


@dataclass
class LanguageResult:
    """Resultado acumulado de las páginas de un idioma."""

    language_code: str
    pages: int = 0
    failed_pages: list = field(default_factory=list)
    expected_regions: int = 0
    exact_regions: int = 0
    similarity_sum: float = 0.0

    @property
    def accuracy(self):
        """Porcentaje de regiones con su texto exacto y en su orden."""
        if not self.expected_regions:
            return 0.0
        return self.exact_regions / self.expected_regions * 100

    @property
    def similarity(self):
        """Parecido medio de caracteres por región, de 0 a 100."""
        if not self.expected_regions:
            return 0.0
        return self.similarity_sum / self.expected_regions * 100


def load_expected(json_path):
    """Lee la lista de textos esperados de una página."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return [compact(text) for text in data["regions"]]


def recognised_texts(provider, image_path, language_code):
    """Devuelve el texto de cada región reconocida, en orden de lectura."""
    image_bytes = image_path.read_bytes()
    with Image.open(image_path) as image:
        width, height = image.size
    detected = provider.detect(image_bytes)
    regions = arrange_regions(detected, width, height, language_code)
    return [compact(region.text) for region in regions]


def score_page(result, expected, recognised):
    """Suma al resultado del idioma la comparación de una página."""
    result.pages += 1
    result.expected_regions += len(expected)
    for position, expected_text in enumerate(expected):
        actual = recognised[position] if position < len(recognised) else ""
        if actual == expected_text:
            result.exact_regions += 1
        result.similarity_sum += SequenceMatcher(None, expected_text, actual).ratio()


def evaluate_language(provider, folder, language_code):
    """Procesa todas las páginas con texto esperado de un idioma."""
    result = LanguageResult(language_code)
    for image_path in sorted(folder.iterdir()):
        expected_path = image_path.with_suffix(".json")
        if image_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if not expected_path.exists():
            continue
        try:
            recognised = recognised_texts(provider, image_path, language_code)
        except OcrProviderError as error:
            result.failed_pages.append(f"{image_path.name}: {error}")
            continue
        score_page(result, load_expected(expected_path), recognised)
    return result


def verdict(result, threshold):
    """Devuelve si el idioma alcanza el umbral acordado con el PO."""
    if threshold is None:
        return "Umbral por definir"
    return "Cumple" if result.accuracy >= threshold else "No cumple"


def render_report(results, thresholds):
    """Construye el informe en Markdown, listo para la evidencia."""
    lines = [
        "# Informe de precisión del OCR (CA-13.4)",
        "",
        f"Proveedor: `{settings.OCR_PROVIDER}`",
        "",
        "| Idioma | Páginas | Regiones esperadas | Exactas y en orden "
        "| Precisión | Parecido de caracteres | Umbral | Resultado |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        threshold = thresholds.get(result.language_code)
        shown_threshold = "—" if threshold is None else f"{threshold} %"
        lines.append(
            f"| {result.language_code} | {result.pages} "
            f"| {result.expected_regions} | {result.exact_regions} "
            f"| {result.accuracy:.1f} % | {result.similarity:.1f} % "
            f"| {shown_threshold} | {verdict(result, threshold)} |"
        )
    failures = [item for result in results for item in result.failed_pages]
    if failures:
        lines += ["", "## Páginas que no se pudieron procesar", ""]
        lines += [f"- {failure}" for failure in failures]
    return "\n".join(lines) + "\n"


class Command(BaseCommand):
    """Genera el informe de precisión del OCR por idioma (CA-13.4)."""

    help = "Mide la precisión del OCR sobre un juego de páginas de prueba."

    def add_arguments(self, parser):
        """Declara la carpeta del juego de prueba y el archivo de salida."""
        parser.add_argument("folder", help="Carpeta con una subcarpeta por idioma.")
        parser.add_argument(
            "--output", help="Guarda además el informe en este archivo Markdown."
        )

    def handle(self, *args, **options):
        """Recorre los idiomas, mide cada uno e imprime el informe."""
        folder = Path(options["folder"])
        if not folder.is_dir():
            raise CommandError(f"No existe la carpeta {folder}.")
        language_folders = sorted(path for path in folder.iterdir() if path.is_dir())
        if not language_folders:
            raise CommandError("La carpeta no tiene subcarpetas por idioma.")

        provider = get_provider()
        results = [
            evaluate_language(provider, path, path.name) for path in language_folders
        ]
        report = render_report(results, settings.OCR_ACCURACY_THRESHOLDS)

        if options["output"]:
            Path(options["output"]).write_text(report, encoding="utf-8")
        self.stdout.write(report)
