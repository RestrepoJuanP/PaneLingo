# Sprint 3 — Producto final

> Borrador listo para integrar en la Wiki. Los campos que dependen de una
> actividad real permanecen señalados como pendientes para evitar presentar
> evidencia inexistente.

## 1. Objetivo del sprint

Cerrar el flujo principal de PaneLingo para que un traductor pueda organizar
un álbum, consultar el estado de sus páginas, conservar y retomar su trabajo,
eliminar proyectos que ya no necesita y exportar las traducciones aprobadas a
un archivo DOCX privado. La épica EP-08 Edición de imagen amplió el objetivo:
el traductor también puede limpiar el texto original, maquetar la traducción
sobre la página y descargar las páginas traducidas como PNG.

## 2. Incremento de producto

El Sprint 3 entrega trece historias funcionales: siete del flujo principal y
seis de la épica EP-08 Edición de imagen.

| Historia | Capacidad entregada | Casos de prueba |
|---|---|---|
| HU-20 | Eliminar un álbum propio mediante confirmación accesible y eliminación en cascada. | CP-20.1 a CP-20.5 |
| HU-22 | Consultar y filtrar el estado de cada página, con actualización automática. | CP-22.1 a CP-22.4 |
| HU-23 | Autoguardar correcciones y traducciones, reintentar fallos y evitar sobrescrituras concurrentes. | CP-23.1 a CP-23.5 |
| HU-24 | Continuar desde la última página y región trabajadas, incluso en una sesión nueva. | CP-24.1 a CP-24.4 |
| HU-25 | Ver el progreso del álbum medido por páginas aprobadas y su desglose por estado. | CP-25.1 a CP-25.4 |
| HU-27 | Preparar en segundo plano un DOCX con las traducciones aprobadas. | CP-27.1 a CP-27.4 |
| HU-28 | Descargar de forma privada una exportación terminada y consultar el historial. | CP-28.1 a CP-28.4 |
| HU-85 | Añadir a mano una región de texto que el OCR no detectó, con dibujo o con formulario de coordenadas. | CP-85.1 a CP-85.7 |
| HU-86 | Eliminar falsos positivos con deshacer y marcar regiones como «No traducir». | CP-86.1 a CP-86.6 |
| HU-87 | Ver la página con la traducción superpuesta, ajustada en el servidor con fuentes SIL OFL. | CP-87.1 a CP-87.7 |
| HU-88 | Limpiar el texto original en una capa aparte, conservando siempre la imagen original. | CP-88.1 a CP-88.8 |
| HU-89 | Maquetar cada traducción sobre la imagen limpia (caja, fuente, tamaño, alineación y color) y aprobar la página como «Maquetada». | CP-89.1 a CP-89.9 |
| HU-90 | Exportar las páginas traducidas como PNG en un ZIP, como segundo formato junto al DOCX. | CP-90.1 a CP-90.7 |

**Descartada:** HU-91 (limpiar con IA el texto que está sobre el dibujo,
prioridad *Could*). El *spike* previo no la justificó: Gemini no ofrece
edición de imagen en su nivel gratuito y el *inpainting* con OpenCV dejó
aceptables 0 de 3 regiones reales, frente a un criterio de 2 de 3. No se
añadió ninguna dependencia. Detalle en
[ADR-003, P4](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91).

Los casos detallados, sus precondiciones, resultados esperados y pruebas
automáticas se encuentran en los anexos del repositorio:

- [HU-20 — Eliminar álbum](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-20.md)
- [HU-22 — Consultar estado de una página](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-22.md)
- [HU-23 — Autoguardar el trabajo](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-23.md)
- [HU-24 — Continuar un trabajo guardado](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-24.md)
- [HU-25 — Consultar progreso del álbum](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-25.md)
- [HU-27 — Exportar resultados](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-27.md)
- [HU-28 — Descargar resultados](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-28.md)
- [HU-85 — Añadir una región de texto a mano](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-85.md)
- [HU-86 — Gestionar regiones detectadas](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-86.md)
- [HU-87 — Vista previa de la página traducida](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-87.md)
- [HU-88 — Limpiar el texto original](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-88.md)
- [HU-89 — Maquetar la traducción sobre la imagen](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-89.md)
- [HU-90 — Exportar las páginas traducidas como PNG](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-90.md)
- [HU-91 — Descartada tras el spike](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-91.md)

## 3. Decisiones funcionales de cierre

- El progreso del álbum se calcula por **páginas aprobadas**, de acuerdo con
  los ejemplos numéricos de HU-25.
- El autoguardado usa control optimista de versiones. Una pestaña con una
  versión antigua no puede sobrescribir un cambio más reciente.
- El botón **Continuar** se basa en la última actividad manual persistida; una
  propuesta automática no reemplaza el punto de trabajo del usuario.
- La exportación ofrece dos formatos: el DOCX de texto estructurado de HU-27
  y, desde HU-90, las páginas traducidas como PNG en un ZIP. La reinserción
  del texto en la imagen entró en el alcance con RF-15 y ADR-003.
- La página traducida se **compone por capas** (original, imagen limpia y
  textos maquetados) y no se genera con IA. Un único algoritmo de
  maquetación, en el servidor, alimenta la vista previa, el editor y la
  exportación (ADR-003).
