# ADR-001 — Proveedor de detección y OCR, y ejecución asíncrona del procesamiento

| Campo | Valor |
|---|---|
| Estado | **Aceptado** por el responsable de OCR el 2026-10-20; pendiente de revisión por el equipo en el PR de HU-12 |
| Fecha | 2026-10-20 |
| Responsable | Andres Velez (responsable de OCR, HU-12 y HU-13) |
| Historias afectadas | HU-12, HU-13 y, por el contrato de datos, HU-14, HU-15, HU-16 y HU-22 |
| Requisitos | RF-07; RNF de rendimiento: menos de 10 s por página (wiki, Sprint 0) |

## 1. Contexto

HU-12 pide que una página pase de "Pendiente de procesamiento" a "Procesada" con sus regiones de texto detectadas, y que el usuario pueda **seguir usando PaneLingo mientras tanto** (CA-12.1). Eso deja dos decisiones abiertas en la definición de listo de la HU:

1. **Qué servicio detecta las regiones y reconoce el texto.** HU-13 extrae el texto de esas mismas regiones, así que el proveedor es compartido.
2. **Cómo se ejecuta el trabajo fuera de la petición web.** La arquitectura de la wiki propone Redis + BullMQ, pero BullMQ es una biblioteca de Node.js, y el stack obligatorio del proyecto es Django y prohíbe Node.js.

Restricciones que condicionan ambas decisiones:

- Stack Python 3.12 + Django 5.x, sin infraestructura adicional en desarrollo: cada integrante ejecuta el proyecto en su portátil, con Windows o Linux.
- Las claves del proveedor viven solo en el servidor, en variables de entorno (RNF de la HU).
- Las pruebas automáticas **no llaman al servicio externo**: lo simulan (definición de terminado de HU-12). Esto también vale para la integración continua.
- El Quality Gate incluye `pip-audit`: cada dependencia nueva es superficie que auditar.
- El PO indicó que el OCR falla sobre todo con japonés, chino y coreano, y que "imprime el texto en desorden" (entrevista del 08/08/2026).

## 2. Decisión 1 — Proveedor detrás de un adaptador

### 2.1 Decisión

El dominio **no conoce a ningún proveedor concreto**. Define una interfaz mínima, `OcrProvider`, con una sola operación:

```
detect(image_bytes) -> list[DetectedRegion]
```

El idioma no forma parte de la firma: Azure lo detecta solo (ver más abajo), y el idioma de origen del álbum lo usa PaneLingo para el orden de lectura.

`DetectedRegion` es el **contrato de datos** que comparten HU-12, HU-13 y HU-14:

| Campo | Tipo | Lo usa |
|---|---|---|
| `x`, `y`, `width`, `height` | enteros, en píxeles de la imagen original | HU-12 |
| `text` | cadena, puede estar vacía | HU-13 |
| `confidence` | decimal de 0 a 1, o vacío si el proveedor no lo da | HU-13 |

El tipo de región (globo de diálogo o cuadro narrativo) y el orden de lectura **no** los decide el proveedor: los calcula PaneLingo (ver §4), para que cambiar de proveedor no altere esa lógica.

Se implementan dos adaptadores:

| Adaptador | Cuándo se usa | Qué hace |
|---|---|---|
| `FakeOcrProvider` | Pruebas automáticas, integración continua y desarrollo sin clave | Devuelve regiones deterministas. Se puede configurar para devolver 0 regiones o para fallar, y así cubrir CA-12.3 y CA-12.4 |
| `AzureReadProvider` | Desarrollo con clave y demostración | Llama a Image Analysis 4.0 con `features=read` y devuelve una región por cada línea de texto. Agrupar esas líneas en globos lo hace PaneLingo (ver S4 en §4) |

El adaptador activo se elige con la variable de entorno `OCR_PROVIDER` (`fake` por defecto). Las credenciales van en `AZURE_VISION_ENDPOINT` y `AZURE_VISION_KEY`.

Detalles de la llamada, según la [documentación de Image Analysis 4.0](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/how-to/call-analyze-image-40):

- `POST <endpoint>/computervision/imageanalysis:analyze?api-version=2024-02-01&features=read`
- Cabecera `Ocp-Apim-Subscription-Key` con la clave y cuerpo binario con `Content-Type: application/octet-stream`.
- Es **síncrona**: la respuesta trae el resultado y no hay que consultar después.
- La respuesta llega en `readResult.blocks[].lines[]`. Cada línea trae `text`, `boundingPolygon` (cuatro puntos) y `words[]`, y cada palabra su propia `confidence` de 0 a 1. La confianza de la región es la media de las de sus palabras.
- **No se envía el idioma.** El modelo es multilingüe y Microsoft recomienda no forzarlo, porque puede devolver texto incompleto. El idioma de origen del álbum se usa solo para el orden de lectura.

