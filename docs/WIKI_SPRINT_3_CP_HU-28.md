# Borrador para la wiki — Casos de prueba de HU-28

## Decisión de alcance

PaneLingo conserva el historial completo de exportaciones y no las elimina por
caducidad. Cada descarga entrega el archivo inmutable que preparó HU-27; nunca
lo regenera con el estado actual del álbum.

**Segundo formato (HU-90).** Desde HU-90 el historial puede tener dos
formatos: el DOCX y el ZIP de páginas PNG. La misma vista descarga los dos;
`export_download_name` elige la extensión según `AlbumExport.format`. El
nombre del DOCX no cambia y el del ZIP es `{álbum}_{idioma}_{fecha}_png.zip`
([ADR-003, P3](adr/ADR-003-edicion-de-imagen.md)). El historial muestra el
formato de cada exportación y el aislamiento del ZIP lo verifica CP-90.7.

## HU-28 — Descargar resultados exportados

Como traductor, quiero descargar el archivo que genera la exportación para
conservar una copia de mi trabajo.

### CP-28.1 — Descargar una exportación terminada — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Una exportación propia terminó correctamente. |
| Pasos | Abrir **Revisión y exportación** y pulsar **Descargar**. |
| Resultado esperado | Se entrega exactamente el archivo guardado (DOCX o, desde HU-90, ZIP de PNG). El nombre incluye el título del álbum, el idioma de destino y la fecha; el del ZIP termina en `_png.zip`. Las exportaciones anteriores siguen disponibles en el historial. |
| CA relacionado | CA-28.1 |
| Pruebas automáticas | `FinishedExportDownloadTests` |

### CP-28.2 — No hay exportación disponible — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | El álbum no tiene una exportación terminada o el archivo ya no existe. |
| Pasos | Abrir la pantalla o solicitar directamente una dirección de descarga. |
| Resultado esperado | No se ofrece **Descargar** y la dirección inexistente responde 404. |
| CA relacionado | CA-28.2 |
| Pruebas automáticas | `UnavailableExportTests` |

### CP-28.3 — Solo el propietario puede descargar

| Campo | Descripción |
|---|---|
| Precondición | Existe una exportación de otra cuenta. |
| Pasos | Solicitar su descarga con otra sesión o sin sesión. |
| Resultado esperado | Se responde 404, sin redirección ni entrega del archivo. |
| CA relacionado | CA-28.3 |
| Pruebas automáticas | `ExportDownloadAccessTests` |

### CP-28.4 — La exportación todavía se está preparando

| Campo | Descripción |
|---|---|
| Precondición | La exportación se encuentra en estado **Preparando**. |
| Pasos | Abrir la pantalla o manipular directamente la dirección de descarga. |
| Resultado esperado | No aparece **Descargar** y la dirección responde 404 hasta que la tarea termine. |
| CA relacionado | CA-28.4 |
| Pruebas automáticas | `UnavailableExportTests` |

## Seguridad

- La vista hereda de `PrivateViewMixin`, filtra por `album__owner` y exige que
  el estado sea `ready`.
- CA-28.3 especializa el comportamiento anónimo: responde 404 en vez de llevar
  al inicio de sesión, para no confirmar que existe el identificador.
- El archivo se abre desde el almacenamiento privado y se envía como adjunto;
  nunca se publica su dirección de `media/`.
