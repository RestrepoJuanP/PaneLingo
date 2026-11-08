# Borrador para la wiki — Casos de prueba de HU-22

> Casos de prueba de HU-22 para el Sprint 3. Las transiciones reutilizan las
> pruebas de las historias que producen cada estado y el detalle del álbum
> añade las pruebas de presentación, filtrado y actualización automática.

## HU-22 — Consultar estado de una página

Como traductor, quiero ver el estado de cada página para saber cuáles están
pendientes, en revisión o terminadas.

### CP-22.1 — Ver el estado de cada página — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Álbum propio con páginas en estados diferentes. |
| Pasos | Abrir el detalle del álbum. |
| Resultado esperado | Cada página muestra un chip con su estado escrito y una variante visual semántica. |
| CA relacionado | CA-22.1 |
| Prueba automática | `albums/tests/test_library_progress.py` › `PageFilterTests::test_each_page_shows_its_status_as_text` |

### CP-22.2 — Transiciones de estado — Esquema con ejemplos

| Estado inicial | Evento | Estado final | Prueba automática |
|---|---|---|---|
| Pendiente | Iniciar procesamiento | Procesando | `test_processing.py` › `ProcessPageTests::test_the_page_moves_to_processing_and_the_task_is_queued` |
| Procesando | OCR fiable | Procesada | `test_processing.py` › `ProcessPageTests::test_finished_detection_leaves_the_page_processed` |
| Procesando | OCR con baja confianza | Necesita revisión | `test_processing.py` › `OcrTextTests::test_low_confidence_marks_the_region_and_the_page` |
| Procesada | Aprobar la última traducción | Aprobada | `test_translation_approval.py` › `PageApprovalTests::test_approving_the_last_region_approves_the_page` |
| Aprobada | Editar una traducción | Procesada | `test_translation_review.py` › `EditApprovedTests::test_the_page_stops_being_approved` |

CA relacionado: CA-22.2.

### CP-22.3 — Actualización automática — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Página propia en estado “Procesando” y detalle del álbum abierto. |
| Pasos | Esperar a que termine el procesamiento. |
| Resultado esperado | El chip y la barra se actualizan sin recarga manual y el cambio se anuncia mediante una región `aria-live="polite"`. Al terminar se detienen las consultas. |
| CA relacionado | CA-22.3 |
| Pruebas automáticas | `test_library_progress.py` › `PageStatusLiveTests`; `test_processing.py` › `LiveRefreshTests` |

### CP-22.4 — Filtrar páginas por estado — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Álbum con páginas pendientes, procesadas y por revisar. |
| Pasos | Elegir “Por revisar”. |
| Resultado esperado | Solo aparecen las páginas que necesitan revisión y se conserva el recuento por estado. |
| CA relacionado | CA-22.4 |
| Pruebas automáticas | `test_library_progress.py` › `PageFilterTests::test_the_filter_shows_only_those_pages`, `test_the_progress_card_splits_the_pages` |

### Aislamiento y accesibilidad

- `test_processing.py` › `LiveRefreshTests::test_the_status_of_a_foreign_page_is_not_found` verifica que una página ajena responde 404.
- La ruta `albums:page_status` permanece clasificada como privada en `config/tests/test_route_access.py`.
- El texto del estado evita comunicarlo únicamente mediante color.
