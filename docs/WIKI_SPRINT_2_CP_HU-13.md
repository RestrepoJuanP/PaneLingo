# Borrador para la wiki — Casos de prueba de HU-13

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-13 — Extraer texto mediante OCR

**Historia de usuario:**  
Como traductor, quiero que el sistema extraiga con OCR el texto de las regiones detectadas para no tener que transcribirlo a mano.

Decisiones técnicas: ADR-001, supuestos S6 (idioma de origen) y S7 (umbral de confianza).

### Criterios de aceptación

**CA-13.1:** Dado que una página propia tiene regiones de texto detectadas, cuando termina el OCR, entonces cada región tiene su texto de origen y un nivel de confianza del 0 al 100 %, y el texto queda guardado aunque el usuario cierre sesión.

**CA-13.2:** Dado que el álbum tiene "Japonés" como idioma de origen, cuando se ejecuta el OCR, entonces el reconocimiento se hace en japonés. *Se verifica comprobando que el texto esté en el alfabeto del idioma de origen; si no lo está, la región se marca para revisión (S6).*

**CA-13.3:** Dado que la confianza de una región queda por debajo del umbral acordado (70 % provisional), cuando termina el OCR, entonces la región se marca para revisión y la página pasa a "Necesita revisión".

**CA-13.4:** Dado el juego de páginas de prueba de un idioma, cuando se procesan con OCR, entonces al menos el umbral acordado de regiones conserva el texto y el orden de sus caracteres.

**CA-13.5:** Dado que el OCR falla en una o varias regiones, cuando termina, entonces esas regiones quedan sin texto y marcadas para revisión, y el resto de la página conserva su resultado.

### CP-13.1 — Texto y confianza por región — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Página propia en un álbum japonés, con texto legible. |
| **Pasos** | Procesar la página, cerrar sesión, volver a entrar y abrirla. |
| **Resultado esperado** | Cada región muestra su texto en japonés y su confianza ("Confianza 97 %"). El texto sigue ahí después de volver a iniciar sesión. |
| **CA relacionado** | CA-13.1 |
| **Prueba automática** | `albums/tests/test_processing.py` › `OcrTextTests`; `test_ocr_providers.py` › `AzureReadSuccessTests` |
| **Estado** | Aprobada |

### CP-13.2 — Texto en otro alfabeto — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Álbum con japonés como idioma de origen. |
| **Pasos** | Procesar una página cuyo texto reconocido esté solo en letras latinas. |
| **Resultado esperado** | La región se marca "Revisar" y la página pasa a "Necesita revisión". Un texto japonés con alguna palabra en inglés, o sin letras ("!?", "…"), no se marca. |
| **CA relacionado** | CA-13.2 |
| **Prueba automática** | `test_ocr_review.py` › `SourceScriptTests`; `test_processing.py` › `OcrTextTests` |
| **Estado** | Aprobada |

### CP-13.3 — Región con baja confianza — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Página con una región que el OCR lee con una confianza inferior al 70 %. |
| **Pasos** | Procesar la página y abrirla. |
| **Resultado esperado** | Esa región muestra "Revisar", el panel indica "1 necesita revisión." y la página queda en "Necesita revisión". Con todas las regiones por encima del umbral, queda "Procesada". |
| **CA relacionado** | CA-13.3 |
| **Prueba automática** | `test_ocr_review.py` › `NeedsReviewTests`; `test_processing.py` › `OcrTextTests` |
| **Estado** | Aprobada |

### CP-13.4 — Precisión mínima por idioma — Esquema con ejemplos

| Campo | Descripción |
|---|---|
| **Precondición** | Juego de páginas de prueba por idioma, con el texto esperado de cada región. |
| **Pasos** | `python manage.py ocr_accuracy_report <carpeta> --output informe-ocr.md` con `OCR_PROVIDER=azure`. |
| **Resultado esperado** | El informe muestra, por idioma, el porcentaje de regiones con su texto exacto y en su orden, y si alcanza el umbral acordado. |
| **CA relacionado** | CA-13.4 |
| **Prueba automática** | `test_ocr_accuracy_report.py` › `AccuracyReportTests` (el cálculo del informe) |
| **Estado** | **Pendiente**: faltan el juego de páginas de prueba y los umbrales del PO |

| idioma | umbral |
|---|---|
| Japonés | por definir |
| Coreano | por definir |
| Chino simplificado | por definir |
| Inglés | por definir |

### CP-13.5 — Falla el OCR en una región — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | El OCR no devuelve texto para una de las regiones de la página. |
| **Pasos** | Procesar la página y abrirla. |
| **Resultado esperado** | Esa región aparece como "Sin texto reconocido" y marcada "Revisar"; las demás conservan su texto. |
| **CA relacionado** | CA-13.5 |
| **Prueba automática** | `test_processing.py` › `OcrTextTests`; `test_ocr_review.py` › `NeedsReviewTests` |
| **Estado** | Aprobada |
