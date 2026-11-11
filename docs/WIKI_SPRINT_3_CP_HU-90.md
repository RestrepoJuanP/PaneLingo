# Borrador para la wiki — Casos de prueba de HU-90

## Decisión de alcance

HU-90 añade un **segundo formato** a la exportación de HU-27 y HU-28: las
páginas traducidas como PNG dentro de un ZIP. El DOCX se sigue generando
igual. Ambos formatos comparten la tarea en segundo plano, el historial, la
instantánea inmutable y la descarga privada; `AlbumExport.format` distingue
`docx` de `png_zip` y `export_download_name` elige la extensión.

Cada PNG se dibuja con `render_page` (`albums/typesetting.py`), la misma
función que alimenta el editor de HU-89: no hay un segundo algoritmo. Las
precisiones acordadas al implementar la historia están en
[ADR-003](adr/ADR-003-edicion-de-imagen.md), P3, P5, P6 y P9:

- **Nombres (P3):** `{álbum}_{idioma}_{fecha}_png.zip` y
  `pagina-{número:03d}.png` con el número real de la página. El ZIP no
  incluye la carpeta `limpias/` mientras el PO no la pida.
- **Precisión de CA-90.4 (P9):** una página sin maquetar se exporta con la
  maquetación **guardada**, que es la que se ve en el editor, y no con una
  automática nueva que descartaría los ajustes del traductor.
- **Página traducida sin imagen limpia (P9):** se exporta como la original,
  sin textos, y se avisa.
- **Imágenes de 16 bits (P9):** se escalan a 8 bits con `albums/imaging.py`
  en lugar de recortarse. BUG-096 completó esa corrección en la clasificación
  de regiones.

## HU-90 — Exportar las páginas traducidas como PNG

Como traductor, quiero descargar las páginas del álbum ya traducidas como
imágenes para entregarlas o publicarlas sin pasar por otro programa.

