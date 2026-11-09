# HU-88 — Limpiar el texto original de la página

## Decisión aplicada

La limpieza se mide y ejecuta por región. Se conserva siempre la imagen
original y se genera una capa PNG privada e independiente. La implementación
sigue ADR-003 aunque su aprobación formal siga pendiente; esta excepción fue
autorizada para no bloquear la historia.

Las constantes del algoritmo están centralizadas en `albums/cleaning.py`:

- `RING_WIDTH = 3`
- `COLOR_TOLERANCE = 24`
- `UNIFORM_RATIO = 0.85`
- ampliación de la caja: 2 px por lado

La validación automática usa imágenes sintéticas reproducibles. Queda como
validación manual pendiente probar tres páginas reales elegidas por Producto.

## Casos de prueba

### CP-88.1 — Limpiar una página — Happy path

1. Dada una página procesada con ocho regiones sobre fondos uniformes.
2. Cuando el traductor pulsa «Limpiar página».
3. Entonces se encola `clean_page_task`, se muestra «Limpiando la página…» y
   cada región queda rellena con su color de fondo.
4. Y la imagen original y los trazos externos permanecen iguales.

Automatización: `PageCleaningTests.test_eight_uniform_regions_are_filled_without_touching_original`
y `test_cleaning_is_queued_and_shown_as_in_progress`.

### CP-88.2 — Fondo no uniforme

1. Dada una región cuyo anillo no alcanza 85 % de píxeles similares.
2. Cuando se limpia la página.
3. Entonces la región queda sin modificar, con estado «Limpieza manual» y el
   resumen indica cuántas regiones requieren limpieza manual o con IA.

Automatización: `test_non_uniform_region_is_left_for_manual_cleaning`.

### CP-88.3 — Región marcada «No traducir»

1. Dada una región excluida de traducción.
2. Cuando se limpia la página.
3. Entonces sus píxeles se conservan y su estado de limpieza es `kept`.

Automatización: `test_skipped_region_remains_identical`.

### CP-88.4 — Comparar las tres vistas

1. Dada una página con capa limpia.
2. Cuando se abre el workspace.
3. Entonces aparecen «Original», «Limpia» y «Traducida»; la vista limpia no
   muestra cajas y la traducida compone el texto sobre la capa limpia.

Automatización: `test_workspace_offers_original_clean_and_translated_views`.

### CP-88.5 — Restaurar una región

1. Dada una región ya rellenada.
2. Cuando se pulsa «Restaurar original».
3. Entonces solo esa caja vuelve a los píxeles originales y queda «Sin limpiar».

Automatización: `test_restore_puts_back_original_pixels_and_pending_status`.

### CP-88.6 — Fallo de limpieza

1. Dado un error al construir la capa limpia.
2. Cuando termina la tarea.
3. Entonces se conserva el original, se muestra el error y se ofrece reintentar.

Automatización: `test_failure_keeps_original_and_offers_retry`.

### CP-88.7 — Cambios posteriores de regiones

1. Dada una página limpia.
2. Cuando se añade, elimina o cambia «No traducir» en una región.
3. Entonces se actualizan solo los píxeles de esa región, sin rehacer la página.

Automatización: `test_region_actions_update_only_their_area` y
`test_new_region_is_cleaned_without_rebuilding_the_page`.

### CP-88.8 — Aislamiento por propietario

1. Dada una página que pertenece a otra cuenta.
2. Cuando se solicita limpiar, descargar su capa limpia o restaurar una región.
3. Entonces las tres operaciones responden 404.

Automatización: `test_foreign_cleaning_resources_and_actions_return_not_found`.
