# Borrador para la wiki — Casos de prueba de HU-15

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-15 — Corregir texto detectado

**Historia de usuario:**  
Como traductor, quiero corregir el texto que detectó el OCR para solucionar los errores antes de traducir.

**Decisiones del 2026-10-20 (preguntas abiertas del DoR):**
- **CA-15.5:** una región que se deja vacía se acepta como "sin texto que traducir"; no se elimina.
- **Añadir, eliminar o fusionar regiones a mano** queda fuera de esta HU; si el PO lo aprueba, irá en una HU nueva.
- **Volver a procesar** una página reemplaza sus regiones y, con ellas, las correcciones (supuesto S2 del ADR-001); el modal de confirmación avisa de cuántas se perderán.

### Criterios de aceptación

**CA-15.1:** Dado que el usuario ve el texto detectado de una página propia, cuando edita el texto de la región 3 y lo guarda, entonces la región conserva el texto corregido, queda marcada como "revisada por el usuario" y el texto original del OCR se conserva para consultarlo.

**CA-15.2:** Dado que el usuario corrigió el texto de la región 3, cuando se genera la traducción de la página (HU-16), entonces se traduce el texto corregido y no el original del OCR.

**CA-15.3:** Dado que el usuario corrigió el texto de la región 3, cuando pulsa "Restaurar texto del OCR", entonces la región vuelve al texto detectado originalmente.

**CA-15.4:** Dado que el usuario editó una región y no la ha guardado, cuando intenta salir de la página, entonces se le avisa de que hay cambios sin guardar y no se pierden hasta que confirme que quiere salir.

**CA-15.5:** Dado que el usuario borra todo el texto de una región, cuando guarda, entonces la región se acepta como "sin texto que traducir".

### CP-15.1 — Corregir el texto de una región — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página propia procesada; la región 1 necesita revisión. |
| **Pasos** | Abrir "Corregir texto" en la región 1, cambiar el texto y pulsar "Guardar corrección". |
| **Resultado esperado** | La región muestra el texto corregido y la etiqueta "Corregida", deja de pedir revisión y debajo se ve "Texto del OCR: …". Si ninguna otra región la necesita, la página pasa de "Necesita revisión" a "Procesada". Las demás regiones no cambian. |
| **CA relacionado** | CA-15.1 |
| **Prueba automática** | `albums/tests/test_corrections.py` › `CorrectRegionTests` |
| **Estado** | Aprobada |

### CP-15.2 — La traducción usa el texto corregido — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Una región corregida y otra sin corregir. |
| **Pasos** | Consultar el texto que vale para traducir de cada región (`TextRegion.final_text`, el que usará HU-16). |
| **Resultado esperado** | La corregida devuelve el texto corregido; la otra, el del OCR. |
| **CA relacionado** | CA-15.2 |
| **Prueba automática** | `test_corrections.py` › `TranslationTextTests` |
| **Estado** | Aprobada (se verificará de punta a punta cuando exista HU-16) |

### CP-15.3 — Deshacer una corrección — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Región corregida cuyo texto del OCR era dudoso. |
| **Pasos** | Pulsar "Restaurar texto del OCR". |
| **Resultado esperado** | La región vuelve al texto detectado, pierde la etiqueta "Corregida" y, como el texto del OCR era dudoso, vuelve a pedir revisión. |
| **CA relacionado** | CA-15.3 |
| **Prueba automática** | `test_corrections.py` › `RestoreTests` |
| **Estado** | Aprobada |

### CP-15.4 — Salir con cambios sin guardar — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página procesada con texto detectado. |
| **Pasos** | Editar el texto de una región sin guardarlo e intentar salir: pulsar "Volver al álbum", usar las flechas de navegación o recargar. |
| **Resultado esperado** | El navegador avisa de que hay cambios sin guardar y no sale hasta que se confirma. Sin cambios, no avisa. Al guardar una región no se avisa por ella. |
| **CA relacionado** | CA-15.4 |
| **Prueba automática** | `test_corrections.py` › `UnsavedChangesTests` (marcas del formulario); el aviso del navegador se comprobó a mano |
| **Estado** | Aprobada |

### CP-15.5 — Dejar vacía una región — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Región con texto detectado. |
| **Pasos** | Borrar todo su texto y pulsar "Guardar corrección". |
| **Resultado esperado** | La región no se elimina: se muestra "Sin texto que traducir", queda corregida y no pide revisión. |
| **CA relacionado** | CA-15.5 |
| **Prueba automática** | `test_corrections.py` › `EmptyRegionTests` |
| **Estado** | Aprobada |

Además, `CorrectionAccessTests` comprueba que una región de otra cuenta responde 404 y que un GET responde 405.
