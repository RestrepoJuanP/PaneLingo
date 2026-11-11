# Sprint 3 — Reporte de pruebas de software

Fecha de ejecución: **10 de noviembre de 2026** (primera versión: 9 de
noviembre de 2026, sobre `main` en `99113ef`, con 555 pruebas)

Versión base: rama `chore/ep08-verification-fixes`, que contiene EP-08
completa (HU-85 a HU-90), BUG-096 y las correcciones de la verificación
final, apilada sobre `main` en `8eb3323`

Entorno: Python 3.12.10, Django 5.2 y SQLite de prueba

## 1. Objetivo

Verificar que las historias del Sprint 3 cumplen sus criterios de aceptación,
que cada caso de prueba tiene cobertura automática y que los cambios conservan
el comportamiento entregado en los sprints anteriores.

## 2. Alcance

Este reporte cubre:

- 13 historias de usuario del Sprint 3: las siete del flujo principal
  (HU-20, HU-22 a HU-25, HU-27 y HU-28) y seis de la épica EP-08 Edición de
  imagen (HU-85 a HU-90). HU-91 se descartó tras su *spike* y no tiene casos
  de prueba ([ADR-003, P4](adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91)).
- 74 casos de prueba funcionales: 30 del flujo principal y 44 de EP-08.
- Seguridad por autenticación, aislamiento de propietario y respuestas 404.
- Accesibilidad incluida en los contratos de plantillas y componentes.
- Regresiones de los seis bugs corregidos antes del cierre.
- Suite completa de Django, cobertura, análisis estático, formato y
  dependencias.

Las pruebas de usabilidad con participantes pertenecen a un entregable
separado. La suite automática no sustituye sus tiempos, errores, SEQ, SUS ni
observaciones cualitativas.

## 3. Estrategia

| Nivel | Herramienta | Propósito |
|---|---|---|
| Modelo y servicio | Django Test Framework | Verificar persistencia, estados, archivos y reglas de negocio. |
| Vista e integración | Django test client | Verificar rutas, permisos, formularios, mensajes y respuestas. |
| Presentación | Respuestas HTML y contratos JS | Verificar contenido, atributos accesibles y comportamiento configurado en JavaScript vanilla. |
| Documento exportado | `python-docx` | Abrir el DOCX generado y comprobar su estructura y contenido. |
| Imagen generada | Pillow y `zipfile` | Abrir el ZIP y cada PNG, y comprobar nombres, orden, resolución, modo de color y píxeles. |
| Calidad estática | Ruff y Black | Mantener convenciones, imports, complejidad y formato. |
| Seguridad de dependencias | `pip-audit` | Detectar vulnerabilidades conocidas en dependencias de ejecución. |
| Integración continua | GitHub Actions | Repetir las verificaciones en cada PR y push a `main`. |

Los proveedores de OCR y traducción se simulan durante las pruebas. De esta
forma la suite es determinista y no transmite páginas, credenciales ni datos a
servicios externos. Las imágenes de prueba de EP-08 son sintéticas y se
generan en cada prueba.

