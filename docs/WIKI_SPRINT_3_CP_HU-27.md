# Borrador para la wiki — Casos de prueba de HU-27

## Decisión de alcance

El MVP exporta **texto estructurado en DOCX**, no imágenes recompuestas. El
documento sigue el flujo actual del PO: organiza por página y región el texto
de origen y su traducción aprobada. La reinserción de texto en PNG, fuentes y
limpieza de burbujas pertenece a una épica posterior de edición de imagen.

La exportación conserva una instantánea del contenido aprobado al confirmar.
Así, el usuario puede seguir trabajando mientras Huey prepara el archivo sin
que una edición posterior cambie silenciosamente ese DOCX.

## HU-27 — Exportar resultados de traducción

Como traductor, quiero exportar los resultados de un álbum para utilizarlos
fuera de PaneLingo.

### CP-27.1 — Exportar traducciones aprobadas a DOCX — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Álbum propio con traducciones aprobadas. |
| Pasos | Abrir **Revisión y exportación** y pulsar **Exportar DOCX**. |
| Resultado esperado | Se prepara un DOCX que incluye título e idiomas y, para cada región aprobada, página, orden de lectura, tipo, texto de origen y traducción. |
| CA relacionado | CA-27.1 |
| Pruebas automáticas | `ExportDocumentTests` |

### CP-27.2 — Hay regiones sin aprobar — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | El álbum tiene traducciones aprobadas y pendientes. |
| Pasos | Abrir la pantalla de exportación y confirmar. |
| Resultado esperado | Se informa cuántas regiones no se incluirán y el servidor exige confirmación; el DOCX contiene solo las aprobadas. |
| CA relacionado | CA-27.2 |
| Pruebas automáticas | `UnapprovedRegionsTests` |

### CP-27.3 — No hay nada aprobado — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Ninguna región tiene traducción aprobada. |
| Pasos | Abrir la pantalla o manipular un POST de exportación. |
| Resultado esperado | La acción está deshabilitada, se explica el motivo y no se crea un archivo vacío. |
| CA relacionado | CA-27.3 |
| Pruebas automáticas | `NothingApprovedTests` |

### CP-27.4 — Preparación en segundo plano

| Campo | Descripción |
|---|---|
| Precondición | Hay al menos una traducción aprobada. |
| Pasos | Confirmar la exportación. |
| Resultado esperado | Se muestra **Preparando exportación…**, el usuario puede seguir trabajando y el estado se actualiza automáticamente a listo o error. Dos pulsaciones no encolan dos tareas. |
| CA relacionado | CA-27.4 |
| Pruebas automáticas | `BackgroundExportTests` |

## Seguridad y almacenamiento

- Las pantallas y el estado filtran por `album__owner`; otra cuenta recibe 404.
- El DOCX se guarda bajo `media/albums/user_<id>/album_<id>/exports/`, pero
  su dirección no se publica ni se sirve directamente.
- Al eliminar el álbum, su archivo exportado también se elimina.
- HU-28 añadirá la respuesta de descarga autenticada y el nombre entregado al
  navegador.

