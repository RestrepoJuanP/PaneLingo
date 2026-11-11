# Textos para la Wiki y los issues — Cierre de EP-08

> Bloques listos para pegar. **No se ha editado la Wiki ni ningún issue**: lo
> hace el equipo, copiando cada bloque en el destino indicado. Los formatos
> imitan los de las páginas actuales de la Wiki ([Sprint 0](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-0)
> y [Backlog y tablero](https://github.com/RestrepoJuanP/PaneLingo/wiki/Backlog-y-tablero)).
>
> Los bloques 1 y 2 aplican la sección «Consecuencias» de
> [ADR-003](adr/ADR-003-edicion-de-imagen.md). La aprobación formal del ADR
> por el PO sigue pendiente (issue [#84](https://github.com/RestrepoJuanP/PaneLingo/issues/84)):
> si el equipo prefiere esperar a esa aprobación, los bloques 1 y 2 se pegan
> después y el bloque 4 se pega ya, porque recoge el estado real.

Contenido:

1. [RF-15 en los requisitos funcionales del Sprint 0](#1-rf-15-en-los-requisitos-funcionales-del-sprint-0)
2. [Cambio en el Alcance del Sprint 0](#2-cambio-en-el-alcance-del-sprint-0)
3. [Entrada de EP-08 para la página del Sprint 3](#3-entrada-de-ep-08-para-la-página-del-sprint-3)
4. [Nota de estado en Backlog y tablero](#4-nota-de-estado-en-backlog-y-tablero)
5. [Textos de cierre y comentarios de issues](#5-textos-de-cierre-y-comentarios-de-issues)

---

## 1. RF-15 en los requisitos funcionales del Sprint 0

**Destino:** página [Sprint 0](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-0),
sección «Requisitos funcionales», después del punto 14.

```markdown
15. RF-15 El usuario debe poder obtener las páginas traducidas como imágenes: el sistema limpia el texto original de cada región, permite maquetar la traducción sobre la página (posición, tamaño, fuente, alineación y color) y exporta las páginas resultantes en PNG con la resolución y el modo de color de la original. *(Añadido en el Sprint 3 con la épica EP-08 Edición de imagen; ver [ADR-003](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md).)*
```

---

## 2. Cambio en el Alcance del Sprint 0

**Destino:** página [Sprint 0](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-0),
sección «Alcance».

**a) Primer párrafo.** Sustituir «descrito en los requisitos RF-01 a RF-14»
por «descrito en los requisitos RF-01 a RF-15» y «y exportación de
resultados» por:

```markdown
y exportación de resultados, tanto en texto (DOCX) como en páginas traducidas (PNG).
```

**b) Lista de exclusiones.** Eliminar esta viñeta:

```markdown
- Reinserción automática del texto traducido dentro de la imagen. El MVP exporta el texto traducido asociado a cada región, no una imagen recompuesta.
```

**c) Nota al final de la sección**, después del párrafo del objetivo del MVP:

```markdown
> **Cambio de alcance (Sprint 3).** La reinserción del texto traducido en la imagen, que el MVP dejaba fuera, entró en el alcance con RF-15 y la épica EP-08 Edición de imagen, a pedido del PO (entrevista del 08/08/2026 y reunión del 04/08/2026) y como deuda acordada en la [Review del Sprint 2](Acta-Review-Sprint-2). La página se **compone por capas** (original, imagen limpia y textos maquetados) y no se genera con un modelo de imagen. La limpieza con IA del texto que está sobre el dibujo (HU-91) se evaluó con un *spike* y se descartó. Decisiones: [ADR-003](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md).
```

---

## 3. Entrada de EP-08 para la página del Sprint 3

**Destino:** página del Sprint 3, dentro del incremento de producto. El
borrador completo de esa página es
[`WIKI_SPRINT_3_CIERRE.md`](WIKI_SPRINT_3_CIERRE.md), que ya incluye EP-08;
este bloque sirve si se prefiere una sección propia de la épica.

```markdown
### EP-08 Edición de imagen

**Requisito:** RF-15. **Decisiones:** [ADR-003](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md) (aprobación formal del PO pendiente, issue [#84](https://github.com/RestrepoJuanP/PaneLingo/issues/84)).

La épica añade al espacio de trabajo el flujo **Detección → Traducción → Maquetación → Exportar**. La página traducida se compone a partir de tres capas: la imagen original, una imagen limpia sin el texto original y los textos traducidos con su caja y su estilo. Un único algoritmo de maquetación, en el servidor, alimenta la vista previa, el editor y la exportación, así que lo que se ve es lo que se exporta.

| Historia | Capacidad entregada | Casos de prueba | Estado |
|---|---|---|---|
| [HU-85](https://github.com/RestrepoJuanP/PaneLingo/issues/85) | Añadir a mano una región que el OCR no detectó | CP-85.1 a CP-85.7 | Entregada |
| [HU-86](https://github.com/RestrepoJuanP/PaneLingo/issues/86) | Eliminar falsos positivos con deshacer y marcar «No traducir» | CP-86.1 a CP-86.6 | Entregada |
| [HU-87](https://github.com/RestrepoJuanP/PaneLingo/issues/87) | Vista previa de la página traducida, con fuentes SIL OFL | CP-87.1 a CP-87.7 | Entregada |
| [HU-88](https://github.com/RestrepoJuanP/PaneLingo/issues/88) | Limpiar el texto original en una capa aparte | CP-88.1 a CP-88.8 | Entregada |
| [HU-89](https://github.com/RestrepoJuanP/PaneLingo/issues/89) | Maquetar cada traducción sobre la imagen y aprobar la página como «Maquetada» | CP-89.1 a CP-89.9 | Entregada; partes manuales de CP-89.2, 89.3, 89.6 y 89.8 pendientes de ejecutar |
| [HU-90](https://github.com/RestrepoJuanP/PaneLingo/issues/90) | Exportar las páginas traducidas como PNG en un ZIP, junto al DOCX | CP-90.1 a CP-90.7 | Entregada |
| [HU-91](https://github.com/RestrepoJuanP/PaneLingo/issues/91) | Limpiar con IA el texto que está sobre el dibujo (*Could*) | — | **Descartada** tras el *spike* |

**HU-91, descartada.** El *spike* comparó Gemini con edición de imagen y el *inpainting* local con OpenCV. Gemini no tiene nivel gratuito para editar imágenes y el proyecto no tiene clave, así que no se envió ninguna imagen. OpenCV dejó aceptables 0 de 3 regiones reales frente a un criterio de 2 de 3 fijado de antemano: la máscara por umbral no separa el texto del dibujo. No se añadió ninguna dependencia. Las regiones que la limpieza deja en «Limpieza manual» se avisan antes de aprobar la maquetación y de exportar. Detalle en [ADR-003, P4](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91).

**Corrección BUG-096.** Las páginas en gris de 16 bits se veían casi blancas porque Pillow recorta esos modos en lugar de escalarlos; HU-90 lo corrigió en la miniatura, la limpieza, el recorte del OCR manual y el dibujo de la página, y BUG-096 en la clasificación globo/narración, donde todas las regiones de esas páginas salían como globo. Las regiones procesadas antes de la corrección siguen así hasta reprocesar la página, lo que borra su trabajo; la propuesta de cambiar el tipo sin reprocesar queda para el PO (ADR-003, P10).

**Pruebas.** 123 pruebas automáticas nuevas (678 en total), cobertura local del 97 % y Quality Gate 7/7. Casos y trazabilidad: [CP de HU-89](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-89.md), [CP de HU-90](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-90.md) y [reporte de pruebas del Sprint 3](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_REPORTE_PRUEBAS.md).

**Pendiente de decisión del PO:** «Completado» exige páginas maquetadas (P1-bis), nombres del ZIP y carpeta `limpias/` (P3-bis) y cambiar el tipo de una región sin reprocesar (P10).
```

---

## 4. Nota de estado en Backlog y tablero

**Destino:** página [Backlog y tablero](https://github.com/RestrepoJuanP/PaneLingo/wiki/Backlog-y-tablero),
sección «Épica EP-08 Edición de imagen». Sustituir la nota «Propuesta
pendiente de aprobación del PO» por:

```markdown
> **Estado al cierre del Sprint 3.** HU-85 a HU-90 entregadas; HU-91 descartada tras el *spike* ([ADR-003, P4](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91)). Las decisiones de diseño están en [ADR-003](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md), autorizado para implementación y con la aprobación formal del PO todavía pendiente ([#84](https://github.com/RestrepoJuanP/PaneLingo/issues/84)). [Sprint 0 › Alcance](Sprint-0#alcance) y el requisito RF-15 se actualizaron con el cambio de alcance.
```

Y en la tabla de la épica, la fila 7 pasa a:

```markdown
| 7 | ~~[HU-91 — Limpiar con IA el texto que está sobre el dibujo](https://github.com/RestrepoJuanP/PaneLingo/issues/91)~~ **Descartada** tras el *spike* | Could | L | HU-88 |
```

---

## 5. Textos de cierre y comentarios de issues

### #89 — HU-89 (lo cierra su PR)

El PR de HU-89 lleva `Closes #89`. Comentario para dejar en el issue al
fusionarlo:

```markdown
Entregada en el PR de `feature/HU-89-typesetting-editor`.

- Pestaña **Maquetación** en el espacio de trabajo (`?paso=maquetacion`): caja, fuente, tamaño automático o fijo, alineación y color de cada texto, edición del texto sobre la imagen, deshacer (20 pasos), **Restablecer** y **Aprobar página** («Maquetada»).
- Un único algoritmo de maquetación en `albums/typesetting.py`; el navegador pinta lo que devuelve el servidor (ADR-003).
- CP-89.1 a CP-89.9 con prueba automática (52 pruebas nuevas, una de ellas de la verificación final). Las partes interactivas de CP-89.2, CP-89.3, CP-89.6 y CP-89.8 se verifican a mano con el procedimiento de `docs/WIKI_SPRINT_3_CP_HU-89.md`, que tiene la tabla de resultados para rellenar.
- Supuestos de ADR-003 P1, P2, P7 y P8. El boceto del panel de propiedades sigue pendiente de revisión del equipo (DoR).
```

### #90 — HU-90 (lo cierra su PR)

El PR de HU-90 lleva `Closes #90`. Comentario para dejar en el issue al
fusionarlo:

```markdown
Entregada en el PR de `feature/HU-90-png-export`.

- **Revisión y exportación** ofrece «Documento de texto (DOCX)», que no cambia, y «Páginas traducidas (PNG en un ZIP)».
- Cada PNG tiene la resolución de la original, sale en `L` o `RGB` sin alfa y es idéntico a lo que muestra el editor (`render_page`).
- Precisión de CA-90.4 (ADR-003, P9): una página sin maquetar se exporta con su maquetación **guardada**, la que se ve en el editor.
- CP-90.1 a CP-90.7 con prueba automática (23 pruebas nuevas, una de ellas de la verificación final).
- Nombres de archivo y carpeta `limpias/` como supuesto, pendientes de confirmar por el PO (ADR-003, P3-bis).
- Las páginas grises de 16 bits se escalan a 8 bits; la clasificación de regiones se completó en BUG-096.
```

### #91 — HU-91 (cerrar como «Not planned»)

Cerrar el issue a mano con el motivo **Not planned** y este comentario:

```markdown
Se cierra como **no planificada** tras el *spike* del 10/11/2026 (ADR-003, P4).

- **Gemini:** ningún modelo que edite imágenes tiene nivel gratuito y el proyecto no tiene `GEMINI_API_KEY`; no se envió ninguna imagen.
- **OpenCV (`cv2.inpaint`):** 0 de 3 regiones reales de *Pepper & Carrot* (David Revoy, CC BY 4.0) aceptables con cualquiera de las 16 configuraciones, frente a un criterio de 2 de 3 fijado antes de ver resultados. La máscara por umbral no separa el texto del dibujo; las alternativas viables (segmentación por color o LaMa con PyTorch) cuestan semanas o varios GB de dependencias.
- No se añade ninguna dependencia. Las regiones en «Limpieza manual» se avisan antes de aprobar la maquetación y de exportar, y la caja del editor de HU-89 puede tapar el texto original.

Si se retoma, debe partir de un enfoque distinto al de la máscara por umbral y repetir el mismo criterio. Detalle: https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91
```

### #84 — ADR-003 (no procede cerrarlo)

**No se cierra:** el issue conserva la aprobación formal del PO, que sigue
pendiente. Comentario de estado para dejar en él:

```markdown
Estado al cierre del Sprint 3: el ADR está copiado en `docs/adr/ADR-003-edicion-de-imagen.md` y se implementó como línea técnica provisional.

- HU-85 a HU-90 entregadas; HU-91 descartada tras el *spike* (P4).
- Decisiones tomadas durante la implementación: P1 a P9.
- **Pendiente de decisión del PO:** aprobación de este ADR, P1-bis («Completado» exige páginas maquetadas), P3-bis (nombres del ZIP y carpeta `limpias/`) y P10 (cambiar el tipo de una región sin reprocesar).

Este issue se cerrará cuando el PO apruebe el ADR o pida cambios, que se anotarán en el propio ADR.
```

### #27 y #28 — HU-27 y HU-28 (segundo formato)

La definición de terminado de HU-90 pide actualizar HU-27 y HU-28 con el
nuevo formato. Los anexos del repositorio
([CP de HU-27](WIKI_SPRINT_3_CP_HU-27.md) y [CP de HU-28](WIKI_SPRINT_3_CP_HU-28.md))
ya lo recogen. Comentario para cada issue:

```markdown
**Actualización (HU-90):** la exportación tiene ahora un segundo formato, «Páginas traducidas (PNG en un ZIP)», además del DOCX, que no cambia. Ambos comparten la tarea en segundo plano, la instantánea inmutable, el historial y la descarga privada; el ZIP se llama `{álbum}_{idioma}_{fecha}_png.zip`. Casos del nuevo formato: CP-90.1 a CP-90.7.
```
