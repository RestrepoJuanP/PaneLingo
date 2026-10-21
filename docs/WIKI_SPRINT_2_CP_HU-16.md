# Borrador para la wiki — Casos de prueba de HU-16

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12 a HU-15. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-16 — Generar traducción asistida por IA

**Historia de usuario:**  
Como traductor, quiero generar con IA una traducción que tenga en cuenta el contexto de la página completa para partir de una propuesta inicial.

**Decisiones del 2026-10-21 (ADR-002):**
- **Proveedor:** Google Gemini (nivel gratuito de AI Studio), detrás de un adaptador. Las pruebas usan un proveedor simulado.
- **⚠️ Riesgo de privacidad:** en el nivel gratuito, Google puede usar el texto enviado para mejorar sus productos. Se acepta solo para el MVP y con material de prueba; lo debe aceptar el PO.
- **"Reintentar con IA" por región** (el "Retry AI" del mockup): envía la página entera como contexto, pero solo cambia esa región.
- **Volver a procesar** una página borra sus traducciones, y el aviso dice cuántas se perderán (T6).

### Criterios de aceptación

**CA-16.1:** Dado que tengo una página propia con el texto de origen revisado, cuando pulso "Traducir página", entonces cada región recibe una propuesta de traducción, que queda "Generada" y asociada a su región, y puedo seguir usando PaneLingo mientras se genera.

**CA-16.2:** Cuando se solicita la traducción, entonces el servicio recibe todas las regiones de la página en orden de lectura, con su tipo, y los idiomas de origen y destino del álbum.

**CA-16.3:** Dado que la región 2 tiene una traducción "Aprobada", cuando vuelvo a pulsar "Traducir página", entonces la región 2 conserva su traducción aprobada y solo se regeneran las regiones sin aprobar.

**CA-16.4:** Cuando el servicio devuelve un error o se agota el tiempo de espera, entonces veo un mensaje de error con la opción "Reintentar" y las traducciones que ya existían no se pierden.

**CA-16.5:** Dado que la página no tiene regiones con texto, entonces el botón "Traducir página" no está disponible y se explica el motivo.

**CA-16.6:** Cuando pulso "Traducir página", entonces no se me pide elegir un tipo o estilo de traducción y la IA traduce a partir del contexto de la página.

### CP-16.1 — Traducir una página — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página propia procesada, con dos regiones de texto y ninguna traducida. |
| **Pasos** | Pulsar "Traducir página" en el espacio de trabajo. |
| **Resultado esperado** | Aparece "Traduciendo la página 1. Puedes seguir usando PaneLingo mientras tanto." y la vista se actualiza sola al terminar. Cada región muestra "ES · traducción" con su propuesta y el estado "Generada". "Reintentar con IA" en una sola región cambia solo esa región. |
| **CA relacionado** | CA-16.1 |
| **Prueba automática** | `albums/tests/test_translation.py` › `TranslatePageTests`, `RetryRegionTests` |
| **Estado** | Aprobada |

### CP-16.2 — Se envía el contexto de la página — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página japonesa procesada; la región 1 tiene una corrección de HU-15. |
| **Pasos** | Pulsar "Traducir página" y revisar la petición que recibe el proveedor. |
| **Resultado esperado** | Viajan todas las regiones con texto en orden de lectura, con su tipo ("Globo de diálogo" o "Cuadro narrativo") y los idiomas "Japonés" y "Español". La región 1 viaja con el texto corregido. Una región vaciada a propósito no viaja. |
| **CA relacionado** | CA-16.2 |
| **Prueba automática** | `albums/tests/test_translation.py` › `PageContextTests`; `albums/tests/test_translation_providers.py` › `GeminiRequestTests` |
| **Estado** | Aprobada |

### CP-16.3 — No se pisan las traducciones aprobadas — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página traducida con la región 2 "Aprobada". |
| **Pasos** | Pulsar "Traducir de nuevo". |
| **Resultado esperado** | La región 2 conserva su traducción y su estado "Aprobada". Viaja como contexto, pero no se pide su traducción. "Reintentar con IA" no aparece en una región aprobada. |
| **CA relacionado** | CA-16.3 |
| **Prueba automática** | `albums/tests/test_translation.py` › `ApprovedTranslationTests` |
| **Estado** | Aprobada |

### CP-16.4 — Falla el servicio de IA — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página traducida; el servicio de IA no responde, rechaza la clave, agota la cuota o devuelve una respuesta ilegible. |
| **Pasos** | Pulsar "Traducir de nuevo". |
| **Resultado esperado** | Se ve el motivo (por ejemplo, "El servicio de traducción no está disponible.") con "Se conservan las traducciones anteriores" y el botón "Reintentar". Las traducciones anteriores siguen igual. Una traducción colgada más de 5 minutos también pasa a error. |
| **CA relacionado** | CA-16.4 |
| **Prueba automática** | `albums/tests/test_translation.py` › `TranslationFailureTests`; `albums/tests/test_translation_providers.py` › `GeminiResponseTests` |
| **Estado** | Aprobada |

### CP-16.5 — Página sin texto de origen — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página procesada sin texto, o con todas sus regiones marcadas "sin texto que traducir". |
| **Pasos** | Abrir la página. |
| **Resultado esperado** | "Traducir página" aparece deshabilitado, con el motivo: "Esta página no tiene texto que traducir" o "No hay texto pendiente de traducir". Un envío directo no encola nada. |
| **CA relacionado** | CA-16.5 |
| **Prueba automática** | `albums/tests/test_translation.py` › `NothingToTranslateTests` |
| **Estado** | Aprobada |

### CP-16.6 — Sin selector de estilo de traducción — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página procesada con texto. |
| **Pasos** | Pulsar "Traducir página". |
| **Resultado esperado** | La traducción empieza sin pedir ningún tipo o estilo: no hay selector en la pantalla y la página se traduce. |
| **CA relacionado** | CA-16.6 |
| **Prueba automática** | `albums/tests/test_translation.py` › `NoStyleSelectorTests` |
| **Estado** | Aprobada |

### Estrategia de pruebas automáticas de HU-16

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Contexto de la página | Escenarios con el proveedor simulado, que guarda la última petición | Se comprueba exactamente lo que viaja: orden, tipo, idiomas, texto corregido y regiones excluidas |
| Adaptador de Gemini | Integración con la red simulada (`unittest.mock`) | Contrato con la API (clave en cabecera, esquema JSON) y cada error HTTP, sin gastar cuota |
| Traducir, reintentar y fallar | Escenarios por CP, con Huey inmediato | Un caso de prueba por criterio de aceptación |
| Aislamiento | Página o región ajena → 404; GET → 405 (`config/tests/test_route_access.py`) | Definición de terminado |

**Ejecución manual con Gemini real (21/10/2026):** sobre la página de *Naruto* del reporte de pruebas.
- **"Traducir página":** tradujo las 9 regiones con texto en unos 15 s, con el contexto de la página. Por ejemplo, 「イルカ先生だ」 → "Es el Iruka-sensei", y la vista se actualizó sola.
- **"Reintentar con IA" en la región 1:** cambió solo esa región.
- **Ajuste encontrado:** la IA copiaba los saltos de línea de las columnas del OCR y partía palabras ("¡Idio / ta!!"). Se ajustó la instrucción para que escriba texto corrido.
