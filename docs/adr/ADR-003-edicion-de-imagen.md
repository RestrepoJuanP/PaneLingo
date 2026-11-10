# ADR-003 — Componer la página traducida a partir de capas

- **Estado:** provisional; autorizado para implementación, aprobación formal
  del Product Owner pendiente
- **Fecha:** 9 de noviembre de 2026
- **Épica:** EP-08 Edición de imagen
- **Requisito:** RF-15

## Contexto

El Product Owner espera descargar páginas limpias y traducidas como PNG. El
flujo actual detecta, corrige, traduce y aprueba texto, pero la exportación de
HU-27 y HU-28 solo produce un DOCX. Generar una imagen completa con IA no es
repetible, puede alterar el dibujo y dificulta corregir una palabra sin rehacer
la página.

El issue #84 conserva la aprobación formal del PO como pendiente. El equipo
decidió comenzar la implementación usando esta decisión como línea técnica
provisional. Si el PO solicita un cambio, debe registrarse en este ADR antes de
modificar las historias dependientes.

## Decisión

### Composición por capas

La página final se obtiene al combinar:

1. La imagen original de `ComicPage.image`.
2. Una imagen limpia, que se añadirá en HU-88.
3. Los textos traducidos y sus propiedades de maquetación, que se añadirán en
   HU-87 y HU-89.

### Flujo

El workspace evoluciona por cuatro pasos que permiten volver atrás:

1. Detección.
2. Traducción.
3. Maquetación.
4. Exportación.

HU-85 añade regiones omitidas por el OCR y HU-86 permite eliminar falsos
positivos o conservar texto sin traducir.

### Coordenadas y renderizado

- Todas las coordenadas se guardan en píxeles de la imagen original.
- El navegador solo transforma esas coordenadas para el zoom.
- El ajuste del texto se calcula en el servidor con Pillow.
- La vista previa y la exportación comparten el mismo algoritmo.
- Las fuentes deben tener licencia SIL OFL 1.1 y vivir en `static/fonts/`.

### Procesamiento

- La limpieza de páginas y la generación de ZIP son tareas de Huey.
- Añadir una única región puede ejecutar OCR durante la petición porque solo
  procesa un recorte pequeño.
- Todos los proveedores externos permanecen detrás de adaptadores y las
  pruebas usan proveedores simulados.
- La IA de limpieza es opcional, se aplica región por región y exige aceptar
  o descartar el resultado.

## Orden de implementación

1. HU-85 — Añadir una región manual.
2. HU-86 — Eliminar y marcar “No traducir”.
3. HU-87 — Vista previa traducida.
4. HU-88 — Limpiar el texto original.
5. HU-89 — Editor de maquetación.
6. HU-90 — Exportar PNG en ZIP.
7. HU-91 — Limpieza con IA, opcional y precedida por un spike.

HU-85, HU-86 y HU-87 no dependen entre sí. HU-88 depende de HU-86; HU-89
depende de HU-87 y HU-88; HU-90 depende de HU-89; HU-91 depende de HU-88.

## Consecuencias

- Se amplía el alcance del producto con RF-15.
- HU-27 y HU-28 conservarán DOCX y ganarán un segundo formato en HU-90.
- La regla de “Completado” de HU-25 y HU-26 no cambia en esta épica. Exigir
  páginas maquetadas queda como propuesta abierta para el PO (sección
  «Decisiones pendientes de cerrar», P1-bis).
- Pillow sigue siendo la única dependencia obligatoria de imagen.
- OpenCV solo puede incorporarse si el spike de HU-91 lo justifica y pasa la
  auditoría de dependencias.

## Validación pendiente

- [ ] Aprobación formal del Product Owner.
- [ ] Actualización de RF-15 y del alcance en la Wiki.
- [ ] Confirmación de las fuentes y sus licencias antes de HU-87.
- [ ] Decisión del proveedor para HU-91 después del spike.

## Decisiones cerradas antes de HU-89

Acordadas por el equipo el 10 de noviembre de 2026. HU-89 y HU-90 se
implementan con ellas como **supuestos**, aunque el DoR de ambas no está
completo: quedan pendientes de confirmar con el equipo (boceto del panel de
propiedades de HU-89) y con el PO (nombres de archivo de HU-90). El boceto del
panel se diseña en el módulo de HU-89 con los componentes y tokens existentes
y se revisa antes de implementarlo. Si el equipo o el PO cambian alguna de
estas decisiones, el cambio se anota aquí antes de tocar el código.

### P1 — Estado “Maquetada” de una página (HU-89)

- Se guarda en un campo `ComicPage.typeset_approved_at` (nulo = sin maquetar),
  separado de `ComicPage.Status`, como `TranslationState` y `CleaningState`.
  Un valor nuevo de `Status` obligaría a revisar cada comparación con
  `Status.APPROVED` (aprobación de traducciones, `was_processed`, filtros,
  progreso, procesamiento y regiones manuales).
- La rejilla del álbum muestra “Maquetada” cuando la página está en
  `APPROVED` y tiene `typeset_approved_at`.
- El campo vuelve a nulo cuando se guarda un cambio de maquetación o de texto
  de cualquier región, cuando la página sale de `APPROVED`, cuando se vuelve a
  limpiar la página y cuando se reprocesa.
