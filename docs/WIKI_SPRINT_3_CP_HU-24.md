# Borrador para la wiki — Casos de prueba de HU-24

## Decisión funcional

El botón **Continuar** aparece en las tarjetas de álbumes activos que tienen
páginas y trabajo pendiente: estados **En progreso** o **En revisión**. No se
muestra en álbumes vacíos, completados ni archivados.

El último punto se deriva de la actividad manual persistida en las regiones:
correcciones del texto de origen, traducciones editadas y aprobaciones. Una
propuesta generada automáticamente no cuenta como trabajo manual. El enlace
incluye un ancla `#region-N`, por lo que la página se abre con esa región
seleccionada.

## HU-24 — Continuar un trabajo guardado

Como traductor, quiero retomar un proyecto guardado para seguir la traducción
desde donde la dejé.

### CP-24.1 — Retomar desde el último punto — Happy path

| Campo | Descripción |
|---|---|
| Precondición | El último cambio manual del álbum fue en la región 3 de la página 7. |
| Pasos | Pulsar **Continuar** en la tarjeta del álbum. |
| Resultado esperado | Se abre la página 7 con la región 3 seleccionada. |
| CA relacionado | CA-24.1 |
| Prueba automática | `ResumeLastPointTests::test_continue_opens_the_last_page_and_region` |

### CP-24.2 — Recuperar en otro dispositivo

| Campo | Descripción |
|---|---|
| Precondición | El usuario guardó texto, traducción y estado en una sesión anterior. |
| Pasos | Iniciar una sesión nueva y abrir la biblioteca. |
| Resultado esperado | Se recuperan los mismos datos y el mismo enlace para continuar; otra cuenta no puede verlos. |
| CA relacionado | CA-24.2 |
| Pruebas automáticas | `ResumeAcrossSessionsTests`, `ResumeAccessTests` |

### CP-24.3 — Álbum sin trabajo previo — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | El álbum tiene páginas, pero ninguna actividad manual guardada. |
| Pasos | Pulsar **Continuar**. |
| Resultado esperado | Se abre la primera página que no está aprobada. |
| CA relacionado | CA-24.3 |
| Prueba automática | `ResumeFallbackTests::test_album_without_previous_work_opens_first_unapproved_page` |

### CP-24.4 — El último punto ya no existe — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Se eliminó la página que contenía el único punto trabajado. |
| Pasos | Pulsar **Continuar**. |
| Resultado esperado | Se abre la primera página no aprobada, sin errores. |
| CA relacionado | CA-24.4 |
| Prueba automática | `ResumeFallbackTests::test_deleted_last_page_falls_back_without_errors` |