- «Maquetada» es un estado aparte de la aprobación de la página. La regla de
  «Completado» del álbum no cambia; exigir páginas maquetadas queda como
  propuesta para el PO (ADR-003, P1-bis).
- Cada exportación representa una instantánea inmutable de las regiones
  aprobadas al momento de confirmarla.
- Las imágenes y exportaciones permanecen privadas; su acceso se realiza por
  vistas autenticadas y con aislamiento por propietario.

## 4. Correcciones realizadas antes del cierre

| Bug | Corrección | Regresión automática |
|---|---|---|
| BUG-063 | El mensaje de reprocesamiento coincide con la cantidad real de correcciones que serán reemplazadas. | `albums/tests/test_corrections.py` |
| BUG-071 | Las respuestas 404 y 500 usan una pantalla segura y coherente con la identidad visual. | `config/tests/test_error_pages.py` |
| BUG-072 | Las regiones aprobadas no inflan los contadores ni aparecen como pendientes de revisión. | `albums/tests/test_library_progress.py` |
| BUG-073 | Una página procesada sin regiones se considera completa y no queda bloqueada. | `albums/tests/test_processing.py` y `test_library_progress.py` |
| BUG-074 | La portada inválida se rechaza de la misma forma al crear y al editar un álbum. | `albums/tests/test_cover.py` |
| BUG-096 | Las páginas en gris de 16 bits se escalan a 8 bits también al clasificar sus regiones; antes, todas salían como globo. La primera parte de la corrección llegó con HU-90 (miniatura, limpieza, recorte del OCR manual y dibujo de la página). | `albums/tests/test_ocr_layout.py` |

Las regiones de páginas de 16 bits procesadas antes de BUG-096 siguen
clasificadas como globo hasta reprocesar la página, lo que borra su trabajo;
la propuesta de cambiar el tipo sin reprocesar está en ADR-003, P10.

## 5. Calidad y pruebas

Los 74 casos de prueba de las historias del Sprint 3 tienen al menos una
prueba automática asociada; la suite tiene 676 pruebas y una cobertura local
del 97 %. Cuatro casos de HU-89 (CP-89.2, CP-89.3, CP-89.6 y CP-89.8) tienen
además una parte interactiva que se verifica a mano y **todavía no se ha
ejecutado**. La suite también conserva las pruebas de los sprints anteriores
y las regresiones de los bugs de cierre.

La estrategia, la matriz HU → CA → CP → prueba y las instrucciones de
reproducción están en el [reporte de pruebas del Sprint 3](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_REPORTE_PRUEBAS.md).

El Quality Gate obligatorio ejecuta, en orden:

1. Ruff con correcciones seguras.
2. Black.
3. Ruff en modo de verificación.
4. Black en modo de verificación.
5. Comprobaciones de Django.
6. Suite automática de Django.
7. Auditoría de dependencias con `pip-audit`.

## 6. Entregables complementarios

| Entregable | Estado | Ubicación o siguiente acción |
|---|---|---|
| Backlog final | En preparación | Confirmar estados finales en GitHub Projects. |
| Casos y pruebas automáticas | Listo | Anexos de HU y reporte de pruebas. |
| Pruebas de usabilidad | Pendiente de ejecución real | Aplicar el protocolo definido en Sprint 2 a cinco participantes. |
| Manual de usuario | Pendiente | Crear con capturas de la versión desplegada. |
| Despliegue público | Pendiente | Preparar producción y publicar URL en esta página y en README. |
| Caso de negocio, sección 6 | Pendiente | Concluir viabilidad técnica, operativa y financiera. |
| Ceremonias | Pendiente de evidencia | Incorporar actas y enlaces reales del Sprint 3. |
| Presentación | Pendiente | Preparar demo para cliente y sustentación ante el profesor. |

El seguimiento detallado está en la
[lista de verificación de la entrega](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/SPRINT_3_DELIVERY_CHECKLIST.md).

## 7. Demostración funcional sugerida

1. Iniciar sesión y crear un álbum con idiomas de origen y destino.
2. Cargar una página y procesarla.
3. Corregir el texto detectado y observar el autoguardado.
4. Generar, editar y aprobar una traducción.
5. Volver a la biblioteca y verificar estado, progreso y botón **Continuar**.
6. Abrir **Revisión y exportación**, preparar el DOCX y descargarlo.
7. Abrir el archivo y comprobar título, idiomas, páginas y regiones.
8. En la página, pulsar **Limpiar página** y comparar las vistas
   «Original», «Limpia» y «Traducida».
9. Abrir la pestaña **Maquetación**, cambiar fuente, tamaño y caja de un
   texto y pulsar **Aprobar página**.
10. Exportar en «Páginas traducidas (PNG en un ZIP)», descargar el ZIP y
    comparar un PNG con el editor.
11. Mostrar el aislamiento de datos con una segunda cuenta.

## 8. Evidencias pendientes de completar por el equipo

- **URL pública:** pendiente.
- **Fecha y responsable del despliegue:** pendiente.
- **Participantes y resultados de usabilidad:** pendientes.
- **Hallazgos de usabilidad trasladados al backlog:** pendientes.
- **Enlaces a ceremonias del Sprint 3:** pendientes.
- **Enlace al manual de usuario:** pendiente.
- **Enlace a la presentación final:** pendiente.

Estos campos deben reemplazarse con enlaces verificables antes de presentar el
Sprint 3 como cerrado.
