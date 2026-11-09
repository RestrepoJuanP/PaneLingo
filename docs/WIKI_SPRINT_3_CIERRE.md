# Sprint 3 — Producto final

> Borrador listo para integrar en la Wiki. Los campos que dependen de una
> actividad real permanecen señalados como pendientes para evitar presentar
> evidencia inexistente.

## 1. Objetivo del sprint

Cerrar el flujo principal de PaneLingo para que un traductor pueda organizar
un álbum, consultar el estado de sus páginas, conservar y retomar su trabajo,
eliminar proyectos que ya no necesita y exportar las traducciones aprobadas a
un archivo DOCX privado.

## 2. Incremento de producto

El Sprint 3 entrega siete historias funcionales:

| Historia | Capacidad entregada | Casos de prueba |
|---|---|---|
| HU-20 | Eliminar un álbum propio mediante confirmación accesible y eliminación en cascada. | CP-20.1 a CP-20.5 |
| HU-22 | Consultar y filtrar el estado de cada página, con actualización automática. | CP-22.1 a CP-22.4 |
| HU-23 | Autoguardar correcciones y traducciones, reintentar fallos y evitar sobrescrituras concurrentes. | CP-23.1 a CP-23.5 |
| HU-24 | Continuar desde la última página y región trabajadas, incluso en una sesión nueva. | CP-24.1 a CP-24.4 |
| HU-25 | Ver el progreso del álbum medido por páginas aprobadas y su desglose por estado. | CP-25.1 a CP-25.4 |
| HU-27 | Preparar en segundo plano un DOCX con las traducciones aprobadas. | CP-27.1 a CP-27.4 |
| HU-28 | Descargar de forma privada una exportación terminada y consultar el historial. | CP-28.1 a CP-28.4 |

Los casos detallados, sus precondiciones, resultados esperados y pruebas
automáticas se encuentran en los anexos del repositorio:

- [HU-20 — Eliminar álbum](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-20.md)
- [HU-22 — Consultar estado de una página](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-22.md)
- [HU-23 — Autoguardar el trabajo](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-23.md)
- [HU-24 — Continuar un trabajo guardado](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-24.md)
- [HU-25 — Consultar progreso del álbum](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-25.md)
- [HU-27 — Exportar resultados](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-27.md)
- [HU-28 — Descargar resultados](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/WIKI_SPRINT_3_CP_HU-28.md)

## 3. Decisiones funcionales de cierre

- El progreso del álbum se calcula por **páginas aprobadas**, de acuerdo con
  los ejemplos numéricos de HU-25.
- El autoguardado usa control optimista de versiones. Una pestaña con una
  versión antigua no puede sobrescribir un cambio más reciente.
- El botón **Continuar** se basa en la última actividad manual persistida; una
  propuesta automática no reemplaza el punto de trabajo del usuario.
- La exportación es un DOCX de texto estructurado. La recomposición de las
  imágenes con texto traducido no forma parte del alcance actual.
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

## 5. Calidad y pruebas

Los 30 casos de prueba de las historias del Sprint 3 tienen al menos una
prueba automática asociada. La suite también conserva las pruebas de los
sprints anteriores y las regresiones de los bugs de cierre.

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
8. Mostrar el aislamiento de datos con una segunda cuenta.

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
