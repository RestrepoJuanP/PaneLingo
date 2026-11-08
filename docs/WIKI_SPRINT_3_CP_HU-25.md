# Borrador para la wiki — Casos de prueba de HU-25

## Decisión funcional

El progreso se mide por **páginas aprobadas**. Aunque el issue conserva una
pregunta abierta sobre páginas frente a regiones, CA-25.1 y CA-25.2 fijan la
unidad mediante los ejemplos “8 de 24 páginas aprobadas (33 %)” y “9 de 24
páginas aprobadas (38 %)”. Las regiones no ponderan el porcentaje.

## HU-25 — Consultar progreso del álbum

Como traductor, quiero ver el progreso de cada álbum para saber cuánto trabajo
me falta.

### CP-25.1 — Ver el progreso — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Álbum propio con 24 páginas, ocho aprobadas. |
| Pasos | Abrir “Mis álbumes” y luego el detalle del álbum. |
| Resultado esperado | Ambas pantallas muestran una barra con “8 de 24 páginas aprobadas (33 %)”. |
| CA relacionado | CA-25.1 |
| Prueba automática | `albums/tests/test_library_progress.py` › `AlbumApprovalProgressTests::test_library_and_detail_show_approved_page_progress` |

### CP-25.2 — Actualizar el progreso — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Álbum con 24 páginas, ocho aprobadas. |
| Pasos | Aprobar una página adicional y volver a consultar el álbum. |
| Resultado esperado | El progreso muestra “9 de 24 páginas aprobadas (38 %)”. |
| CA relacionado | CA-25.2 |
| Prueba automática | `AlbumApprovalProgressTests::test_progress_changes_when_one_more_page_is_approved` |

### CP-25.3 — Desglosar por estado — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Álbum con páginas en diferentes estados. |
| Pasos | Abrir el detalle del álbum. |
| Resultado esperado | Se muestran las cantidades de pendientes, en proceso, en revisión y aprobadas. Las páginas con error cuentan como pendientes y las procesadas todavía no aprobadas cuentan como en revisión. |
| CA relacionado | CA-25.3 |
| Prueba automática | `AlbumApprovalProgressTests::test_detail_breaks_pages_down_into_four_states` |

### CP-25.4 — Álbum sin páginas — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Álbum propio sin páginas. |
| Pasos | Abrir “Mis álbumes” y el detalle del álbum. |
| Resultado esperado | Se muestra “Sin páginas” y no “0 %”. |
| CA relacionado | CA-25.4 |
| Prueba automática | `AlbumApprovalProgressTests::test_album_without_pages_says_so_instead_of_showing_zero_percent` |

### Accesibilidad y aislamiento

- La barra usa `role="progressbar"`, `aria-valuenow`, límites de 0 a 100 y
  `aria-valuetext` con la fracción completa.
- El cálculo se realiza sobre los álbumes ya filtrados por propietario en la
  biblioteca y en `OwnedAlbumMixin`; no se expone información de otras cuentas.
