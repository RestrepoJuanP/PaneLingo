# Borrador para la wiki — Casos de prueba de HU-89

## Decisión de alcance

La maquetación se calcula **una sola vez, en el servidor**
(`albums/typesetting.py`, `layout_for_region`). El editor solo pinta las
líneas, el tamaño y la caja que devuelve el servidor, y la exportación PNG
de HU-90 dibuja con la misma función (`render_page`). Las coordenadas se
guardan en píxeles de la imagen original. Las decisiones están en
[ADR-003](adr/ADR-003-edicion-de-imagen.md) (P1, P2, P6, P7 y P8); su
aprobación formal por el PO sigue pendiente.

La pestaña **Maquetación** se abre con `?paso=maquetacion` en el espacio de
trabajo de la página y solo está disponible cuando la página tiene imagen
limpia (HU-88) y regiones de texto.

Las pruebas automáticas cubren todo lo que decide el servidor. La
interacción con ratón y teclado ocurre en JavaScript, que el cliente de
pruebas de Django no ejecuta: esas partes se verifican a mano con el
procedimiento de cada caso y se registran en la sección
[Resultado de la ejecución manual](#resultado-de-la-ejecución-manual).

## HU-89 — Maquetar la traducción sobre la imagen

Como traductor, quiero ajustar cada texto traducido directamente sobre la
página (su posición, tamaño, fuente y alineación) para que la página final
se vea como un cómic editado profesionalmente.

Issue: [#89](https://github.com/RestrepoJuanP/PaneLingo/issues/89)

**Antecedentes comunes:** sesión iniciada; una página propia limpia, con sus
traducciones aprobadas, abierta en la pestaña **Maquetación**.

### CP-89.1 — Maquetación automática de partida — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Página limpia con traducciones aprobadas y sin maquetación guardada. |
| Pasos | Abrir la pestaña **Maquetación**. |
| Resultado esperado | Cada traducción aparece sobre la imagen limpia, dentro de la caja de su región del OCR, ajustada con `fit_text` y con la fuente por defecto de su tipo (Comic Neue regular en diálogo, cursiva en narración). Las líneas y el tamaño los emite el servidor. |
| CA relacionado | CA-89.1 |
| Pruebas automáticas | `albums/tests/test_typesetting_editor.py::LayoutAlgorithmTests::test_default_layout_uses_the_ocr_box_and_the_kind_font`, `albums/tests/test_typesetting_workspace.py::InitialLayoutTests::test_each_region_carries_the_server_lines_and_size`, `albums/tests/test_typesetting_workspace.py::InitialLayoutTests::test_the_editor_starts_from_the_cleaned_image` |
| Estado | Cubierto por prueba automática |

### CP-89.2 — Seleccionar un texto — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Pestaña **Maquetación** abierta con al menos dos textos. |
| Pasos | Hacer clic en el texto de la región 2. Después, recargar y llegar al mismo texto solo con `Tab`. |
| Resultado esperado | El texto queda seleccionado con un marco y tiradores en las cuatro esquinas, y el panel lateral muestra fuente, tamaño (automático o fijo), alineación, color y texto. Cada caja es enfocable, con `role="button"` y el nombre «Región N, texto: …». |
| CA relacionado | CA-89.2 |
| Prueba automática | `albums/tests/test_typesetting_workspace.py::EditorMarkupTests::test_each_box_carries_urls_versions_and_an_accessible_name` (marcado accesible de cada caja) |
| Parte manual | **Selección con clic y con `Tab`, marco, tiradores y panel.** Procedimiento: (1) con el ratón, pulsar el texto de la región 2 y comprobar marco, cuatro tiradores y los valores del panel; (2) recargar, pulsar `Tab` hasta llegar a la región 2, comprobar que el foco es visible y que `Espacio` la selecciona; (3) con un lector de pantalla, comprobar que se anuncia «Región 2, texto: …». |
| Estado | Marcado cubierto por prueba automática; interacción **manual pendiente de ejecutar** |

### CP-89.3 — Mover y cambiar el tamaño de la caja — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Un texto seleccionado. |
| Pasos | Arrastrar el texto y uno de sus tiradores. Después, con el foco en la caja, usar las flechas, `Mayús` + flechas y `Alt` + flechas. Intentar llevar la caja fuera de la imagen. |
| Resultado esperado | La caja se mueve o cambia de tamaño y el texto se vuelve a ajustar. Las flechas mueven 1 px de la imagen, `Mayús` + flechas 10 px y `Alt` + flechas cambian el tamaño. La caja no sale de los bordes de la imagen: el servidor rechaza una caja que se sale y acepta una que llega justo al borde. |
| CA relacionado | CA-89.3 |
| Pruebas automáticas | `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_a_box_outside_the_image_is_rejected`, `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_a_box_touching_the_edges_is_accepted` |
| Parte manual | **Arrastre, tiradores y teclado.** Procedimiento: (1) arrastrar la caja y soltarla; comprobar que el texto se reajusta y que la barra pasa por «Guardando…» y después muestra el mensaje de guardado; (2) arrastrar el tirador inferior derecho y comprobar el reajuste; (3) con el foco en la caja, pulsar `→` una vez y `Mayús` + `→` una vez y comprobar en el panel que la posición cambia 1 y 10 px; (4) pulsar `Alt` + `↓` y comprobar que crece el alto; (5) arrastrar la caja contra cada borde y comprobar que no sale de la imagen. |
| Estado | Límites cubiertos por prueba automática; interacción **manual pendiente de ejecutar** |

### CP-89.4 — Cambiar el estilo — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Un texto seleccionado. |
| Pasos | En el panel, elegir «Bangers», tamaño fijo 28 px, alineación izquierda y color `#FFFFFF`. Después, volver a «Tamaño automático». |
| Resultado esperado | El texto se ve con ese estilo sobre la imagen y el servidor lo guarda y lo devuelve recalculado. «Tamaño automático» vuelve al ajuste de `fit_text`. Un valor inválido (fuente fuera del registro, tamaño fuera de 8–200, color sin formato `#RRGGBB`) responde 400 con su campo y no guarda nada. |
| CA relacionado | CA-89.4 |
| Pruebas automáticas | `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_the_panel_style_of_the_scenario_is_applied`, `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_each_valid_style_is_saved`, `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_each_invalid_value_is_rejected_and_nothing_changes` |
| Estado | Cubierto por prueba automática |

### CP-89.5 — Editar el texto sobre la imagen — Happy path

| Campo | Descripción |
|---|---|
| Precondición | La región 2 tiene la traducción aprobada. |
| Pasos | Hacer doble clic en el texto (o pulsar `Enter` con él seleccionado), cambiarlo y pulsar `Ctrl+Enter`. |
| Resultado esperado | El texto se guarda como la traducción de la región (el mismo dato que edita HU-18), la lista de regiones muestra el texto nuevo y la región vuelve a «Editada» (CA-18.2). |
| CA relacionado | CA-89.5 |
| Prueba automática | `albums/tests/test_typesetting_editor.py::TranslationEditTests::test_editing_updates_the_translation_and_removes_approval` |
| Estado | Cubierto por prueba automática |

### CP-89.6 — Guardado, deshacer y restablecer — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Varios cambios de maquetación hechos en la página. |
| Pasos | Hacer un cambio y esperar. Pulsar `Ctrl+Z` varias veces. Pulsar **Restablecer** en una región. |
| Resultado esperado | Cada cambio se guarda solo, sin botón «Guardar», y la barra lo indica. `Ctrl+Z` deshace el último cambio de maquetación de la página, hasta 20 pasos. **Restablecer** devuelve la caja del OCR, la fuente del tipo, el tamaño automático, la alineación al centro y el color negro. |
| CA relacionado | CA-89.6 |
| Prueba automática | `albums/tests/test_typesetting_editor.py::LayoutResetTests::test_reset_restores_the_ocr_box_and_the_default_style` |
| Parte manual | **Guardado automático y `Ctrl+Z` por teclado.** Procedimiento: (1) cambiar la alineación y comprobar que la barra muestra «Guardando…» y después el mensaje de guardado, sin pulsar ningún botón; (2) recargar y comprobar que el cambio sigue; (3) hacer tres cambios y pulsar `Ctrl+Z` tres veces: cada pulsación deshace uno, y el contador del botón **Deshacer** baja; (4) hacer 21 cambios y comprobar que solo se pueden deshacer 20; (5) con el foco en el editor de texto, comprobar que `Ctrl+Z` deshace la escritura y no la maquetación. |
| Estado | **Restablecer** cubierto por prueba automática; guardado y `Ctrl+Z` **manual pendiente de ejecutar** |

### CP-89.7 — Aprobar la maquetación — Happy path / Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Página limpia; en un caso con todas las traducciones aprobadas y en otro con una sin aprobar. |
| Pasos | Pulsar **Aprobar página** en la pestaña **Maquetación**. Después, cambiar un texto o un estilo. Repetir con una traducción sin aprobar y con una página sin imagen limpia. |
| Resultado esperado | La página queda «Maquetada» en la rejilla del álbum. Cualquier cambio posterior le quita ese estado. Sin todas las traducciones aprobadas o sin imagen limpia, **Aprobar página** no está disponible y se explica el motivo con texto. Sin JavaScript, el botón funciona como formulario normal y vuelve a la página con un mensaje. |
| CA relacionado | CA-89.7 |
| Pruebas automáticas | `albums/tests/test_typesetting_editor.py::TypesetApprovalTests::test_approving_with_everything_ready`, `::test_the_grid_shows_the_typeset_chip`, `::test_rejected_without_a_cleaned_image`, `::test_rejected_with_translations_not_approved`, `::test_without_javascript_it_redirects_with_a_message`, `::test_a_later_change_removes_the_typeset_state`; `albums/tests/test_typesetting_workspace.py::EditorMarkupTests::test_approve_is_disabled_with_its_reason`, `::test_an_approved_page_says_so_in_text`, `::test_layout_responses_carry_the_page_status` |
| Estado | Cubierto por prueba automática |

**Regresión de los 20 caminos.** `albums/tests/test_typesetting_editor.py::TypesetInvalidationTests::test_every_path_clears_the_typeset_state`
recorre, cada uno en su `subTest`, los 20 caminos que cambian una página
maquetada (maquetar, restablecer, editar por formulario y por autoguardado,
aprobar con texto, corregir, restaurar el origen, aplicar traducciones,
eliminar y restaurar una región, «No traducir» y volver a traducir, región
manual, retirar y abandonar la aprobación, limpiar, reemplazar y restaurar la
limpieza, procesar y guardar regiones) y comprueba que todos borran
«Maquetada» (ADR-003, P1). `test_reapproving_an_approved_region_keeps_the_typeset_state`
fija el caso contrario: volver a aprobar sin cambios no la borra.

### CP-89.8 — Lo que se ve es lo que se exporta — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Página maquetada con estilos distintos en varias regiones. |
| Pasos | Comparar el editor con el PNG que genera la exportación de HU-90. |
| Resultado esperado | Las líneas, el tamaño y la posición de cada texto en el editor coinciden con el PNG exportado, con una diferencia máxima de 2 px. El PNG tiene la resolución de la original y solo cambian los píxeles de las cajas traducidas. |
| CA relacionado | CA-89.8 |
| Pruebas automáticas | `albums/tests/test_typesetting_editor.py::RenderPageTests::test_the_render_keeps_resolution_and_mode`, `::test_pixels_change_inside_each_box_and_nowhere_else`, `::test_the_drawn_text_matches_the_layout_within_two_pixels`, `::test_the_stored_style_is_drawn`; `albums/tests/test_png_export.py::ImageFidelityTests::test_same_resolution_rgb_and_identical_to_render_page` |
| Parte manual | **Comparación visual del editor con el PNG.** Procedimiento: (1) maquetar una página con una región en Bangers a tamaño fijo, otra alineada a la izquierda y otra con color; (2) exportar en PNG (HU-90), descargar el ZIP y abrir la página; (3) poner el editor al 100 % de zoom y comparar, región por región, los saltos de línea, el tamaño y la posición con el PNG; (4) anotar cualquier diferencia visible. |
| Estado | Coincidencia de ±2 px cubierta por prueba automática; comparación visual **manual pendiente de ejecutar** |

### CP-89.9 — Solo páginas propias — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Existe una región y una página de otra cuenta. |
| Pasos | Enviar a sus identificadores los POST de maquetar, restablecer, editar el texto y aprobar la página. |
| Resultado esperado | Las cuatro acciones responden 404 y nada cambia. |
| CA relacionado | CA-89.9 |
| Prueba automática | `albums/tests/test_typesetting_editor.py::ForeignResourceTests::test_every_endpoint_answers_404_without_changes` |
| Estado | Cubierto por prueba automática |

**Total: 9 CP; 51 pruebas automáticas nuevas** en
`albums/tests/test_typesetting_editor.py` (29) y
`albums/tests/test_typesetting_workspace.py` (22).

Pruebas de apoyo sin CP propio: pestañas y `?paso=` (`StepTabsTests`, 5),
funcionamiento sin JavaScript (`WithoutJavascriptTests`, 2), fuentes y
límites emitidos por el servidor en lugar de escritos en el JavaScript
(`EditorMarkupTests` y `EditorScriptTests`, 6, patrón BUG-043), versión
desactualizada → 409 (`test_a_stale_version_is_a_conflict_and_nothing_changes`),
tamaño fijo que no cabe (`test_a_fixed_size_that_does_not_fit_is_kept`,
ADR-003 P2), regiones sin aprobar o «No traducir» (ADR-003 P6) y aviso de
«Limpieza manual» sin bloqueo (ADR-003 P7).

Evidencia del Quality Gate:
[`etapa-89/`](evidence/sprint-3/etapa-89/E89-quality-gate-RESUMEN.md) y
[`etapa-89b/`](evidence/sprint-3/etapa-89b/E89b-quality-gate-RESUMEN.md).

## Resultado de la ejecución manual

Para rellenar por el equipo al ejecutar cada procedimiento. Hasta entonces,
ninguna parte manual consta como ejecutada en el repositorio.

| CP | Parte manual | Fecha | Responsable | Resultado | Evidencia |
|---|---|---|---|---|---|
| CP-89.2 | Selección con clic y con `Tab`, marco, tiradores y panel | | | | |
| CP-89.3 | Arrastre, tiradores y teclado; límites de la imagen | | | | |
| CP-89.6 | Guardado automático y `Ctrl+Z` por teclado | | | | |
| CP-89.8 | Comparación visual del editor con el PNG exportado | | | | |

## Seguridad y accesibilidad

- Las rutas de maquetación usan `private_view`, solo aceptan POST y buscan la
  región por `page__album__owner`; lo ajeno responde 404.
- El servidor valida fuente, tamaño, alineación, color y caja; el navegador
  no decide ningún límite.
- Cada caja es un elemento enfocable con nombre accesible, el foco no se
  pierde al guardar y los requisitos de **Aprobar página** se dicen con
  texto, no solo con color.
- Sin JavaScript se ven la nota de la pestaña y **Aprobar página** como
  formulario con CSRF.