`AzureReadProvider` usa la **API REST con la biblioteca estándar** (`urllib.request`), no el SDK `azure-ai-vision-imageanalysis`. Así no hay ninguna dependencia nueva que auditar ni que instalar en cada portátil, para una única llamada HTTP.

### 2.2 Alternativas comparadas

Precios consultados el 2026-10-20. Hay que confirmarlos antes de usarlos en la Sección 4 (Finanzas) del caso de negocio.

| Opción | Detección y OCR en una llamada | Japonés, coreano y chino | Coste por página | Infraestructura | Valoración |
|---|---|---|---|---|---|
| **Azure AI Vision — Read** (Image Analysis 4.0) | Sí: líneas con posición y confianza por palabra | Sí, también chino tradicional | **Nivel F0 gratuito: unas 5 000 transacciones al mes, a 20 por minuto.** El precio del nivel de pago no está confirmado (≈ USD 1–1,50 por 1 000) | Ninguna: HTTP y una clave. **El equipo ya tiene cuenta de Azure** | **Elegida.** Gratis para el volumen del MVP, sin dependencias y sin cuentas nuevas |
| Google Cloud Vision (`DOCUMENT_TEXT_DETECTION`) | Sí: bloques con posición, texto y confianza | Sí | 1 000 al mes gratis; luego USD 1,50 por 1 000 | HTTP y una clave, pero pide una cuenta de facturación con tarjeta | Equivalente en calidad. Se descarta por la cuota gratuita más baja y por la tarjeta |
| OCR.space | Sí: palabras con posición | Solo con Engine 3, que da 2 500 al mes | Gratis: 25 000 peticiones al mes, máximo 500 al día | HTTP y una clave obtenida con un correo | Se descarta: limita las imágenes a 1 MB (nuestro límite es 10 MB) y no se encontró que devuelva confianza, que necesita HU-13 |
| PaddleOCR 3 / PP-OCRv5 (local) | Sí, con posición y confianza | Japonés y chino en el modelo principal; coreano en uno propio | Gratis, sin límites | PaddlePaddle (cientos de MB), problemas conocidos en Windows y no admite el Python 3.14 de algunos equipos | Se aplaza: buena opción privada y sin cuotas, como adaptador opcional en un sprint posterior |
| IA con visión (Gemini Flash-Lite) | Podría dar también el tipo de región y el orden | Sí | Tiene nivel gratuito | HTTP y una clave | Se descarta: en el nivel gratuito Google usa el contenido para mejorar sus productos, y serían las obras del cliente |
| Tesseract (local) | Sí, con regiones | Débil con texto vertical japonés y con letra de manga | Gratis | Binario nativo en cada máquina | Se descarta: precisión insuficiente para el problema que señaló el PO |
| manga-ocr + comic-text-detector (local) | No: son dos modelos | Muy bueno en japonés; sin coreano ni chino | Gratis | PyTorch y modelos de cientos de MB | Se descarta para el MVP por el peso y por cubrir solo japonés |
| AWS Textract | Sí | **No** soporta japonés, coreano ni chino | — | — | Se descarta |

### 2.3 Consecuencias

- Las pruebas son rápidas, deterministas y no gastan cuota ni necesitan red.
- Cambiar de proveedor, o añadir PaddleOCR más adelante, es escribir un adaptador nuevo sin tocar vistas, modelos ni pruebas de dominio.
- El nivel F0 admite unas 20 peticiones por minuto. Con un único trabajador procesando de una en una, no se alcanza. Si Azure responde 429 (demasiadas peticiones), se trata como un fallo recuperable: CA-12.4, con "Reintentar".
- Riesgo: Azure devuelve **líneas**, no globos. PaneLingo las agrupa por proximidad (S4). Dos globos muy juntos pueden salir como una sola región, y un globo grande como dos. El usuario podrá corregirlo en HU-15. Se mide con el juego de páginas de prueba (pendiente, ver §6).
- Riesgo: depender de un servicio externo y de su cuota. Hay que llevarlo al inventario de riesgos de la Sección 5 del caso de negocio. La mitigación es CA-12.4: si el servicio falla, la página pasa a "Error" y se puede reintentar sin perder datos.

## 3. Decisión 2 — Huey con almacenamiento SQLite para las tareas en segundo plano

