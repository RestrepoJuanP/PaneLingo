# Lista de verificación — Entrega final del Sprint 3

Fecha de corte: **9 de noviembre de 2026**

Rama de preparación: `docs/sprint-3-final-delivery`

Base verificada: `main` en `99113ef`

Actualización del 13 de noviembre de 2026: producto desplegado en AWS, manual de usuario en PDF, Sección 6 del caso de negocio y página Sprint 3 de la Wiki listos; correcciones U1 a U5 de la evaluación heurística y la review (690 pruebas).

Actualización del 10 de noviembre de 2026: se añade la épica EP-08 Edición de
imagen y BUG-096, verificados en la rama `docs/ep08-closure` (apilada sobre
`main` en `8eb3323`). Los estados de los entregables que dependen del equipo
no cambian.

## Propósito

Esta lista convierte los entregables del documento maestro del Sprint 3 en
acciones verificables. El estado **Listo** solo se usa cuando existe evidencia
en el repositorio o en la Wiki; no se da por realizada ninguna actividad que
dependa de participantes, reuniones o servicios externos.

## Convención de estados

| Estado | Significado |
|---|---|
| Listo | El entregable existe y tiene evidencia verificable. |
| En preparación | Hay una base reutilizable, pero falta consolidarla o publicarla. |
| Requiere evidencia | La actividad debe ocurrir con personas o servicios reales. |
| Pendiente | Todavía no se ha iniciado. |

## Entregables obligatorios

| Entregable | Estado al corte | Evidencia disponible | Acción para cerrar |
|---|---|---|---|
| Producto de software del Sprint 3 | Listo | HU-20, HU-22 a HU-25, HU-27, HU-28 y HU-85 a HU-88 fusionadas en `main`; HU-89, HU-90 y BUG-096 terminadas con Quality Gate 7/7, en PR pendientes de fusión; HU-91 descartada tras el spike (ADR-003, P4) | Fusionar los PR de EP-08 en orden y ejecutar la demostración final sobre la versión desplegada. |
| Backlog actualizado | En preparación | Historias y bugs gestionados en GitHub Projects; código fusionado en `main` | Confirmar en el tablero que todos los elementos cerrados tengan estado y responsable finales. |
| Actualización de documentos anteriores | En preparación | Wiki de Sprint 1 y Sprint 2; ADR-001, ADR-002 y ADR-003; textos para la Wiki en `docs/WIKI_EP08_ACTUALIZACIONES.md` | Pegar en la Wiki RF-15, el cambio de alcance del Sprint 0, la entrada de EP-08 y la actualización de HU-27 y HU-28; corregir enlaces o cifras que cambien al completar despliegue y viabilidad. |
| Casos de prueba del Sprint 3 | Listo | Trece borradores de casos de prueba y la nota de HU-91 en `docs/WIKI_SPRINT_3_CP_HU-*.md` | Publicar o integrar los borradores en la página de Sprint 3 de la Wiki. Las partes manuales de CP-89.2, CP-89.3, CP-89.6 y CP-89.8 se ejecutaron el 11/11/2026. |
| Pruebas automáticas | Listo | 678 pruebas, cobertura local del 97 %, CI y trazabilidad en `docs/WIKI_SPRINT_3_REPORTE_PRUEBAS.md` | Adjuntar la ejecución de CI del PR final. |
| Correcciones de cierre | Listo | BUG-063, BUG-071, BUG-072, BUG-073 y BUG-074 fusionados en `main`; BUG-096 corregido en `fix/BUG-096-16bit-grayscale`, pendiente de fusión | Fusionar BUG-096 y mostrar las regresiones cubiertas en el informe de pruebas. |
| Resultados de usabilidad | Requiere evidencia | Protocolo completo definido en la página Sprint 2 de la Wiki | Ejecutar cinco sesiones reales, tabular métricas, registrar hallazgos y crear bugs o HU de Sprint 4. |
| Manual de usuario | Listo | [`docs/manual/PaneLingo-Manual-de-usuario.pdf`](manual/PaneLingo-Manual-de-usuario.pdf) (18 páginas, capturas de la versión desplegada) y página «Manual de usuario» de la Wiki | Entregarlo al cliente. |
| Despliegue público | Listo | https://13-185-1-92.sslip.io en AWS EC2 con Docker y HTTPS; procedimiento en la página «Despliegue en AWS» de la Wiki | Mantener la instancia encendida hasta la sustentación. |
| Caso de negocio final | Listo | Sección 6 en la página Sprint 3 de la Wiki: viabilidad técnica y operativa, costo-beneficio, costos a escala, sensibilidad, riesgos de privacidad y conclusión | — |
| Evidencias de ceremonias | Requiere evidencia | Registros de Sprint 1 y enlaces de Sprint 2 | Incorporar actas, fechas, participantes, acuerdos y enlaces reales del Sprint 3. |
| Presentación al cliente | Pendiente | Producto y trazabilidad funcional disponibles | Preparar demostración breve enfocada en valor, cambios y retroalimentación. |
| Sustentación ante el profesor | Pendiente | Código, pruebas y documentación disponibles | Preparar presentación con demo, arquitectura, calidad, usabilidad, negocio, manual y despliegue. |

