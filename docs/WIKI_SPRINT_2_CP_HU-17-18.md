# Borrador para la wiki — Casos de prueba de HU-17 y HU-18

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12 a HU-16. HU-17 y HU-18 se implementan juntas en el espacio de trabajo (ADR-002, T3), pero cada una conserva sus criterios y sus casos de prueba.

### HU-17 — Revisar traducción generada

**Historia de usuario:**  
Como traductor, quiero revisar las traducciones generadas para comprobar que son precisas y coherentes.

### HU-18 — Editar traducción generada

**Historia de usuario:**  
Como traductor, quiero modificar una traducción generada por IA para mejorar su precisión y adaptarla al contexto.

**Decisiones del 2026-10-21 (ADR-002):**
- **T3:** HU-17 y HU-18 se fusionan en una sola pantalla, el espacio de trabajo del mockup, como recomienda la nota INVEST del issue.
- **T4:** se navega entre regiones con los botones "Anterior" y "Siguiente" y con **Alt+↑ / Alt+↓**. Las flechas solas ya pasan de página, y las teclas sueltas chocan con los lectores de pantalla.
- **T1 (CA-18.4):** una traducción vacía se acepta como "se deja sin traducir". Queda "Editada" y se podrá aprobar en HU-19.
- **Mientras la IA traduce la página no se guarda ninguna edición**, para que la tarea no la sobrescriba.

### Criterios de aceptación

**CA-17.1:** Cuando abro la revisión de la página, entonces veo, por cada región, su texto de origen y su traducción lado a lado, y la región se resalta sobre la imagen de la página.

**CA-17.2:** Cuando pulso "Siguiente" o uso el atajo de teclado correspondiente, entonces paso a la siguiente región en orden de lectura y el foco se mueve a esa región.

**CA-17.3:** Cada región muestra su estado ("Generada", "Editada" o "Aprobada"), veo cuántas regiones de la página faltan por aprobar y puedo mostrar solo las regiones sin aprobar.

**CA-17.4:** Cuando recorro las traducciones sin editarlas, entonces ningún texto ni estado cambia.

**CA-18.1:** Cuando modifico la traducción de la región 3 y la guardo, entonces la región conserva el texto editado como versión de trabajo, su estado pasa a "Editada" y la propuesta original de la IA se conserva y se puede consultar.

**CA-18.2:** Dado que la región 2 está "Aprobada", cuando modifico su traducción y guardo, entonces su estado vuelve a "Editada" y necesita aprobarse de nuevo.

**CA-18.3:** Cuando escribo una traducción con saltos de línea, signos ¿ ¡ y puntos suspensivos, entonces se guarda y se muestra exactamente como la escribí.

**CA-18.4:** Cuando borro todo el texto de una traducción y guardo, entonces se acepta como "se deja sin traducir" (decisión T1).

### CP-17.1 — Comparar el origen con la traducción — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página propia traducida (HU-16). |
| **Pasos** | Abrir el espacio de trabajo de la página y pulsar un bloque. |
| **Resultado esperado** | Cada bloque muestra "JA · texto de origen" y debajo "ES · traducción". Al pulsar el bloque se resalta su región en la imagen. |
| **CA relacionado** | CA-17.1 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `CompareTests` |
| **Estado** | Aprobada |

### CP-17.2 — Recorrer las traducciones — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página traducida con varias regiones. |
| **Pasos** | Pulsar "Siguiente" y "Anterior", y luego usar Alt+↓ y Alt+↑. |
| **Resultado esperado** | La selección pasa a la región siguiente o anterior en orden de lectura, se resalta en la imagen y el foco se mueve a su bloque. |
| **CA relacionado** | CA-17.2 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `StepThroughTests` (marcado y orden). El comportamiento con teclado se verificó a mano en el navegador (21/10/2026) |
| **Estado** | Aprobada |