### 3.1 Decisión

El procesamiento de una página se ejecuta como tarea de **[Huey](https://huey.readthedocs.io/)**, con su integración para Django (`huey.contrib.djhuey`) y el almacenamiento **`SqliteHuey`**: la cola vive en un archivo SQLite propio (`huey.sqlite3`), separado de `db.sqlite3` y fuera de Git.

Flujo:

1. La vista recibe el POST "Procesar página", pone la página en "Procesando" y encola la tarea con `transaction.on_commit`, para que el trabajador no lea la página antes de que se guarde el cambio de estado.
2. La vista responde enseguida y el usuario puede seguir navegando (CA-12.1).
3. El trabajador (`python manage.py run_huey`, en otra terminal) ejecuta la detección y guarda el resultado.

Configuración:

- `worker_type = "thread"`: el tipo `process` depende de `fork` y no funciona igual en Windows.
- `immediate` se controla con la variable `HUEY_IMMEDIATE`. Con `True`, la tarea se ejecuta dentro de la misma petición. Sirve para las pruebas y para demostrar sin levantar el trabajador.

### 3.2 Alternativas comparadas

| Opción | Infraestructura extra | Windows | Valoración |
|---|---|---|---|
| Redis + BullMQ (wiki) | Redis y **Node.js** | — | **Incompatible** con el stack obligatorio |
| Celery + Redis | Servidor Redis | Celery no soporta Windows oficialmente desde la versión 4 | Se descarta: demasiado para el MVP y frágil en los equipos del grupo |
| RQ + Redis | Servidor Redis | RQ necesita `fork`: no funciona en Windows | Se descarta |
| django-q2 (broker ORM) | Ninguna | Sí | Viable. Se prefiere Huey por tener menos dependencias y un modo inmediato integrado para las pruebas |
| Tareas nativas de Django (`django.tasks`) | — | — | Llegan con Django 6.0; el proyecto fija Django 5.2. Se revisará al migrar |
| Hilo lanzado desde la vista | Ninguna | Sí | Se descarta: si el servidor se reinicia, la tarea se pierde sin rastro y no hay reintentos |
| **Huey + SqliteHuey** | **Ninguna** | **Sí**, con trabajador de hilos | **Elegida** |

### 3.3 Consecuencias

- Una dependencia nueva: `huey` (versión 3.x, Python puro). Entra en `requirements.txt` y pasa por `pip-audit`.
- Hay que arrancar un segundo proceso (`run_huey`). Se documenta en el README. Con `HUEY_IMMEDIATE=True` no hace falta.
- SQLite admite un solo escritor a la vez. Basta para un trabajador y el volumen de un traductor. Para desplegar con varios trabajadores, el cambio es una línea: `huey_class` pasa a `RedisHuey` o `PostgresHuey`, sin tocar las tareas.
- Si el trabajador se cae a mitad de una tarea, la página quedaría "Procesando" para siempre. Mitigación: se guarda `processing_started_at`. Pasado `PROCESSING_STALE_AFTER` (5 minutos), la próxima consulta de la página la pasa a "Error" y se ofrece "Reintentar". Si el trabajador terminara después, ya no la toca, porque solo procesa páginas que siguen "Procesando".

## 4. Decisiones de dominio asociadas (supuestos provisionales)

Las preguntas al PO de la definición de listo siguen abiertas. Para no bloquear el desarrollo se trabaja con estos supuestos. Cada uno está aislado en un solo punto del código para poder cambiarlo si el PO decide otra cosa.

| # | Pregunta | Supuesto provisional | Motivo |
|---|---|---|---|
| S1 | ¿Hace falta un estado "Error"? | **Resuelto el 2026-10-20: sí.** Si la detección falla, o la página queda "Procesando" más de `PROCESSING_STALE_AFTER`, pasa a **"Error"** (`ComicPage.Status.FAILED`). El motivo se guarda en `processing_error` y se muestra junto a "Reintentar". Las regiones que ya tuviera se conservan | Distingue una página que falló de una que nunca se procesó. **Cambia el texto de CA-12.4** ("vuelve a Pendiente" → "pasa a Error") y añade un estado a la tabla de HU-22 y a la derivación del estado del álbum de HU-26 |
| S2 | ¿Reprocesar descarta las correcciones manuales? | **Sí, tras confirmación.** Las regiones nuevas reemplazan a las anteriores solo si la detección termina bien | CA-12.5 pide confirmación "porque se reemplazarán sus regiones"; CA-12.4 exige no perder datos si falla |
| S3 | ¿Cómo se distingue un globo de un cuadro narrativo? | Heurística: luminosidad media del interior de la región. Fondo claro → globo; fondo oscuro o de color → cuadro narrativo | Ningún proveedor lo clasifica. Es una primera aproximación, medible con el juego de páginas de prueba y corregible a mano en HU-15 |
| S4 | Cómo se forman las regiones y en qué orden se leen | Las líneas que devuelve el proveedor se agrupan en una región cuando sus cajas se tocan o están separadas por menos de la altura de una línea. Las regiones se agrupan después en filas por solapamiento vertical; dentro de cada fila van de derecha a izquierda si el idioma de origen es japonés, y de izquierda a derecha en el resto | CA-12.1 y CA-12.2. El coreano (webtoon) y el chino simplificado se leen de izquierda a derecha |
| S5 | Juego de páginas de prueba | Pendiente: lo aporta el equipo o el PO. Las pruebas automáticas no lo necesitan porque usan el proveedor simulado | Lo necesita la medición de precisión de HU-13 (CA-13.4) |
| S6 | HU-13, CA-13.2: "el reconocimiento se hace en el idioma de origen" | **Decidido el 2026-10-20:** no se fuerza el idioma en Azure (ver §2.1). Se comprueba el resultado: si el texto de una región tiene letras y ninguna es del alfabeto del idioma de origen (kana o kanji en japonés, hangul en coreano, hanzi en chino, latino en el resto), la región se marca para revisión | Cumple el objetivo del criterio, que es que no pase inadvertido un texto mal reconocido, sin perder texto por forzar el idioma |
| S7 | HU-13, CA-13.3: umbral de confianza | **70 % provisional** (`OCR_REVIEW_THRESHOLD`), el que propone el backlog. Una región sin texto o sin confianza también se marca | Pendiente de confirmar por el PO con el juego de páginas de prueba |

## 5. Estrategia de pruebas automáticas de HU-12

Responde a la tabla del documento maestro del Sprint 2: cada funcionalidad lleva al menos una prueba de happy path y otra de flujo alternativo.

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Agrupación de líneas en regiones y orden de lectura (S4) | Unitarias, con ejemplos | Es un algoritmo puro: entradas y salidas exactas, sin base de datos, y es justo el "desorden" que señaló el PO |
| Clasificación globo / cuadro (S3) | Unitarias, con imágenes sintéticas generadas con Pillow | Lógica aislada; las imágenes se generan en la prueba, así que no hay archivos binarios en el repositorio |
| Adaptador de Azure Read | Integración con la red simulada (`unittest.mock` sobre `urlopen`) y una respuesta JSON de ejemplo con la forma de `readResult` | Verifica la traducción de la respuesta al contrato `DetectedRegion` y el manejo de los errores HTTP (401, 429, 5xx y tiempo de espera) sin gastar cuota |
| Servicio de procesamiento | Escenarios (CA-12.1, 12.3, 12.4 y 12.5) con `FakeOcrProvider` | Cada escenario Gherkin se corresponde con una prueba que cita su CP en el docstring |
| Vistas de procesar y de ver la página | Integración Django (`TestCase` + `Client`) con Huey en modo inmediato | Recorre el flujo completo petición → tarea → estado final, y el aislamiento por propietario (CA-12.6 → 404) |
| Rutas nuevas | Auditoría existente `config/tests/test_route_access.py` | Garantiza que las rutas nuevas exigen sesión |

## 6. Pendientes fuera de este ADR

- Ejecutar `python manage.py ocr_accuracy_report <carpeta>` sobre el juego de páginas de prueba (S5) y acordar con el PO los umbrales de CA-13.4 (`OCR_ACCURACY_THRESHOLDS`). El informe resultante es la evidencia de precisión de HU-13.

- Que el PO responda S2 (y, de paso, S3). S1 quedó resuelto: hay estado "Error".
- Actualizar en el issue #12 el texto de CA-12.4 y avisar a los responsables de HU-22 y HU-26 del estado nuevo.
- El juego de páginas de prueba (S5).
- Crear en la cuenta de Azure del equipo un recurso **Computer Vision en el nivel F0** (gratuito) y repartir el endpoint y la clave por un canal privado, nunca en el repositorio. Con F0 no hay cobro posible: al agotar la cuota, Azure responde 429 hasta el mes siguiente.
- Añadir la medición de coverage (`coverage.py`) al Quality Gate. Lo pide el documento maestro para todo el equipo; se propone como tarea `chore` aparte.
