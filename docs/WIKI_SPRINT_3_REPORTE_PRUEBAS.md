# Sprint 3 — Reporte de pruebas de software

Fecha de ejecución: **9 de noviembre de 2026**

Versión base: `main` en `99113ef`

Entorno: Python 3.12, Django 5.2 y SQLite de prueba

## 1. Objetivo

Verificar que las historias del Sprint 3 cumplen sus criterios de aceptación,
que cada caso de prueba tiene cobertura automática y que los cambios conservan
el comportamiento entregado en los sprints anteriores.

## 2. Alcance

Este reporte cubre:

- 7 historias de usuario del Sprint 3.
- 30 casos de prueba funcionales.
- Seguridad por autenticación, aislamiento de propietario y respuestas 404.
- Accesibilidad incluida en los contratos de plantillas y componentes.
- Regresiones de los cinco bugs corregidos antes del cierre.
- Suite completa de Django, análisis estático, formato y dependencias.

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
| Calidad estática | Ruff y Black | Mantener convenciones, imports, complejidad y formato. |
| Seguridad de dependencias | `pip-audit` | Detectar vulnerabilidades conocidas en dependencias de ejecución. |
| Integración continua | GitHub Actions | Repetir las verificaciones en cada PR y push a `main`. |

Los proveedores de OCR y traducción se simulan durante las pruebas. De esta
forma la suite es determinista y no transmite páginas, credenciales ni datos a
servicios externos.

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

Archivo: `albums/tests/test_export.py`.

### HU-28 — Descargar resultados exportados

| CA | CP | Prueba o grupo automático | Estado |
|---|---|---|---|
| CA-28.1 | CP-28.1 | `FinishedExportDownloadTests` | Cubierto |
| CA-28.2 | CP-28.2 | `UnavailableExportTests` | Cubierto |
| CA-28.3 | CP-28.3 | `ExportDownloadAccessTests` | Cubierto |
| CA-28.4 | CP-28.4 | `UnavailableExportTests::test_preparing_export_has_no_link_and_cannot_be_downloaded` | Cubierto |

Archivo: `albums/tests/test_export_download.py`.

## 5. Regresiones de bugs de cierre

| Bug | Riesgo controlado | Prueba de regresión |
|---|---|---|
| BUG-063 | Una advertencia incorrecta podría ocultar el alcance del reprocesamiento. | `UnsavedChangesTests::test_reprocessing_warning_agrees_with_one_correction` y `test_reprocessing_warning_agrees_with_multiple_corrections` |
| BUG-071 | Los errores de producción podían mostrar una respuesta inconsistente o sin navegación segura. | `config/tests/test_error_pages.py::ErrorPageTests` |
| BUG-072 | Una región aprobada podía seguir contándose como trabajo pendiente. | `ApprovedReviewAccountingTests` |
| BUG-073 | Una página sin texto podía quedar en un estado incompleto. | `PageWithoutTextTests` y `PageFilterTests::test_a_processed_page_without_text_is_full` |
| BUG-074 | Crear y editar un álbum podían validar de forma distinta una portada falsa. | `AlbumCoverTests::test_fake_image_is_rejected` |

## 6. Ejecución del Quality Gate

| Paso | Comando | Resultado |
|---:|---|---|
| 1 | `ruff check . --fix` | Aprobado — sin hallazgos |
| 2 | `black .` | Aprobado — 108 archivos sin cambios |
| 3 | `ruff check .` | Aprobado — sin hallazgos |
| 4 | `black --check .` | Aprobado — 108 archivos con formato correcto |
| 5 | `python manage.py check` | Aprobado — cero problemas |
| 6 | `python manage.py test` | Aprobado — 555 pruebas en 37 segundos |
| 7 | `pip-audit -r requirements.txt` | Aprobado — sin vulnerabilidades conocidas |

**Resultado: Quality Gate 7/7 en verde.** Las salidas corresponden a esta
rama y a la fecha indicada, no a una ejecución de una rama anterior.

## 7. Cómo reproducir

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

En CI, `.github/workflows/quality.yml` ejecuta las verificaciones sobre Python
3.12, usa una base SQLite efímera y publica el reporte HTML de cobertura como
artefacto temporal.

## 8. Conclusión

La trazabilidad está completa para los 30 CP funcionales del Sprint 3 y para
las cinco regresiones de cierre. Las 555 pruebas finalizaron correctamente y
el Quality Gate local quedó 7/7 en verde. La verificación restante de esta
etapa es comprobar que la misma suite termine en verde en la CI del pull
request.
