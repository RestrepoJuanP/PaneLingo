# Borrador para la Wiki — Casos de prueba de HU-85

## Decisión funcional

Una región añadida manualmente guarda su caja en píxeles de la imagen
original y utiliza el mismo proveedor OCR que el procesamiento completo. El
servidor valida la caja, lee únicamente el recorte y recalcula el orden de
lectura de todas las regiones.

La interacción con puntero es una mejora progresiva: el formulario de
coordenadas permite realizar la misma operación sin ratón. El ADR-003 se usa
como base provisional y conserva pendiente la aprobación formal del PO.

## HU-85 — Añadir una región de texto a mano

Como traductor, quiero marcar una zona donde el OCR no detectó texto para que
también pueda corregirse, traducirse y aprobarse.

### CP-85.1 — Dibujar una región y leer su texto — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Página propia procesada con regiones existentes. |
| Pasos | Pulsar “Añadir región” y dibujar una caja de al menos 16 × 16 px. |
| Resultado esperado | Se ejecuta OCR sobre el recorte, se crea una región “Añadida a mano”, se determina su tipo y se renumera el orden de lectura. |
| CA relacionado | CA-85.1 |
| Pruebas automáticas | `ManualRegionTests::test_drawn_region_is_read_marked_and_inserted_in_reading_order`, `test_ocr_crop_is_padded_to_the_provider_minimum` |

### CP-85.2 — El OCR no encuentra texto — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | El recorte no contiene texto reconocible. |
| Pasos | Añadir la región. |
| Resultado esperado | La región se crea vacía, queda por revisar, se muestra el aviso y el campo de texto recibe el foco. Si falla el proveedor, no se crea nada y se puede reintentar. |
| CA relacionado | CA-85.2 |
| Pruebas automáticas | `test_empty_ocr_result_creates_an_editable_region_with_the_warning`, `test_provider_failure_keeps_the_page_unchanged_and_can_be_retried` |

### CP-85.3 — Caja inválida — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Página propia procesada. |
| Pasos | Enviar una caja de 10 × 10 px o una que sale de la imagen. |
| Resultado esperado | El servidor muestra un error asociado al formulario y no crea ninguna región. |
| CA relacionado | CA-85.3 |
| Prueba automática | `test_too_small_and_outside_boxes_are_rejected_by_the_server` |

### CP-85.4 — Cancelar el dibujo — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Modo “Añadir región” activo. |
| Pasos | Pulsar Escape, “Cancelar” o volver a pulsar la herramienta. |
| Resultado esperado | El modo termina, el rectángulo provisional desaparece y no se envía el formulario. |
| CA relacionado | CA-85.4 |
| Prueba automática | `test_pointer_mode_can_be_cancelled_and_reports_a_small_box` |

### CP-85.5 — Usar el flujo existente — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Página aprobada. |
| Pasos | Añadir, corregir, traducir y aprobar una región manual. |
| Resultado esperado | La página deja de estar aprobada al añadirla y vuelve a aprobarse cuando termina el flujo de la región nueva. |
| CA relacionado | CA-85.5 |
| Prueba automática | `test_new_region_reopens_an_approved_page_and_uses_existing_workflow` |

### CP-85.6 — Crear mediante el formulario — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Uso exclusivo de teclado. |
| Pasos | Escribir x, y, ancho y alto y pulsar “Añadir y leer”. |
| Resultado esperado | Se crea exactamente la misma región que con el dibujo y cada control tiene una etiqueta asociada. |
| CA relacionado | CA-85.6 |
| Prueba automática | `test_coordinate_form_is_labelled_and_creates_the_same_region` |

### CP-85.7 — Solo páginas propias — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Existe una página de otra cuenta. |
| Pasos | Enviar el POST de creación con su identificador. |
| Resultado esperado | La respuesta es 404 y no se crea ninguna región. Un GET a la ruta de acción responde 405. |
| CA relacionado | CA-85.7 |
| Pruebas automáticas | `test_foreign_page_returns_not_found_and_creates_nothing`, `test_get_does_not_create_a_region` |

## Seguridad y accesibilidad

- La vista usa `private_view`, acepta solo POST y busca la página por
  `album__owner`.
- Las coordenadas se validan otra vez en el servidor.
- El formulario mantiene etiquetas, errores asociados y foco visible.
- El modo de dibujo se cancela con Escape y comunica su estado mediante una
  región `aria-live="polite"`.
- La interfaz sigue siendo operable con teclado mediante el formulario de
  coordenadas.
