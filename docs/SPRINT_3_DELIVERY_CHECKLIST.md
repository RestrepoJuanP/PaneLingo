# Lista de verificación — Entrega final del Sprint 3

Fecha de corte: **9 de noviembre de 2026**

Rama de preparación: `docs/sprint-3-final-delivery`

Base verificada: `main` en `99113ef`

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
| Producto de software del Sprint 3 | Listo | HU-20, HU-22, HU-23, HU-24, HU-25, HU-27 y HU-28 fusionadas en `main` | Ejecutar la demostración final sobre la versión desplegada. |
| Backlog actualizado | En preparación | Historias y bugs gestionados en GitHub Projects; código fusionado en `main` | Confirmar en el tablero que todos los elementos cerrados tengan estado y responsable finales. |
| Actualización de documentos anteriores | En preparación | Wiki de Sprint 1 y Sprint 2; ADR-001 y ADR-002 | Corregir enlaces o cifras que cambien al completar despliegue y viabilidad. |
| Casos de prueba del Sprint 3 | Listo | Siete borradores de casos de prueba en `docs/WIKI_SPRINT_3_CP_HU-*.md` | Publicar o integrar los borradores en la página de Sprint 3 de la Wiki. |
| Pruebas automáticas | Listo | Suite de Django, CI y trazabilidad en `docs/WIKI_SPRINT_3_REPORTE_PRUEBAS.md` | Adjuntar la ejecución de CI del PR final. |
| Correcciones de cierre | Listo | BUG-063, BUG-071, BUG-072, BUG-073 y BUG-074 fusionados en `main` | Mostrar las regresiones cubiertas en el informe de pruebas. |
| Resultados de usabilidad | Requiere evidencia | Protocolo completo definido en la página Sprint 2 de la Wiki | Ejecutar cinco sesiones reales, tabular métricas, registrar hallazgos y crear bugs o HU de Sprint 4. |
| Manual de usuario | Pendiente | La aplicación y el README sirven como fuente técnica | Crear manual orientado al usuario, con capturas y recorridos de los flujos principales. |
| Despliegue público | Pendiente | Configuración local por variables de entorno | Preparar la aplicación para producción, elegir proveedor, desplegar y publicar la URL en Wiki y README. |
| Caso de negocio final | En preparación | Secciones 4 (finanzas) y 5 (riesgos) en la Wiki de Sprint 2 | Completar la sección 6: viabilidad técnica, operativa y conclusión costo-beneficio con cifras actualizadas. |
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
| **Total** | **Siete historias** | **30** | Todos los CP tienen cobertura automática. |

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
