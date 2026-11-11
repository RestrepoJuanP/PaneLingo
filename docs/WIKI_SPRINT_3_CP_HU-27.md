# Borrador para la wiki — Casos de prueba de HU-27

## Decisión de alcance

HU-27 exporta **texto estructurado en DOCX**. El documento sigue el flujo
actual del PO: organiza por página y región el texto de origen y su
traducción aprobada.

**Segundo formato (HU-90).** La épica EP-08 Edición de imagen (RF-15,
[ADR-003](adr/ADR-003-edicion-de-imagen.md)) añadió a la misma pantalla un
segundo formato: **«Páginas traducidas (PNG en un ZIP)»**, con cada página
limpia y con la traducción maquetada. El usuario elige el formato antes de
confirmar; el DOCX se genera exactamente igual que antes. Ambos formatos
comparten la tarea en segundo plano, la instantánea inmutable y el historial.
Los casos del formato PNG están en [CP de HU-90](WIKI_SPRINT_3_CP_HU-90.md).

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
| Resultado esperado | Se prepara un DOCX que incluye título e idiomas y, para cada región aprobada, página, orden de lectura, tipo, texto de origen y traducción. Desde HU-90 se elige primero el formato; con «Documento de texto (DOCX)» el resultado es el mismo (CP-90.1). |
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
- HU-28 añadió la respuesta de descarga autenticada y el nombre entregado al
  navegador.
- El ZIP de PNG de HU-90 se guarda en la misma carpeta privada y sigue las
  mismas reglas.