### CP-17.3 — Identificar lo que falta por aprobar — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página traducida: una región editada y otra aprobada. |
| **Pasos** | Mirar los chips y el contador, y pulsar el filtro "Sin aprobar". |
| **Resultado esperado** | Los chips dicen "Editada" y "Aprobada". El contador dice "1 traducción sin aprobar de 2". El filtro deja solo la región sin aprobar y, con todo aprobado, se lee "Todas las traducciones están aprobadas." |
| **CA relacionado** | CA-17.3 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `PendingApprovalTests` |
| **Estado** | Aprobada |

### CP-17.4 — Revisar no cambia nada por sí solo — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página traducida. |
| **Pasos** | Abrir la página, recorrer las regiones y cambiar de filtro, sin editar. |
| **Resultado esperado** | Ningún texto ni estado de traducción cambia. |
| **CA relacionado** | CA-17.4 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `ReviewChangesNothingTests` |
| **Estado** | Aprobada |

### CP-18.1 — Editar y guardar una traducción — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Región con una propuesta de la IA ("Generada"). |
| **Pasos** | Cambiar la traducción y pulsar "Guardar traducción". |
| **Resultado esperado** | Aparece "Se guardó la traducción de la región N.". La región queda "Editada" con el texto nuevo, y "Ver propuesta de la IA" muestra la propuesta original. Una región sin traducir también admite una traducción escrita a mano. Si se sale sin guardar, el navegador avisa. |
| **CA relacionado** | CA-18.1 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `EditTranslationTests` |
| **Estado** | Aprobada |

### CP-18.2 — Editar una traducción ya aprobada — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Región "Aprobada"; página "Aprobada". |
| **Pasos** | Cambiar la traducción y guardar. |
| **Resultado esperado** | La región vuelve a "Editada" y pierde la fecha de aprobación. La página deja de estar "Aprobada". |
| **CA relacionado** | CA-18.2 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `EditApprovedTests` |
| **Estado** | Aprobada |

### CP-18.3 — Se respeta el formato del texto — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Región traducida. |
| **Pasos** | Escribir "¿Qué haces?", salto de línea, "¡Baja ya!…" y guardar. |
| **Resultado esperado** | Se guarda y se muestra exactamente igual, con el salto de línea, los signos de apertura y los puntos suspensivos. |
| **CA relacionado** | CA-18.3 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `FormattingTests` |
| **Estado** | Aprobada |

### CP-18.4 — Traducción vacía — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Región traducida. |
| **Pasos** | Borrar todo el texto (o dejar solo espacios) y guardar. |
| **Resultado esperado** | Aparece "La región N se deja sin traducir.". La región queda "Editada" con el campo vacío y la indicación "Se deja sin traducir." |
| **CA relacionado** | CA-18.4 |
| **Prueba automática** | `albums/tests/test_translation_review.py` › `EmptyTranslationTests` |
| **Estado** | Aprobada |

### Estrategia de pruebas automáticas

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Comparar, recorrer y filtrar | Integración de plantillas (`assertContains`) | Verifica el HTML que recibe el usuario: etiquetas, enlaces con la imagen, orden y filtro |
| Revisar sin cambiar nada | Escenario que compara la base de datos antes y después | CA-17.4 es justo que no haya efectos |
| Editar, formato y vacío | Escenarios por vista con el servicio `albums/translation_review.py` | Comprueban lo guardado y los estados |
| Aislamiento | Región ajena → 404; GET → 405 (`config/tests/test_route_access.py`) | Definición de terminado |

**Ejecución manual (21/10/2026)** sobre la página de *Naruto* con Gemini:
- **Alt+↓, Alt+↑ y los botones** mueven la selección y el foco entre regiones sin guardar nada.
- **Edición de la región 10:** se guardó "¡Idiota!" + salto de línea + "¡¿Qué haces ahí arriba?!…" tal cual, con el chip "Editada" y la propuesta de la IA ("¡Imbécil!") consultable.