- **La regla de “Completado” de HU-25 y HU-26 no se toca en ningún módulo de
  EP-08**, tampoco en HU-90: ninguna historia pendiente lo pide. Queda como
  propuesta abierta para el PO (P1-bis).

### P2 — Tamaño de letra (HU-89)

- Ajuste automático: entre 8 y 72 (`MIN_FONT_SIZE`, `MAX_FONT_SIZE`) y como
  máximo el 70 % del alto de la caja, sin cambios respecto a HU-87.
- Tamaño fijo: entre 8 y 200, con una constante nueva `MAX_FIXED_FONT_SIZE`.
  `MAX_FONT_SIZE` no se renombra.
- La unidad son píxeles de la imagen original, no de la pantalla.
- Un tamaño fijo que no cabe en su caja no se reduce: se muestra el aviso
  “El texto no cabe”, como en la vista previa.

### P3 — Nombres del ZIP y de los PNG (HU-90)

- ZIP: `{álbum}_{idioma}_{fecha}_png.zip`, generado por
  `export_download_name`, que elige la extensión según `AlbumExport.format`.
  El nombre del DOCX no cambia.
- PNG: `pagina-{page_number:03d}.png` con el número real de la página, que no
  se renumera al borrar páginas (HU-10). Con más de 999 páginas el número se
  alarga solo.
- El ZIP no incluye la imagen limpia sin texto (carpeta `limpias/`) mientras
  el PO no la pida.

### P4 — Spike de HU-91

- El spike compara Gemini con edición de imagen y el *inpainting* local con
  OpenCV. **OpenCV es la opción por defecto.**
- Gemini solo se elige si su nivel gratuito permite editar imágenes con un
  límite diario razonable **y** el equipo acepta enviar recortes de páginas a
  un servicio externo.
- Si el spike no puede comprobar Gemini por falta de clave o de cuota, gana
  OpenCV y se anota así en este ADR.
- Referencia: el 10 de noviembre de 2026, `pip-audit` no encontró
  vulnerabilidades conocidas en `opencv-python-headless` 5.0.0.93 (licencia
  Apache 2.0). Se repite la auditoría en el PR que añada la dependencia.

### P5 — Contenido congelado de la exportación PNG (HU-90)

Al pedir la exportación se congelan en `AlbumExport.snapshot` el texto, la
maquetación de cada región y el nombre de la imagen limpia de cada página. Si
ese archivo cambia o desaparece mientras la tarea se ejecuta, la exportación
falla con el mensaje de CA-90.6 y no deja ningún ZIP a medias.

### P6 — Regiones sin traducción aprobada (HU-90)

`render_page` vuelve a pegar el recorte de la imagen original en las regiones
sin traducción aprobada, igual que hace la limpieza con las regiones “No
traducir”. Es **una sola función compartida** entre `albums/cleaning.py` y
`albums/typesetting.py`, no dos implementaciones.

### P7 — Condiciones para “Aprobar página” en Maquetación (HU-89)

“Aprobar página” exige que exista la imagen limpia **y** que todas las
traducciones estén aprobadas (CA-89.7). Si hay regiones en “Limpieza manual”,
avisa sin bloquear.

### P8 — Identificadores de fuente (HU-89)

`TextRegion.font_family` admite `comic-neue`, `comic-neue-bold`,
`comic-neue-italic` y `bangers`. El valor vacío significa “la fuente por
defecto del tipo de región” (Comic Neue regular para diálogo, cursiva para
narración).

## Decisiones pendientes de cerrar

### P1-bis — “Completado” exige páginas maquetadas (propuesta para el PO)

**Propuesta:** un álbum solo está “Completado” cuando todas sus páginas están
aprobadas **y** maquetadas; las páginas sin regiones que traducir contarían
como maquetadas, porque no tienen nada que maquetar.

**Qué cambiaría en CA-26.1** (Wiki y issue #26): la fila “todas están
‘Aprobadas’ → Completado” pasaría a “todas están ‘Aprobadas’ y ‘Maquetadas’ →
Completado”, y haría falta una fila nueva “todas están ‘Aprobadas’ y alguna sin
maquetar → En revisión” (u otro estado que decida el PO). HU-25 tendría que
decidir si el porcentaje cuenta páginas aprobadas o maquetadas.

**Pruebas que habría que ajustar:**

- `albums/tests/test_library_progress.py`: `DerivedStatusTests`
  (`test_status_follows_the_pages`, `test_processed_but_not_approved_is_in_review`),
  `LibraryFilterTests` (CA-26.2, filtro “Completados” y tarjeta con
  “Completado”), `AlbumApprovalProgressTests` (CP-25.1 a CP-25.4) y
  `ApprovedReviewAccountingTests` (CP-26.1 / BUG-072).
- `albums/tests/test_resume_work.py`:
  `test_empty_and_completed_albums_do_not_offer_continue`.
- `albums/tests/test_archive.py`: `test_it_comes_back_with_its_derived_status`.
- `albums/tests/test_processing.py`: `test_the_page_is_completed_with_zero_regions`.

**Decisión:** pendiente del PO. Hasta entonces, `derive_status`
(`albums/insights.py`) y `progress_percentage` no cambian.

### Confirmaciones pendientes del DoR

- [ ] El equipo revisa el boceto del panel de propiedades y de las pestañas
      de HU-89.
- [ ] El PO confirma los nombres de archivo de HU-90 y si quiere la página
      limpia en el ZIP.
- [ ] Resultado del spike de HU-91 (P4).
