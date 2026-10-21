# Borrador para la wiki — Casos de prueba de HU-19

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12 a HU-18. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-19 — Aprobar traducción

**Historia de usuario:**  
Como traductor, quiero aprobar una traducción revisada para indicar que está lista como versión final.

**Decisiones del 2026-10-21 (ADR-002):**
- **T2:** no hay "Aprobar todas". En su lugar, "Aprobar" pasa directamente a la siguiente región sin aprobar, también con **Ctrl+Enter** desde el campo de la traducción, como el "Enter: aprobar y pasar al siguiente" del mockup.
- **"Aprobar" guarda también lo escrito en el campo**, para no perder una edición al aprobar directamente.
- **T1:** una traducción vacía ("se deja sin traducir") se puede aprobar. Las regiones sin texto que traducir no cuentan para aprobar la página (T5).

### Criterios de aceptación

**CA-19.1:** Cuando pulso "Aprobar" en la región 3, entonces la región 3 queda "Aprobada", con la fecha de aprobación, y el contador de regiones pendientes de la página disminuye en 1.

**CA-19.2:** Cuando apruebo la última región pendiente de la página, entonces la página pasa al estado "Aprobada".

**CA-19.3:** Dado que la región 4 no tiene traducción, entonces la acción "Aprobar" no está disponible en esa región y se explica el motivo.

**CA-19.4:** Dado que la región 3 está "Aprobada", cuando pulso "Retirar aprobación", entonces la región vuelve a "Editada" y la página deja de estar "Aprobada".

**CA-19.5:** Cuando cierro sesión y vuelvo a abrir la página, entonces las regiones aprobadas siguen "Aprobadas".

### CP-19.1 — Aprobar una región — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página traducida con dos regiones "Generadas". |
| **Pasos** | Pulsar "Aprobar" en la región 1, o Ctrl+Enter en su campo de traducción. |
| **Resultado esperado** | Aparece "Región 1 aprobada.". La región muestra "✓ Aprobada el <fecha>". El contador pasa a "1 traducción sin aprobar de 2" y la barra a "1/2 aprobadas". La vista salta a la región 2. Si se había editado el campo, se guarda lo escrito. |
| **CA relacionado** | CA-19.1 |
| **Prueba automática** | `albums/tests/test_translation_approval.py` › `ApproveRegionTests` |
| **Estado** | Aprobada |

### CP-19.2 — La página queda aprobada — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página traducida con una sola región sin aprobar. |
| **Pasos** | Aprobar la última región pendiente. |
| **Resultado esperado** | Aparece "Todas las traducciones están aprobadas: página aprobada.". La página pasa a "Aprobada" y la barra marca "N/N aprobadas". Una región vaciada a propósito no impide aprobar la página, y "se deja sin traducir" se puede aprobar. |
| **CA relacionado** | CA-19.2 |
| **Prueba automática** | `albums/tests/test_translation_approval.py` › `PageApprovalTests` |
| **Estado** | Aprobada |

### CP-19.3 — No se aprueba una región sin traducción — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | La región 2 nunca se tradujo ("Sin traducir"). |
| **Pasos** | Mirar la región 2 e intentar aprobarla. |
| **Resultado esperado** | "Aprobar" está deshabilitado, con el motivo "Para aprobarla necesita una traducción: tradúcela con IA o escríbela.". Un envío directo responde "La región 2 todavía no tiene traducción que aprobar.". Al escribir una traducción, "Aprobar" se habilita y aprueba. |
| **CA relacionado** | CA-19.3 |
| **Prueba automática** | `albums/tests/test_translation_approval.py` › `NoTranslationTests` |
| **Estado** | Aprobada |

### CP-19.4 — Retirar una aprobación — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página "Aprobada", con todas sus regiones aprobadas. |
| **Pasos** | Pulsar "Retirar aprobación" en la región 1. |
| **Resultado esperado** | Aparece "Se retiró la aprobación de la región 1.". La región vuelve a "Editada", sin fecha de aprobación, y la página deja de estar "Aprobada". |
| **CA relacionado** | CA-19.4 |
| **Prueba automática** | `albums/tests/test_translation_approval.py` › `WithdrawApprovalTests` |
| **Estado** | Aprobada |

### CP-19.5 — La aprobación se conserva — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Una región aprobada. |
| **Pasos** | Cerrar sesión, volver a entrar y abrir la página. |
| **Resultado esperado** | La región sigue "Aprobada", con su fecha. |
| **CA relacionado** | CA-19.5 |
| **Prueba automática** | `albums/tests/test_translation_approval.py` › `ApprovalPersistsTests` |
| **Estado** | Aprobada |

### Estrategia de pruebas automáticas

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Aprobar, retirar y estado de la página | Escenarios por vista con el servicio `albums/translation_review.py` | Comprueban estados, fechas, contadores y el paso a la siguiente región |
| Región sin traducción | Escenario de la interfaz (deshabilitado con motivo) y de la vista (el servidor también lo impide) | CA-19.3 no puede depender solo de JavaScript |
| Persistencia | Escenario con cierre y nuevo inicio de sesión | CA-19.5 |
| Aislamiento | Región ajena → 404; GET → 405 (`config/tests/test_route_access.py`) | Definición de terminado |

**Ejecución manual (21/10/2026)** sobre la página de comparación de *Naruto*, traducida con Gemini:
- **Ctrl+Enter** en la región 1 la aprobó con su fecha y saltó a la región 2 ("1/7 aprobadas").
- **Aprobar una a una las seis restantes:** al aprobar la última, la página pasó a "Aprobada", con "7/7 aprobadas" y "Todas las traducciones están aprobadas.".
