# Borrador para la wiki — Casos de prueba de HU-12

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki. Sigue la convención del Sprint 1: un CP por criterio de aceptación, con su tipo de flujo. Cada CP tiene al menos una prueba automática que lo cita en el docstring.

## HU-12 — Detectar regiones de texto

> **Como** traductor, **quiero** que el sistema detecte automáticamente las regiones con texto de una página **para** no tener que marcarlas a mano.

Decisiones técnicas: [ADR-001 — Proveedor de detección y OCR, y ejecución asíncrona](docs/adr/ADR-001-proveedor-ocr-y-tareas-asincronas.md).

### CP-12.1 — Procesar una página — Happy Path

| Campo | Valor |
|---|---|
| Criterio | CA-12.1 |
| Precondición | Sesión iniciada; página propia en "Pendiente de procesamiento" |
| Pasos | 1. Abrir la página desde la rejilla del álbum. 2. Pulsar "Procesar página". 3. Navegar a otra pantalla mientras se procesa. 4. Volver a la página cuando termine |
| Resultado esperado | La página pasa a "Procesando" y la aplicación sigue respondiendo. Al terminar pasa a "Procesada", la vista se actualiza sola, sin pulsar nada, y cada región queda guardada con su posición y su tipo (globo de diálogo o cuadro narrativo) |
| Pruebas automáticas | `albums/tests/test_processing.py` › `ProcessPageTests`, `LiveRefreshTests`; `test_ocr_layout.py` › `MergeLinesTests`, `RegionKindTests`; `test_ocr_providers.py` › `AzureReadSuccessTests`, `ProviderSelectionTests`, `FakeProviderTests` |

### CP-12.2 — Ver las regiones en orden de lectura — Happy Path

| Campo | Valor |
|---|---|
| Criterio | CA-12.2 |
| Precondición | Página propia "Procesada", en un álbum con japonés como idioma de origen, con dos globos en la misma fila |
| Pasos | 1. Abrir la página. 2. Recorrer las regiones con el tabulador |
| Resultado esperado | Cada región aparece resaltada sobre la imagen y numerada; la de la derecha es la n.º 1. Con el teclado, cada región enlaza con su elemento de la lista y el lector de pantalla anuncia número y tipo. En un álbum coreano, la de la izquierda es la n.º 1 |
| Pruebas automáticas | `test_processing.py` › `RegionDisplayTests`; `test_ocr_layout.py` › `ReadingOrderTests`, `ClampTests` |

### CP-12.3 — Página sin texto — Flujo alternativo

| Campo | Valor |
|---|---|
| Criterio | CA-12.3 |
| Precondición | Página propia sin texto, en "Pendiente de procesamiento" |
| Pasos | 1. Pulsar "Procesar página". 2. Esperar a que termine |
| Resultado esperado | La página pasa a "Procesada" con 0 regiones y se muestra "No se detectó texto en esta página." |
| Pruebas automáticas | `test_processing.py` › `PageWithoutTextTests`; `test_ocr_providers.py` › `test_a_page_without_text_returns_no_regions` |

### CP-12.4 — Falla el servicio de detección — Flujo alternativo

| Campo | Valor |
|---|---|
| Criterio | CA-12.4 |
| Precondición | El servicio externo no responde o devuelve un error |
| Pasos | 1. Pulsar "Procesar página" |
| Resultado esperado | La página pasa a **"Error"**, con el chip rojo también en la rejilla del álbum; se muestra el motivo y la opción "Reintentar", y no se pierde ninguna región anterior. Lo mismo ocurre si se queda "Procesando" más de cinco minutos. Al reintentar con el servicio repuesto, termina en "Procesada" |
| Pruebas automáticas | `test_processing.py` › `DetectionFailureTests`; `test_ocr_providers.py` › `AzureReadFailureTests` |

### CP-12.5 — Volver a procesar una página ya procesada — Flujo alternativo

| Campo | Valor |
|---|---|
| Criterio | CA-12.5 |
| Precondición | Página propia "Procesada" con regiones |
| Pasos | 1. Pulsar "Volver a procesar". 2. Pulsar "Cancelar". 3. Repetir y pulsar "Volver a procesar" en la confirmación |
| Resultado esperado | Se pide confirmación porque se reemplazarán las regiones. Al cancelar no cambia nada; al confirmar, las regiones se reemplazan por las nuevas |
| Pruebas automáticas | `test_processing.py` › `ReprocessTests` |

### CP-12.6 — Solo se procesan páginas propias — Flujo alternativo

| Campo | Valor |
|---|---|
| Criterio | CA-12.6 |
| Precondición | Existe una página de otra cuenta |
| Pasos | 1. Abrir su dirección directa. 2. Enviar un POST a su dirección de procesar |
| Resultado esperado | Ambas responden "Página no encontrada" (404) y la página ajena no cambia |
| Pruebas automáticas | `test_processing.py` › `OwnershipTests`; `config/tests/test_route_access.py` |

## Estrategia de pruebas automáticas de HU-12

Responde a la tabla que pide el documento maestro del Sprint 2.

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Agrupación de líneas y orden de lectura | Unitarias, con ejemplos | Algoritmo puro, con entradas y salidas exactas; es el "texto en desorden" que señaló el PO |
| Clasificación globo / cuadro | Unitarias con imágenes sintéticas de Pillow | Lógica aislada y sin archivos binarios en el repositorio |
| Adaptador de Azure | Integración con la red simulada (`unittest.mock`) | Comprueba el contrato de la API y cada error HTTP sin gastar cuota |
| Procesamiento de páginas | Escenarios (un CP por clase) con el proveedor simulado | Cada escenario Gherkin tiene su prueba |
| Vistas y control de acceso | Integración Django (`TestCase` + `Client`) con Huey en modo inmediato | Recorre petición → tarea → estado final y verifica el 404 entre cuentas |