La interacción con ratón y teclado del editor de maquetación (HU-89) ocurre
en JavaScript, que el cliente de pruebas no ejecuta. Esas partes se
verifican a mano con el procedimiento descrito en
[CP de HU-89](WIKI_SPRINT_3_CP_HU-89.md#resultado-de-la-ejecución-manual);
a la fecha no consta ninguna ejecución manual en el repositorio.

## 4. Trazabilidad HU → CA → CP → prueba

### HU-20 — Eliminar álbum

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-20.1 | CP-20.1 | `AlbumDeleteTests::test_confirmation_identifies_the_album_and_its_pages` y `test_detail_offers_an_accessible_confirmation_modal` | Cubierto |
| CA-20.2 | CP-20.2 | `AlbumDeleteTests::test_confirming_deletes_the_album_pages_regions_and_files` | Cubierto |
| CA-20.3 | CP-20.3 | `AlbumDeleteTests::test_canceling_keeps_the_album_and_returns_to_the_trigger` | Cubierto |
| CA-20.4 | CP-20.4 | `AlbumDeleteTests::test_a_foreign_album_returns_404_and_survives` | Cubierto |
| CA-20.5 | CP-20.5 | `AlbumDeleteTests::test_a_get_never_deletes_the_album` | Cubierto |

Archivo: `albums/tests/test_album_delete.py`.

### HU-22 — Consultar estado de una página

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-22.1 | CP-22.1 | `PageFilterTests::test_each_page_shows_its_status_as_text` | Cubierto |
| CA-22.2 | CP-22.2 | Transiciones en `ProcessPageTests`, `OcrTextTests`, `PageApprovalTests` y `EditApprovedTests` | Cubierto |
| CA-22.3 | CP-22.3 | `PageStatusLiveTests` y `LiveRefreshTests` | Cubierto |
| CA-22.4 | CP-22.4 | `PageFilterTests::test_the_filter_shows_only_those_pages` y `test_the_progress_card_splits_the_pages` | Cubierto |

Archivos principales: `albums/tests/test_library_progress.py`,
`test_processing.py`, `test_translation_approval.py` y
`test_translation_review.py`.

### HU-23 — Autoguardar el trabajo

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-23.1 | CP-23.1 | `AutosaveWorkTests` | Cubierto |
| CA-23.2 | CP-23.2 | `ConnectionFailureTests` | Cubierto |
| CA-23.3 | CP-23.3 | `PendingChangesTests` | Cubierto |
| CA-23.4 | CP-23.4 | `AutosaveAssociationTests` | Cubierto |
| CA-23.5 | CP-23.5 | `ConcurrentAutosaveTests` | Cubierto |

Archivo: `albums/tests/test_autosave.py`.

### HU-24 — Continuar un trabajo guardado

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-24.1 | CP-24.1 | `ResumeLastPointTests` | Cubierto |
| CA-24.2 | CP-24.2 | `ResumeAcrossSessionsTests` y `ResumeAccessTests` | Cubierto |
| CA-24.3 | CP-24.3 | `ResumeFallbackTests::test_album_without_previous_work_opens_first_unapproved_page` | Cubierto |
| CA-24.4 | CP-24.4 | `ResumeFallbackTests::test_deleted_last_page_falls_back_without_errors` | Cubierto |

Archivo: `albums/tests/test_resume_work.py`.

### HU-25 — Consultar progreso del álbum

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-25.1 | CP-25.1 | `AlbumApprovalProgressTests::test_library_and_detail_show_approved_page_progress` | Cubierto |
| CA-25.2 | CP-25.2 | `AlbumApprovalProgressTests::test_progress_changes_when_one_more_page_is_approved` | Cubierto |
| CA-25.3 | CP-25.3 | `AlbumApprovalProgressTests::test_detail_breaks_pages_down_into_four_states` | Cubierto |
| CA-25.4 | CP-25.4 | `AlbumApprovalProgressTests::test_album_without_pages_says_so_instead_of_showing_zero_percent` | Cubierto |

Archivo: `albums/tests/test_library_progress.py`.

### HU-27 — Exportar resultados de traducción

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-27.1 | CP-27.1 | `ExportDocumentTests` | Cubierto |
| CA-27.2 | CP-27.2 | `UnapprovedRegionsTests` | Cubierto |
| CA-27.3 | CP-27.3 | `NothingApprovedTests` | Cubierto |
| CA-27.4 | CP-27.4 | `BackgroundExportTests` | Cubierto |

Archivo: `albums/tests/test_export.py`. Desde HU-90 la misma pantalla ofrece
también el formato PNG en un ZIP; el DOCX sigue cubierto por estas pruebas y
por `FormatChoiceTests::test_docx_still_works_the_same`.

### HU-28 — Descargar resultados exportados

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-28.1 | CP-28.1 | `FinishedExportDownloadTests` | Cubierto |
| CA-28.2 | CP-28.2 | `UnavailableExportTests` | Cubierto |
| CA-28.3 | CP-28.3 | `ExportDownloadAccessTests` | Cubierto |
| CA-28.4 | CP-28.4 | `UnavailableExportTests::test_preparing_export_has_no_link_and_cannot_be_downloaded` | Cubierto |

Archivo: `albums/tests/test_export_download.py`. La descarga del ZIP de PNG
usa la misma vista; su aislamiento lo cubre CP-90.7.

### HU-85 — Añadir una región de texto a mano

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-85.1 | CP-85.1 | `ManualRegionTests::test_drawn_region_is_read_marked_and_inserted_in_reading_order` y `test_ocr_crop_is_padded_to_the_provider_minimum` | Cubierto |
| CA-85.2 | CP-85.2 | `ManualRegionTests::test_empty_ocr_result_creates_an_editable_region_with_the_warning` y `test_provider_failure_keeps_the_page_unchanged_and_can_be_retried` | Cubierto |
| CA-85.3 | CP-85.3 | `ManualRegionTests::test_too_small_and_outside_boxes_are_rejected_by_the_server` | Cubierto |
| CA-85.4 | CP-85.4 | `ManualRegionTests::test_pointer_mode_can_be_cancelled_and_reports_a_small_box` | Cubierto |
| CA-85.5 | CP-85.5 | `ManualRegionTests::test_new_region_reopens_an_approved_page_and_uses_existing_workflow` | Cubierto |
| CA-85.6 | CP-85.6 | `ManualRegionTests::test_coordinate_form_is_labelled_and_creates_the_same_region` | Cubierto |
| CA-85.7 | CP-85.7 | `ManualRegionTests::test_foreign_page_returns_not_found_and_creates_nothing` y `test_get_does_not_create_a_region` | Cubierto |

Archivo: `albums/tests/test_manual_regions.py`. Casos:
[CP de HU-85](WIKI_SPRINT_3_CP_HU-85.md).

### HU-86 — Gestionar regiones detectadas

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-86.1 | CP-86.1 | `DeleteRegionTests::test_delete_removes_the_region_and_renumbers_the_following_ones` | Cubierto |
| CA-86.2 | CP-86.2 | `DeleteRegionTests::test_undo_restores_every_edit_and_the_original_reading_order` | Cubierto |
| CA-86.3 | CP-86.3 | `SkipTranslationTests::test_skipped_region_keeps_source_and_is_excluded_from_every_flow` | Cubierto |
| CA-86.4 | CP-86.4 | `SkipTranslationTests::test_enable_translation_returns_an_empty_pending_region` | Cubierto |
| CA-86.5 | CP-86.5 | `SkipTranslationTests::test_empty_text_and_skip_translation_remain_distinct_decisions` | Cubierto |
| CA-86.6 | CP-86.6 | `RegionManagementAccessTests` | Cubierto |

Archivo: `albums/tests/test_region_management.py`. Casos:
[CP de HU-86](WIKI_SPRINT_3_CP_HU-86.md).

### HU-87 — Vista previa de la página traducida

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-87.1 | CP-87.1 | `TranslatedPreviewTests::test_original_and_translated_selector_controls_the_decorative_layer` | Cubierto |
| CA-87.2 | CP-87.2 | `FitTextTests` y `TranslatedPreviewTests::test_long_and_impossible_text_are_reflowed_or_warned` | Cubierto |
| CA-87.3 | CP-87.3 | `TranslatedPreviewTests::test_dialogue_and_narration_use_local_comic_neue_variants` y `FitTextTests::test_font_supports_spanish_characters` | Cubierto |
| CA-87.4 | CP-87.4 | `TranslatedPreviewTests::test_translation_autosave_returns_and_renders_a_new_preview` | Cubierto |
| CA-87.5 | CP-87.5 | `TranslatedPreviewTests::test_untranslated_uses_source_and_skipped_region_has_no_overlay` | Cubierto |
| CA-87.6 | CP-87.6 | `TranslatedPreviewTests::test_preview_font_uses_container_units_and_shares_the_zoom_target` | Cubierto |
| CA-87.7 | CP-87.7 | `TranslatedPreviewTests::test_selector_is_keyboard_operable_and_preview_is_not_announced_twice` | Cubierto |

Archivos: `albums/tests/test_translated_preview.py` y `test_typesetting.py`.
Casos: [CP de HU-87](WIKI_SPRINT_3_CP_HU-87.md).

### HU-88 — Limpiar el texto original de la página

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-88.1 | CP-88.1 | `PageCleaningTests::test_eight_uniform_regions_are_filled_without_touching_original` y `test_cleaning_is_queued_and_shown_as_in_progress` | Cubierto |
| CA-88.2 | CP-88.2 | `PageCleaningTests::test_non_uniform_region_is_left_for_manual_cleaning` | Cubierto |
| CA-88.3 | CP-88.3 | `PageCleaningTests::test_skipped_region_remains_identical` | Cubierto |
| CA-88.4 | CP-88.4 | `PageCleaningTests::test_workspace_offers_original_clean_and_translated_views` | Cubierto |
| CA-88.5 | CP-88.5 | `PageCleaningTests::test_restore_puts_back_original_pixels_and_pending_status` | Cubierto |
| CA-88.6 | CP-88.6 | `PageCleaningTests::test_failure_keeps_original_and_offers_retry` | Cubierto |
| CA-88.7 | CP-88.7 | `PageCleaningTests::test_region_actions_update_only_their_area` y `test_new_region_is_cleaned_without_rebuilding_the_page` | Cubierto |
| CA-88.8 | CP-88.8 | `PageCleaningTests::test_foreign_cleaning_resources_and_actions_return_not_found` | Cubierto |

Archivo: `albums/tests/test_cleaning.py`. Casos:
[CP de HU-88](WIKI_SPRINT_3_CP_HU-88.md). Sigue pendiente la validación
manual con tres páginas reales elegidas por Producto.

### HU-89 — Maquetar la traducción sobre la imagen

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-89.1 | CP-89.1 | `LayoutAlgorithmTests::test_default_layout_uses_the_ocr_box_and_the_kind_font` e `InitialLayoutTests` (2) | Cubierto |
| CA-89.2 | CP-89.2 | `EditorMarkupTests::test_each_box_carries_urls_versions_and_an_accessible_name` | Parcial: selección con clic y `Tab`, manual pendiente |
| CA-89.3 | CP-89.3 | `LayoutStyleTests::test_a_box_outside_the_image_is_rejected` y `test_a_box_touching_the_edges_is_accepted` | Parcial: arrastre y teclado, manual pendiente |
| CA-89.4 | CP-89.4 | `LayoutStyleTests` (3 pruebas de CP-89.4) y `RenderPageTests::test_left_and_right_alignment_are_drawn_where_they_belong` | Cubierto |
| CA-89.5 | CP-89.5 | `TranslationEditTests::test_editing_updates_the_translation_and_removes_approval` | Cubierto |
| CA-89.6 | CP-89.6 | `LayoutResetTests::test_reset_restores_the_ocr_box_and_the_default_style` | Parcial: guardado y `Ctrl+Z`, manual pendiente |
| CA-89.7 | CP-89.7 | `TypesetApprovalTests` (6) y `EditorMarkupTests` (3) | Cubierto |
| CA-89.8 | CP-89.8 | `RenderPageTests` (5) e `ImageFidelityTests::test_same_resolution_rgb_and_identical_to_render_page` | Parcial: comparación visual, manual pendiente |
| CA-89.9 | CP-89.9 | `ForeignResourceTests::test_every_endpoint_answers_404_without_changes` | Cubierto |

Archivos: `albums/tests/test_typesetting_editor.py` y
`test_typesetting_workspace.py`. Casos y procedimientos manuales:
[CP de HU-89](WIKI_SPRINT_3_CP_HU-89.md).

### HU-90 — Exportar las páginas traducidas como PNG

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-90.1 | CP-90.1 | `FormatChoiceTests::test_the_dialog_offers_both_formats_as_native_radios` y `test_docx_still_works_the_same` | Cubierto |
| CA-90.2 | CP-90.2 | `ArchiveContentTests::test_zip_name_type_and_page_order_with_a_gap` y `PreparingPngExportTests::test_png_export_waits_as_preparing_and_is_queued_once` | Cubierto |
| CA-90.3 | CP-90.3 | `ImageFidelityTests` (5 pruebas de CP-90.3) | Cubierto |
| CA-90.4 | CP-90.4 | `UntypesetPagesTests` (3 pruebas de CP-90.4) | Cubierto |
| CA-90.5 | CP-90.5 | `BlankAndKeptTextTests::test_a_blank_page_is_identical_to_the_original` y `test_a_skipped_region_keeps_its_original_text` | Cubierto |
| CA-90.6 | CP-90.6 | `FailureTests` | Cubierto |
| CA-90.7 | CP-90.7 | `ForeignAlbumTests::test_foreign_export_and_download_answer_not_found` | Cubierto |

Archivo: `albums/tests/test_png_export.py`. Casos:
[CP de HU-90](WIKI_SPRINT_3_CP_HU-90.md).

### HU-91 — Limpiar con IA el texto que está sobre el dibujo

Descartada tras el *spike*: sin CP ni pruebas. Ver
[nota de HU-91](WIKI_SPRINT_3_CP_HU-91.md).

## 5. Pruebas nuevas y cobertura

Desde la primera versión de este reporte la suite pasó de **555 a 678
pruebas** (+123), sin eliminar ninguna. Dos de ellas se añadieron en la
verificación final para cerrar huecos detectados: la espera del PNG (CP-90.2)
y el dibujo de la alineación izquierda y derecha (CP-89.4 y CP-89.8). Cada prueba se asignó a la historia
del commit que la introdujo y a un nivel de la sección 3 según lo que
ejercita: llamadas directas a funciones (modelo y servicio), peticiones con
el cliente de Django que comprueban estado, archivos o respuestas (vista e
integración), o marcado HTML y contratos del JavaScript (presentación).

| Historia | Archivo | Modelo y servicio | Vista e integración | Presentación | Total |
|---|---|---:|---:|---:|---:|
| HU-85 | `test_manual_regions.py` | 1 | 11 | 1 | 13 |
| HU-86 | `test_region_management.py` | 0 | 8 | 2 | 10 |
| HU-87 | `test_translated_preview.py`, `test_typesetting.py` | 7 | 1 | 4 | 12 |
| HU-88 | `test_cleaning.py` | 0 | 9 | 1 | 10 |
| HU-89 | `test_typesetting_editor.py`, `test_typesetting_workspace.py` | 8 | 25 | 19 | 52 |
| HU-90 | `test_png_export.py` | 1 | 19 | 3 | 23 |
| BUG-096 | `test_ocr_layout.py` | 3 | 0 | 0 | 3 |
| **Total** | | **20** | **73** | **30** | **123** |

**Cobertura.** El proyecto la mide con coverage.py (configuración en
`pyproject.toml`, mínimo del 90 % que hace fallar la CI). Ejecución local del
10 de noviembre de 2026 sobre la misma versión, con
`coverage run manage.py test` y `coverage report`: **97 %** de 3419
sentencias, con 96 sin cubrir. Los módulos nuevos de EP-08 quedan en
`albums/typesetting.py` 99 %, `albums/exporting.py` 99 %,
`albums/cleaning.py` 95 % y `albums/imaging.py` 100 %. La cifra oficial es la
del artefacto de cobertura de la CI del PR.

## 6. Regresiones de bugs de cierre

| Bug | Riesgo controlado | Prueba de regresión |
|---|---|---|
| BUG-063 | Una advertencia incorrecta podría ocultar el alcance del reprocesamiento. | `UnsavedChangesTests::test_reprocessing_warning_agrees_with_one_correction` y `test_reprocessing_warning_agrees_with_multiple_corrections` |
| BUG-071 | Los errores de producción podían mostrar una respuesta inconsistente o sin navegación segura. | `config/tests/test_error_pages.py::ErrorPageTests` |
| BUG-072 | Una región aprobada podía seguir contándose como trabajo pendiente. | `ApprovedReviewAccountingTests` |
| BUG-073 | Una página sin texto podía quedar en un estado incompleto. | `PageWithoutTextTests` y `PageFilterTests::test_a_processed_page_without_text_is_full` |
| BUG-074 | Crear y editar un álbum podían validar de forma distinta una portada falsa. | `AlbumCoverTests::test_fake_image_is_rejected` |
| BUG-096 | En una página gris de 16 bits todas las regiones se clasificaban como globo, en el OCR automático y en el manual. La primera parte de la corrección (miniatura, limpieza, recorte del OCR manual y dibujo de la página) llegó con HU-90. | `albums/tests/test_ocr_layout.py::SixteenBitRegionKindTests` (3), que falla si se quita el escalado; `ImageFidelityTests::test_a_sixteen_bit_gray_page_is_scaled_not_whitened` y `test_a_sixteen_bit_thumbnail_is_not_white` para la parte de HU-90 |

**Regresión de los 20 caminos de «Maquetada».**
`TypesetInvalidationTests::test_every_path_clears_the_typeset_state` recorre,
cada uno en su `subTest`, los 20 caminos que cambian una página maquetada
(maquetación, texto, aprobación, regiones, limpieza y procesamiento) y
comprueba que todos le quitan el estado «Maquetada» (ADR-003, P1). Así, un
camino nuevo que olvide hacerlo se detecta en cuanto se añade a la lista.

## 7. Ejecución del Quality Gate

| Paso | Comando | Resultado |
|---:|---|---|
| 1 | `ruff check . --fix` | Aprobado — sin hallazgos |
| 2 | `black .` | Aprobado — 126 archivos sin cambios |
| 3 | `ruff check .` | Aprobado — sin hallazgos |
| 4 | `black --check .` | Aprobado — 126 archivos con formato correcto |
| 5 | `python manage.py check` | Aprobado — cero problemas |
| 6 | `python manage.py test` | Aprobado — 678 pruebas |
| 7 | `pip-audit -r requirements.txt` | Aprobado — sin vulnerabilidades conocidas |

**Resultado: Quality Gate 7/7 en verde** con Python 3.12.10, según la
evidencia de la etapa
[`99b`](evidence/sprint-3/etapa-99b/E99b-quality-gate-RESUMEN.md), que incluye
las dos pruebas añadidas en la verificación final; los tiempos y las salidas
completas están en esa carpeta. Las etapas
[`90b`](evidence/sprint-3/etapa-90b/E90b-quality-gate-RESUMEN.md) y
[`99`](evidence/sprint-3/etapa-99/E99-quality-gate-RESUMEN.md) recogen las
ejecuciones anteriores, con 676 pruebas.

## 8. Cómo reproducir

Con el entorno virtual activo y las dependencias de desarrollo instaladas:

```bash
ruff check . --fix
black .
ruff check .
black --check .
python manage.py check
python manage.py test
pip-audit -r requirements.txt
```

Para la cobertura:

```bash
coverage run manage.py test
coverage report
```

En CI, `.github/workflows/quality.yml` ejecuta las verificaciones sobre Python
3.12, usa una base SQLite efímera y publica el reporte HTML de cobertura como
artefacto temporal.

## 9. Conclusión

La trazabilidad está completa para los 74 CP funcionales del Sprint 3 y para
las seis regresiones de cierre. Las 678 pruebas finalizaron correctamente, la
cobertura local es del 97 % y el Quality Gate quedó 7/7 en verde. Quedan
pendientes: la ejecución manual de las partes interactivas de CP-89.2,
CP-89.3, CP-89.6 y CP-89.8, la validación de HU-88 con páginas reales y
comprobar que la misma suite termine en verde en la CI de cada pull request.
