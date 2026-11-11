# ADR-003 — Componer la página traducida a partir de capas

- **Estado:** provisional; autorizado para implementación, aprobación formal
  del Product Owner pendiente
- **Implementación (10 de noviembre de 2026):** HU-85 a HU-90 terminadas
  (HU-85 a HU-88 fusionadas en `main`; HU-89 y HU-90 en PR); HU-91 descartada
  tras el spike (P4); BUG-096 corregido (P9)
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
  o descartar el resultado. **No se implementa:** HU-91 quedó descartada
  tras el spike (P4).

## Orden de implementación

1. HU-85 — Añadir una región manual.
2. HU-86 — Eliminar y marcar “No traducir”.
3. HU-87 — Vista previa traducida.
4. HU-88 — Limpiar el texto original.
5. HU-89 — Editor de maquetación.
6. HU-90 — Exportar PNG en ZIP.
7. HU-91 — Limpieza con IA, opcional y precedida por un spike. **Descartada
   tras el spike** (ver P4).

HU-85, HU-86 y HU-87 no dependen entre sí. HU-88 depende de HU-86; HU-89
depende de HU-87 y HU-88; HU-90 depende de HU-89; HU-91 depende de HU-88.

## Consecuencias

- Se amplía el alcance del producto con RF-15.
- HU-27 y HU-28 conservarán DOCX y ganarán un segundo formato en HU-90.
- La regla de “Completado” de HU-25 y HU-26 no cambia en esta épica. Exigir
  páginas maquetadas queda como propuesta abierta para el PO (sección
  «Pendiente de decisión del PO», P1-bis).
- Pillow sigue siendo la única dependencia obligatoria de imagen.
- OpenCV no se incorpora: el spike de HU-91 no cumplió su criterio y la
  historia quedó descartada (P4).

## Validación pendiente

