# Borrador para la wiki — Casos de prueba de HU-14

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-14 — Visualizar texto detectado

**Historia de usuario:**  
Como traductor, quiero ver el texto que detectó el OCR junto a la página para comprobar que se reconoció correctamente.

**Decisión del 2026-10-20 (pregunta abierta del DoR):** el orden de lectura no se corrige a mano en esta HU; si hace falta, irá en una HU nueva.

### Criterios de aceptación

**CA-14.1:** Dado que una página propia ya está procesada, cuando el usuario la abre, entonces ve en un panel la imagen con sus regiones numeradas y en el otro el texto de cada región en orden de lectura, con su tipo y su nivel de confianza.

**CA-14.2:** Dado que la página tiene regiones, cuando el usuario selecciona una región en la imagen, entonces se resalta su texto en la lista, y al revés.

**CA-14.3:** Dado que hay regiones marcadas para revisión, cuando el usuario abre la página, entonces esas regiones se distinguen visualmente y con texto, no solo con color, y puede mostrar solo las pendientes de revisar.

**CA-14.4:** Dado que la página está en "Pendiente de procesamiento", cuando el usuario la abre, entonces ve "Esta página aún no se ha procesado" y el botón "Procesar página".

**CA-14.5:** Dado que el usuario recorre las regiones con el teclado, cuando avanza por ellas, entonces el foco es visible en todo momento y el lector de pantalla anuncia el número, el tipo y el texto de cada región.

### CP-14.1 — Vista dividida de imagen y texto — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página propia procesada con dos regiones. |
| **Pasos** | Abrir la página. |
| **Resultado esperado** | A un lado, la imagen con las regiones numeradas; al otro, "Texto detectado" con el texto de cada región en orden de lectura, su tipo y su confianza. |
| **CA relacionado** | CA-14.1 |
| **Prueba automática** | `albums/tests/test_detected_text_view.py` › `SplitViewTests` |
| **Estado** | Aprobada |

### CP-14.2 — Relacionar la región con su texto — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página procesada con varias regiones. |
| **Pasos** | Pulsar la región 2 en la imagen; después pulsar el texto de la región 1 en la lista. |
| **Resultado esperado** | Al pulsar la región 2 se resaltan a la vez su caja y su texto, y la lista se desplaza hasta él. Al pulsar el texto 1 se resaltan su texto y su caja. |
| **CA relacionado** | CA-14.2 |
| **Prueba automática** | `test_detected_text_view.py` › `LinkedSelectionTests` |
| **Estado** | Aprobada |

### CP-14.3 — Destacar lo que conviene revisar — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página con una región de baja confianza y otra fiable. |
| **Pasos** | Abrir la página y elegir el filtro "Por revisar". |
| **Resultado esperado** | La región dudosa tiene borde discontinuo y "!" junto a su número en la imagen, y "Revisar" en la lista. Con el filtro solo se ve esa región. Si ninguna necesita revisión, el filtro no aparece. |
| **CA relacionado** | CA-14.3 |
| **Prueba automática** | `test_detected_text_view.py` › `ReviewHighlightTests` |
| **Estado** | Aprobada |

### CP-14.4 — La página aún no se ha procesado — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página en "Pendiente de procesamiento". |
| **Pasos** | Abrir la página. |
| **Resultado esperado** | Se ve "Esta página aún no se ha procesado." y el botón "Procesar página". |
| **CA relacionado** | CA-14.4 |
| **Prueba automática** | `test_detected_text_view.py` › `UnprocessedPageTests` |
| **Estado** | Aprobada |

### CP-14.5 — Uso completo con teclado — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página procesada; lector de pantalla activo. |
| **Pasos** | Recorrer la página con Tab y Mayús+Tab. |
| **Resultado esperado** | Cada caja y cada texto reciben el foco, con el contorno visible. El lector anuncia, por ejemplo, "Región 1: globo de diálogo, necesita revisión. Texto: たぶん". |
| **CA relacionado** | CA-14.5 |
| **Prueba automática** | `test_detected_text_view.py` › `KeyboardAndScreenReaderTests` |
| **Estado** | Aprobada |