Issue: [#90](https://github.com/RestrepoJuanP/PaneLingo/issues/90)

**Antecedentes comunes:** sesión iniciada; un álbum propio con páginas
limpias y traducciones aprobadas; pantalla **Revisión y exportación**
(`/albumes/<id>/exportar/`).

### CP-90.1 — Elegir el formato — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Álbum propio con al menos una traducción aprobada en una página limpia. |
| Pasos | Abrir **Revisión y exportación**. |
| Resultado esperado | Se puede elegir «Documento de texto (DOCX)», como hasta ahora, o «Páginas traducidas (PNG en un ZIP)», con dos botones de opción nativos. El DOCX se sigue generando como antes. |
| CA relacionado | CA-90.1 |
| Pruebas automáticas | `albums/tests/test_png_export.py::FormatChoiceTests::test_the_dialog_offers_both_formats_as_native_radios`, `albums/tests/test_png_export.py::FormatChoiceTests::test_docx_still_works_the_same` |
| Estado | Cubierto por prueba automática |

### CP-90.2 — Exportar en PNG — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Álbum con las páginas 1, 2 y 4 (la 3 se eliminó). |
| Pasos | Elegir «Páginas traducidas (PNG en un ZIP)», confirmar y descargar el resultado. |
| Resultado esperado | Se muestra «Preparando exportación…» mientras la tarea corre. Al terminar se descarga un ZIP llamado `{álbum}_{idioma}_{fecha}_png.zip` que contiene `pagina-001.png`, `pagina-002.png` y `pagina-004.png`, en ese orden. |
| CA relacionado | CA-90.2 |
| Pruebas automáticas | `albums/tests/test_png_export.py::ArchiveContentTests::test_zip_name_type_and_page_order_with_a_gap`, `albums/tests/test_png_export.py::PreparingPngExportTests::test_png_export_waits_as_preparing_and_is_queued_once` (la exportación queda «Preparando», la pantalla lo muestra y un segundo POST no crea otra) |
| Estado | Cubierto por prueba automática. La espera reutiliza el mecanismo de HU-27 (CP-27.4), ahora verificado también con el formato PNG. |

### CP-90.3 — Fidelidad de cada imagen — Happy path

| Campo | Descripción |
|---|---|
| Precondición | Páginas originales en RGB, en escala de grises, en RGBA, con paleta y en gris de 16 bits. |
| Pasos | Exportar en PNG y abrir cada imagen del ZIP. |
| Resultado esperado | Cada PNG tiene la resolución de la original y es idéntico, píxel a píxel, a `render_page` (lo que muestra el editor). Las originales en escala de grises salen en `L` y las de color en `RGB`, sin canal alfa. Una paleta solo de grises sale en `L` y una con colores, en `RGB`. Un PNG gris de 16 bits se escala a 8 bits y no sale blanco. |
| CA relacionado | CA-90.3 |
| Pruebas automáticas | `albums/tests/test_png_export.py::ImageFidelityTests::test_same_resolution_rgb_and_identical_to_render_page`, `::test_a_grayscale_original_exports_in_l`, `::test_an_rgba_original_exports_in_rgb_without_alpha`, `::test_a_gray_palette_exports_in_l_and_a_color_one_in_rgb`, `::test_a_sixteen_bit_gray_page_is_scaled_not_whitened` |
| Estado | Cubierto por prueba automática |

### CP-90.4 — Páginas sin maquetar — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Una página con texto que traducir no está maquetada; otra no tiene texto. |
| Pasos | Pedir la exportación en PNG. |
| Resultado esperado | Antes de confirmar se avisa «1 página no está maquetada: se exportará con la maquetación que se ve en el editor. Las regiones sin traducción aprobada conservarán el texto original.» La página sin texto no cuenta. El servidor exige confirmar el aviso, y la página se exporta con su maquetación guardada (precisión de ADR-003, P9). |
| CA relacionado | CA-90.4 |
| Pruebas automáticas | `albums/tests/test_png_export.py::UntypesetPagesTests::test_the_warning_counts_only_pages_with_text_to_typeset`, `::test_confirmation_is_required_before_exporting`, `::test_an_untypeset_page_uses_its_saved_layout` |
| Estado | Cubierto por prueba automática |

### CP-90.5 — Páginas sin texto y «No traducir» — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Una página en blanco y una región marcada «No traducir». |
| Pasos | Exportar en PNG. |
| Resultado esperado | La página en blanco sale idéntica a la original y la región «No traducir» conserva su texto original. |
| CA relacionado | CA-90.5 |
| Pruebas automáticas | `albums/tests/test_png_export.py::BlankAndKeptTextTests::test_a_blank_page_is_identical_to_the_original`, `albums/tests/test_png_export.py::BlankAndKeptTextTests::test_a_skipped_region_keeps_its_original_text` |
| Estado | Cubierto por prueba automática |

### CP-90.6 — Falla la exportación — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | La tarea falla a mitad, o la imagen limpia o la original cambian o desaparecen después de congelar el contenido. |
| Pasos | Pedir la exportación en PNG y esperar a que termine la tarea. |
| Resultado esperado | Se muestra «No se pudo preparar la exportación. Inténtalo de nuevo.» y no queda ningún ZIP ni archivo temporal para descargar. |
| CA relacionado | CA-90.6 |
| Pruebas automáticas | `albums/tests/test_png_export.py::FailureTests::test_a_failure_mid_task_leaves_an_error_and_no_file`, `::test_a_cleaned_image_changed_after_the_snapshot_fails`, `::test_a_missing_original_fails` |
| Estado | Cubierto por prueba automática |

### CP-90.7 — Solo álbumes propios — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Existe un álbum con una exportación PNG terminada en otra cuenta. |
| Pasos | Pedir exportarlo o descargar su ZIP. |
| Resultado esperado | Las dos acciones responden 404. |
| CA relacionado | CA-90.7 |
| Prueba automática | `albums/tests/test_png_export.py::ForeignAlbumTests::test_foreign_export_and_download_answer_not_found` |
| Estado | Cubierto por prueba automática |

**Total: 7 CP; 23 pruebas automáticas nuevas** en
`albums/tests/test_png_export.py` (una de ellas añadida en la verificación
final del Módulo 6).

Pruebas de apoyo sin CP propio: sin traducciones aprobadas en una página
limpia no hay PNG (`test_png_needs_something_to_draw`), el historial muestra
el formato (`test_history_shows_the_format_of_each_export`), la miniatura de
16 bits no sale blanca (`test_a_sixteen_bit_thumbnail_is_not_white`), aviso
de «Limpieza manual» (`test_manual_cleaning_is_warned`) y página traducida
sin imagen limpia (`test_an_uncleaned_page_is_exported_untranslated_and_warned`).

Evidencia del Quality Gate:
[`etapa-90/`](evidence/sprint-3/etapa-90/E90-quality-gate-RESUMEN.md) y, tras
BUG-096, [`etapa-90b/`](evidence/sprint-3/etapa-90b/E90b-quality-gate-RESUMEN.md).

## Resultado de la ejecución manual

Todos los CP de HU-90 tienen cobertura automática completa. Esta tabla
registra la verificación en el navegador. La del 11/11/2026 se hizo en local; la
versión desplegada sigue pendiente.

| CP | Comprobación | Fecha | Responsable | Resultado | Evidencia |
|---|---|---|---|---|---|
| CP-90.2 | Descargar el ZIP y abrirlo con el explorador del sistema | 11/11/2026 | Juan Pablo | Correcto | Lista de comprobación del Módulo 6 ejecutada en local (`runserver`, proveedores simulados). Resultado informado por el responsable; sin capturas versionadas |
| CP-90.3 | Abrir los PNG en un visor y comprobar resolución y modo | | | Pendiente | La lista del 11/11/2026 comparó el PNG con el editor (CP-89.8), pero no incluía comprobar a mano la resolución ni el modo; los cubre `ImageFidelityTests` |

## Seguridad y almacenamiento

- La exportación y la descarga filtran por `album__owner`; lo ajeno responde
  404, igual que el DOCX de HU-28.
- El ZIP se guarda en el almacenamiento privado del álbum y solo se entrega
  por la vista de descarga autenticada.
- Las páginas se dibujan una a una y cada imagen se cierra al terminar, para
  no cargar el álbum entero en memoria.