## Cierre funcional verificable

| Historia | Resultado entregado | CP documentados | Prueba principal |
|---|---|---:|---|
| HU-20 | Eliminación segura de álbumes | 5 | `albums/tests/test_album_delete.py` |
| HU-22 | Estado y filtrado de páginas | 4 | `albums/tests/test_library_progress.py` |
| HU-23 | Autoguardado y conflictos entre sesiones | 5 | `albums/tests/test_autosave.py` |
| HU-24 | Continuación desde el último punto | 4 | `albums/tests/test_resume_work.py` |
| HU-25 | Progreso por páginas aprobadas | 4 | `albums/tests/test_library_progress.py` |
| HU-27 | Exportación asíncrona a DOCX | 4 | `albums/tests/test_export.py` |
| HU-28 | Descarga privada e historial de exportaciones | 4 | `albums/tests/test_export_download.py` |
| HU-85 | Regiones de texto añadidas a mano | 7 | `albums/tests/test_manual_regions.py` |
| HU-86 | Eliminar regiones y marcar «No traducir» | 6 | `albums/tests/test_region_management.py` |
| HU-87 | Vista previa de la página traducida | 7 | `albums/tests/test_translated_preview.py` |
| HU-88 | Limpieza del texto original en una capa aparte | 8 | `albums/tests/test_cleaning.py` |
| HU-89 | Editor de maquetación y estado «Maquetada» | 9 | `albums/tests/test_typesetting_editor.py` |
| HU-90 | Exportación de páginas traducidas en PNG dentro de un ZIP | 7 | `albums/tests/test_png_export.py` |
| HU-91 | Descartada tras el spike (ADR-003, P4) | 0 | — |
| **Total** | **Trece historias entregadas y una descartada** | **74** | Todos los CP tienen cobertura automática; cuatro de HU-89 tienen además una parte manual, ejecutada el 11/11/2026. |

## Evidencia que debe aportar el equipo

Estos puntos no se pueden sustituir por texto generado ni por pruebas
automáticas:

- Identidad o código anonimizado de los cinco participantes de usabilidad.
- Consentimiento y fecha de cada sesión; no se versionan datos personales ni
  grabaciones sin autorización.
- Hoja de resultados con éxito, tiempo, errores, ayudas y SEQ por tarea.
- Respuestas SUS y comentarios cualitativos reales.
- Actas o enlaces reales de planeación, coordinación, review y retrospectiva.
- Cuenta y autorización para crear el servicio de despliegue público.
- URL pública comprobada y fecha de la última verificación.

## Orden de cierre recomendado

1. Completar la preparación para despliegue y publicar una versión estable.
2. Construir el manual con capturas de esa misma versión.
3. Ejecutar el protocolo de usabilidad de Sprint 2 sobre la versión publicada.
4. Corregir hallazgos pequeños y registrar como bugs o HU los cambios grandes.
5. Completar la viabilidad con los costos reales del despliegue elegido.
6. Reunir las evidencias de ceremonias y actualizar el backlog.
7. Preparar la presentación y hacer un ensayo de la demostración.
8. Ejecutar el Quality Gate y verificar todos los enlaces de Wiki y README.

## Criterio de entrega

La entrega final puede marcarse como completa cuando todos los renglones de la
tabla de entregables estén en **Listo**, la URL pública responda, el Quality
Gate y la CI estén en verde y la Wiki permita llegar a cada evidencia sin
solicitar archivos adicionales.