- [ ] Aprobación formal del Product Owner (issue #84, abierto).
- [ ] Actualización de RF-15 y del alcance en la Wiki. El texto listo para
      pegar está en `docs/WIKI_EP08_ACTUALIZACIONES.md`; la Wiki aún no se
      ha editado.
- [x] Confirmación de las fuentes y sus licencias antes de HU-87: Comic Neue
      (Regular, Bold, Italic) y Bangers, con sus licencias SIL OFL 1.1
      (`OFL.txt` y `OFL-Bangers.txt`), en `static/fonts/` desde HU-87.
- [x] Decisión del proveedor para HU-91 después del spike: ninguno; HU-91
      descartada (P4).

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

**Resultado del spike (10 de noviembre de 2026) — Gemini, descartado.** Según
la [página oficial de precios de la API de Gemini](https://aistudio.google.com/docs/pricing),
consultada ese día, ninguno de los modelos que generan o editan imágenes
(Gemini 2.5 Flash Image, 3.1 Flash Image, 3.1 Flash Lite Image, 3 Pro Image y
Nano Banana 2.1) tiene nivel gratuito: la columna *Free Tier* dice "Not
available" y el precio va de 0,034 a 0,24 USD por imagen. Guías de terceros
de 2026 coinciden ([memetik.ai](https://www.memetik.ai/guides/gemini-api-free-tier-limits),
[aifreeapi.com](https://www.aifreeapi.com/en/posts/gemini-image-free-tier-2026)).
Además, el proyecto no tiene `GEMINI_API_KEY` configurada, así que no se hizo
ninguna llamada real ni se envió ninguna imagen. Por la regla anterior,
Gemini no puede elegirse: la comparación queda limitada a OpenCV.

**Resultado del spike (10 de noviembre de 2026) — OpenCV no cumple el
criterio: HU-91 queda descartada.**

*Criterio, fijado antes de ver resultados.* La HU se implementa si, con UNA
sola configuración por defecto, al menos dos de tres regiones quedan
aceptables al 100 % de zoom: sin rastro legible del texto y sin borrar
líneas del dibujo que se noten fuera de lo que antes tapaba el texto.

*Material.* Tres regiones reales de páginas de *Pepper & Carrot*, episodio 1
(Pepper & Carrot, David Revoy, CC BY 4.0, www.peppercarrot.com), cargadas en
una base de datos local y marcadas “Limpieza manual” por la limpieza de
HU-88. Las imágenes y los resultados se quedaron en una carpeta temporal: no
entran al repositorio ni se usan como fixture.

| Caso | Página (1200 × 1660 px) | Caja (x, y, ancho, alto) | Texto frente al fondo |
|---|---|---|---|
| Onomatopeya sobre fondo con detalle (“SPLASH”) | E01P02 | 692, 1360, 70, 54 | Más claro, junto a destellos |
| Texto sobre fondo casi plano (firma “WWW.PEPPERCARROT.COM 05/2014”) | E01P03 | 800, 1316, 110, 32 | Más claro, sobre un degradado |
| Texto sobre líneas finas (“SHH SHH”) | E01P01 | 513, 238, 64, 56 | Más oscuro, sobre el marco de una ventana |

*Configuraciones probadas.* `cv2.inpaint` (radio 3) con `INPAINT_TELEA` e
`INPAINT_NS`, recorte con 24 px de margen y máscara limitada a la caja:

- Las pedidas: máscara de píxeles oscuros (gris < 90 o < 130), dilatación 1
  o 2 (8 configuraciones por región).
- Extra: máscara por contraste con el fondo local (|gris − mediana de
  21 px| > 30 o > 50), dilatación 1 o 2 (8 configuraciones más).

*Resultado.* **0 de 3 regiones aceptables con cualquier configuración.**

- Máscara oscura: en “SPLASH” y en la firma selecciona el **fondo** y no el
  texto, que es más claro; extiende el color del texto o deja una franja
  plana muy visible. En “SHH” el texto (gris ≈ 150) no entra en la máscara y
  queda intacto.
- Mejor candidata, contraste u30 d2 con TELEA: el texto deja de leerse en
  “SPLASH” y “SHH”, pero quedan manchas del color del texto y se pierde parte
  de un destello; en la firma quedan restos legibles (“…RCARROT.CO…”).
- Tiempo: mediana de 0,6 a 2,6 ms por región, máximo 4,5 ms. El tiempo no
  era el problema.

*Motivo técnico.* La máscara por umbral no separa el texto del dibujo: o
confunde el fondo con la tinta, o no capta el texto, y en letras gruesas el
color del texto queda dentro de la máscara y el *inpainting* lo propaga.
Ajustar umbrales y dilataciones no cambia ese límite.

*Alternativas que sí podrían funcionar, con su coste.*

- Segmentar el texto por color (agrupar los colores de la caja y quedarse
  con el del texto): semanas de trabajo y ajustes por obra, y seguiría
  dependiendo de OpenCV.
- *Inpainting* con aprendizaje automático (por ejemplo LaMa): necesita
  PyTorch y los pesos del modelo, varios GB de dependencias, y conviene una
  GPU para tiempos aceptables.

*Peso.* `opencv-python-headless` 5.0.0.93 más `numpy` son 56 MB en wheels y
unos 170 MB instalados (`pip-audit` sin vulnerabilidades conocidas). El
despliegue público está pendiente y los planes gratuitos de alojamiento
suelen limitar el tamaño; no compensa para una historia *Could* que no
cumple su criterio.

*Alternativa que ya ofrece el producto.* La caja de la traducción en el
editor de HU-89 puede taparse y moverse sobre el texto original, y las
regiones en “Limpieza manual” se avisan antes de aprobar la maquetación (P7)
y antes de exportar (P9), para que el traductor las resuelva fuera de
PaneLingo si lo necesita.

*Decisión.* HU-91 (#91) no se implementa: se cierra como “no planificada”
con enlace a este ADR. No se añade ninguna dependencia. Si en el futuro se
retoma, debe partir de un enfoque distinto al de la máscara por umbral y
repetir este criterio.

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

### P9 — Precisiones de HU-90 (exportar PNG)

Acordadas el 10 de noviembre de 2026 al implementar HU-90:

- **Precisión de CA-90.4 — maquetación guardada, no una automática nueva.**
  Una página sin maquetar se exporta con la maquetación que tiene guardada,
  que es la que se ve en el editor (y la automática si nadie la tocó). Una
  automática “literal” descartaría los ajustes del traductor y rompería
  CA-89.8. El aviso dice: “1 página no está maquetada: se exportará con la
  maquetación que se ve en el editor. Las regiones sin traducción aprobada
  conservarán el texto original.” No cuentan como pendientes las páginas sin
  regiones que traducir (sin regiones, solo “No traducir” o vacías).
- **Página traducida sin imagen limpia:** se exporta como la original, sin
  textos, y se avisa (“1 página no está limpia: se exportará sin traducir.”).
  Dibujar la traducción sobre el texto original la haría ilegible, y
  bloquear dejaría sin exportar el resto del álbum. Es la regla de P6
  aplicada a la página entera. `render_page` no dibuja textos sin capa limpia.
- **Requisito para exportar en PNG:** al menos una traducción aprobada y no
  vacía en una página limpia, la misma regla que el DOCX un poco más
  estricta: sin ella, el ZIP sería una copia de las originales.
- **Aviso adicional:** las regiones en “Limpieza manual” se avisan, sin
  bloquear, antes de confirmar.
- **Modos de color.** `1`, `L`, `LA`, `I;16*`, `I` y `F` salen en `L`; las
  paletas (`P`, `PA`) salen en `L` si todos los colores que usan son grises
  (`getcolors(maxcolors=256)`) y en `RGB` si no; el resto, en `RGB`. Nunca hay
  canal alfa: se descarta igual que en la limpieza y en el editor.
- **Imágenes de 16 bits.** `convert()` de Pillow recorta los modos de 16 y 32
  bits en vez de escalarlos: un PNG gris de 16 bits salía casi blanco en la
  miniatura, la capa limpia, el editor y el PNG. `albums/imaging.py`
  (`to_rgb`) los escala a 8 bits y lo usan la miniatura, la limpieza, el
  recorte del OCR manual y el dibujo de la página, para que editor y PNG
  coincidan. Las capas limpias de páginas de 16 bits creadas antes de este
  cambio siguen recortadas hasta que se vuelvan a limpiar.
  La clasificación globo/narración (`albums/ocr/layout.py`) también recortaba
  y la corrigió BUG-096: las regiones de páginas de 16 bits procesadas antes
  de esa corrección siguen clasificadas como globo hasta reprocesar la página.
  **Reprocesar no es gratis:** borra todas las regiones de la página, con sus
  traducciones, su maquetación y las regiones manuales, quita la aprobación
  de la maquetación y descarta la capa limpia (`save_regions`, en
  `albums/processing.py`). En páginas ya trabajadas conviene valorarlo antes;
  hoy no hay otra forma de corregir el tipo (propuesta P10).

## Pendiente de decisión del PO

Propuestas abiertas que necesitan una decisión del Product Owner. Ninguna se
implementa hasta que el PO decida y, si hace falta, se redacte la historia
con sus CA y CP. Las de EP-08 están detalladas aquí; las de sprints
anteriores se resumen con un enlace al documento donde se plantearon, y
siguen abiertas porque el repositorio no registra ninguna decisión sobre
ellas.

| Propuesta | Origen | Qué se decide |
|---|---|---|
| P1-bis | EP-08 (HU-89) | Si «Completado» exige además páginas maquetadas. |
| P3-bis | EP-08 (HU-90) | Si se confirman los nombres del ZIP y de los PNG, y si el ZIP incluye la carpeta `limpias/`. |
| P10 | EP-08 (BUG-096) | Si se permite cambiar el tipo globo/narración de una región sin reprocesar. |
| Aprobación de ADR-003 | EP-08 (#84) | Aprobación formal de esta decisión. |
| Juego de páginas de prueba y umbrales de OCR | ADR-001, S5 y S7 | Quién aporta el juego de páginas y qué umbral de confianza (70 % provisional) y de precisión por idioma se acepta (CA-13.3 y CA-13.4). |
| Riesgo de privacidad de Gemini y supuestos T1 a T3 | ADR-002, §2.3 y §5 | Aceptar el riesgo del nivel gratuito; traducción vacía (T1), sin «Aprobar todas» (T2) y HU-17 y HU-18 fusionadas (T3). |
| Reordenar o insertar páginas | Sprint 1, propuesta 2.4 | Si entra como historia y si renumera las páginas. |
| Perfil y preferencias | Sprint 1, propuesta 2.5 | Si entra como historia y dónde viven los idiomas predeterminados. |

Las propuestas 2.1, 2.2 y 2.3 del Sprint 1 ya no están abiertas: el estado
del álbum pasó a derivarse del avance y los filtros llegaron con HU-26, y
eliminar álbumes llegó con HU-20. HU-49 y HU-50, pedidas en la review del
Sprint 1, están cerradas.

Documentos de origen: [ADR-001](ADR-001-proveedor-ocr-y-tareas-asincronas.md),
[ADR-002](ADR-002-traduccion-asistida-por-ia.md) y
[Sprint 1 — propuestas abiertas](../WIKI_SPRINT_1_DESARROLLO.md#2-propuestas-abiertas-para-el-product-owner).


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

### P3-bis — Nombres de archivo y carpeta `limpias/` del ZIP (HU-90)

**Situación:** HU-90 se implementó con los nombres de P3 como supuesto,
porque el DoR de la historia pedía que el PO los confirmara y esa
confirmación no consta: `{álbum}_{idioma}_{fecha}_png.zip` y
`pagina-{page_number:03d}.png`. El ZIP no incluye la imagen limpia sin texto.

**Qué se decide:** si los nombres sirven tal cual y si el ZIP debe llevar
también una carpeta `limpias/` con cada página limpia, sin textos. El PO la
mencionó en la entrevista del 08/08/2026 («las páginas limpias del texto en
su lenguaje original»).

**Qué cambiaría:** los nombres solo tocan `export_download_name` y
`png_name`, en `albums/exporting.py`, más
`ArchiveContentTests`. Añadir `limpias/` sería un criterio nuevo de HU-90 con
su CP.

**Decisión:** pendiente del PO.

### P10 — Cambiar el tipo de una región sin reprocesar (propuesta para el PO)

**Carencia:** el tipo globo/narración (`TextRegion.kind`) lo asigna solo la
heurística de luminosidad (`albums/ocr/layout.py`, supuesto S3) al procesar
la página o al añadir una región manual. HU-15 corrige el texto, no el tipo,
y ninguna pantalla permite cambiarlo, aunque ADR-001 (S3) suponía que el tipo
sería «corregible a mano en HU-15». El tipo decide la fuente por defecto de
la maquetación (P8: regular para diálogo, cursiva para narración). Cuando la
heurística se equivoca, como con las páginas de 16 bits anteriores a BUG-096
(P9), la única salida es reprocesar la página y perder su trabajo.

**Propuesta:** permitir cambiar el tipo de una región desde el workspace, sin
reprocesar ni tocar su texto, traducción ni maquetación guardada.

**Decisión:** pendiente del PO. Solo se documenta: no tiene HU, CA ni CP y no
se implementa hasta que el PO la acepte y se redacte la historia.

## Confirmaciones pendientes del DoR

- [ ] El equipo revisa el boceto del panel de propiedades y de las pestañas
      de HU-89.
- [ ] El PO confirma los nombres de archivo de HU-90 y si quiere la página
      limpia en el ZIP (P3-bis).
- [x] Resultado del spike de HU-91 (P4): descartada.
