# ADR-002 — Traducción asistida por IA: proveedor, modelo de datos y flujo de revisión

| Campo | Valor |
|---|---|
| Estado | **Propuesto** el 2026-10-21; pendiente de revisión por el equipo y de las decisiones del PO marcadas con ⚠️ |
| Fecha | 2026-10-21 |
| Responsable | Andres Velez, con Tomás Sepúlveda (HU-16, HU-19) y Juan Pablo Restrepo (HU-17, HU-18) |
| Historias afectadas | HU-16, HU-17, HU-18, HU-19 y, por el contrato de datos, HU-22, HU-25, HU-26 y HU-27 |
| Requisitos | RF-09 y RF-10; RNF de rendimiento: menos de 10 s por página |
| Referencias | [ADR-001](ADR-001-proveedor-ocr-y-tareas-asincronas.md) (adaptador y Huey); mockup `design/PaneLingo.dc.html`, pantalla *Workspace* |

## 1. Contexto

Con HU-12 a HU-15, cada página tiene sus regiones de texto en orden de lectura, con su tipo (globo o cuadro narrativo) y el texto de origen ya revisado. El siguiente paso del flujo es traducir:

- **HU-16** pide generar con IA una propuesta de traducción por región, **con el contexto de la página entera** y no frase a frase (CA-16.2).
- **HU-17, HU-18 y HU-19** piden revisar, editar y aprobar esas traducciones en la misma pantalla.

El mockup resuelve las cuatro en el espacio de trabajo. Cada bloque de texto muestra:
- el texto de origen y la traducción editable;
- un chip de estado y la confianza;
- los botones "Approve block" y "Retry AI".

Además tiene una nota con el contexto de la página, un contador de bloques aprobados y atajos de teclado ("Enter: aprobar y pasar al siguiente").

Restricciones heredadas de ADR-001:
- Stack Django sin infraestructura extra.
- Las claves solo en variables de entorno.
- Las pruebas nunca llaman al servicio real.
- Toda dependencia nueva pasa por `pip-audit`.

## 2. Decisión 1 — Proveedor de traducción detrás de un adaptador: Google Gemini

### 2.1 Decisión

Igual que el OCR, el dominio solo conoce una interfaz, `TranslationProvider`, con una operación:

```
translate(request: PageTranslationRequest) -> list[RegionTranslation]
```

`PageTranslationRequest` es el contrato que envía el **contexto de la página** (CA-16.2):

| Campo | Contenido |
|---|---|
| `source_language`, `target_language` | Nombres de los idiomas del álbum, por ejemplo "japonés" y "español" |
| `regions` | Todas las regiones de la página en orden de lectura. Cada una lleva su número, su tipo, su texto (`final_text`, es decir, la corrección de HU-15 si existe) y si hay que traducirla o va solo como contexto |

`RegionTranslation` devuelve, por cada región pedida, su número y su traducción.

Dos adaptadores:

| Adaptador | Cuándo | Qué hace |
|---|---|---|
| `FakeTranslationProvider` | Pruebas, integración continua y desarrollo sin clave | Traducción determinista ("[ES] texto"). Se puede configurar para fallar o para omitir regiones, y así cubrir CA-16.4 |
| `GeminiProvider` | Desarrollo con clave y demostración | Llama a la API de Gemini (`generateContent`) con **salida JSON estructurada**: un esquema que exige un objeto por región con `number` y `translation` |

Configuración por variables de entorno:
- `TRANSLATION_PROVIDER` (`fake` por defecto);
- `GEMINI_API_KEY`;
- `GEMINI_MODEL`: se usa un modelo *Flash* del nivel gratuito, y el nombre exacto se fija al probar la clave.

Detalles de la llamada:
- `POST https://generativelanguage.googleapis.com/v1beta/models/<modelo>:generateContent`, con la clave en la cabecera `x-goog-api-key` (nunca en la URL, para que no quede en los registros).
- Una instrucción de sistema fija:
  - traductor de cómic;
  - respetar el tipo de región, el tono y los signos de cada idioma;
  - traducir solo las regiones marcadas;
  - devolver el mismo número de región.
  - Sin selector de estilo, como pide CA-16.6.
- `responseMimeType: application/json` y `responseSchema`, para que la respuesta se pueda validar.
- Igual que `AzureReadProvider`: **API REST con `urllib.request`**, sin SDK. Ninguna dependencia nueva.
- Tiempo de espera de 60 s. Los errores 400, 401, 403, 429 y 5xx, el tiempo agotado y una respuesta que no cumple el esquema se convierten en `TranslationError`, que es el caso de CA-16.4.

### 2.2 Alternativas comparadas

Consultadas el 2026-10-21. Las cuotas gratuitas cambian a menudo y las fuentes no coinciden; las de Gemini se ven por proyecto en la consola de AI Studio.

| Opción | Contexto de página | Japonés → español | Coste | Puesta en marcha | Valoración |
|---|---|---|---|---|---|
| **Google Gemini (AI Studio), modelos Flash** | Sí, con salida JSON estructurada | Bueno | **Nivel gratuito sin tarjeta**, con límites por minuto y por día | Clave con una cuenta de Google; una llamada HTTP | **Elegida** por el equipo el 2026-10-21 |
| Groq (modelos abiertos) | Sí | Aceptable; los modelos abiertos rinden menos en japonés | Gratis sin tarjeta | Clave y API compatible con OpenAI | Alternativa si se agota la cuota de Gemini |
| OpenRouter (modelos `:free`) | Sí | Depende del modelo | Gratis, unas 50 peticiones al día | Clave | Se descarta: cuota diaria insuficiente para probar |
| Claude (Anthropic) | Sí | Muy bueno | De pago por uso | Clave con saldo | Se descarta para el MVP por coste; sigue siendo la opción de calidad para producción |
| Azure AI Translator | **No**: traduce frases sueltas | Bueno | 2 M caracteres al mes gratis | Ya hay cuenta de Azure | Se descarta: incumple CA-16.2 |
| GitHub Models | Sí | Bueno | Gratis con límites | Token de GitHub | Se descarta: se informó de su retirada a mitad de 2026 y no se pudo confirmar su estado |

### 2.3 Consecuencias y riesgos

- **⚠️ Privacidad (decisión del PO).** En el nivel gratuito, Google puede usar el contenido enviado para mejorar sus productos. ADR-001 descartó Gemini para el OCR justo por eso. Aquí el riesgo es menor, porque se envía **texto y no las imágenes**, pero sigue siendo la obra del cliente. Se acepta **solo para el MVP y con material de prueba**. Antes de usar obras reales hay que pasar al nivel de pago de Gemini (que no usa los datos para entrenar) o a otro adaptador; cambiarlo es solo configuración. Va al inventario de riesgos de la Sección 5 del caso de negocio.
- **Cuota.** Una página es una sola petición, así que un álbum de 20 páginas son 20 peticiones. Un 429 se trata como fallo recuperable, con "Reintentar".
- **Calidad.** La IA puede equivocarse. Por eso todo pasa por revisión y aprobación humana (HU-17 a HU-19), y la propuesta original de la IA se conserva (CA-18.1).
- Cambiar de proveedor es escribir otro adaptador, sin tocar dominio, vistas ni pruebas.

## 3. Decisión 2 — La traducción vive en la región

### 3.1 Decisión

Cada región de texto tiene una sola traducción vigente. Se añaden campos a `TextRegion`, igual que hizo HU-15 con la corrección del texto de origen:

| Campo | Para qué |
|---|---|
| `machine_translation` | Propuesta de la IA, que se conserva aunque se edite (CA-18.1) |
| `translation` | Texto de trabajo: el que se revisa, se edita, se aprueba y se exportará |
| `translation_status` | `untranslated` · `generated` · `edited` · `approved`; en pantalla, "Sin traducir", "Generada", "Editada" y "Aprobada" (CA-17.3) |
| `translated_at`, `approved_at` | Fechas de la última propuesta y de la aprobación (CA-19.1) |

Y a `ComicPage`, el estado de la tarea de traducción, separado del estado de la página para no mezclar OCR y traducción:

| Campo | Para qué |
|---|---|
| `translation_state` | `idle` · `translating` · `failed` |
| `translation_error`, `translation_started_at` | Mensaje para "Reintentar" (CA-16.4) y detección de tareas colgadas, igual que en ADR-001 |

### 3.2 Alternativa descartada

Un modelo `Translation` aparte, con historial de versiones, permitiría deshacer varias ediciones, pero ninguna HU lo pide. CA-18.1 solo exige conservar la propuesta de la IA. Se puede migrar más adelante sin romper el contrato.

### 3.3 Transiciones

```
Sin traducir --(Traducir página / Reintentar IA)--> Generada --(editar y guardar)--> Editada
Generada | Editada --(Aprobar)--> Aprobada --(editar, o Retirar aprobación)--> Editada
```

- **CA-16.3:** al traducir de nuevo la página, las regiones **Aprobadas** viajan como contexto pero no se piden ni se sobrescriben.
- **CA-19.2:** cuando todas las regiones que necesitan traducción están Aprobadas, la página pasa a "Aprobada" (`ComicPage.Status.APPROVED`, que ya existe). Al retirar o editar una aprobación vuelve a "Procesada" (CA-19.4).

## 4. Decisión 3 — La traducción corre en segundo plano con Huey

Se reutiliza la infraestructura de ADR-001. La tarea `translate_page_task` sigue el mismo patrón que el OCR:

1. "Traducir página" pone `translation_state = translating`.
2. La tarea se encola con `transaction.on_commit`.
3. La vista se actualiza sola al terminar (CA-16.1).

Si falla, el estado pasa a `failed` con su mensaje y **no se toca ninguna traducción existente** (CA-16.4). "Reintentar IA" en una sola región (el "Retry AI" del mockup) envía igualmente la página entera como contexto, pero solo aplica el resultado a esa región.

## 5. Decisiones de dominio (supuestos provisionales)

| # | Pregunta | Supuesto | Motivo |
|---|---|---|---|
| T1 | ⚠️ CA-18.4: ¿se puede guardar una traducción vacía? | **Sí**, como decisión explícita de "dejar sin traducir" (por ejemplo, una onomatopeya). Queda "Editada" y se puede aprobar | Mantiene la coherencia con HU-15 (región vacía = "sin texto que traducir") y deja que la página llegue a "Aprobada" |
| T2 | ⚠️ HU-19: ¿botón "Aprobar todas"? | **No** en esta versión. En su lugar, "Aprobar y pasar a la siguiente" | Mantiene el control fino que pide la HU y reduce clics como el atajo Enter del mockup |
| T3 | ⚠️ HU-17 y HU-18: ¿se fusionan? | **Sí**: una sola pantalla de revisión y edición, que es el espacio de trabajo, como en el mockup y como recomienda el issue (nota INVEST) | Revisar sin poder editar no entrega valor por sí solo |
| T4 | CA-17.2: atajos de teclado | Botones "Región anterior" y "Región siguiente" en el panel. **Alt+↓ / Alt+↑** para moverse entre regiones y **Ctrl+Enter** para aprobar y pasar a la siguiente. No se usan teclas sueltas | Las flechas sin modificador ya pasan de página (HU-11), y las teclas de una letra chocan con los lectores de pantalla (WCAG 2.1.4) |
| T5 | ¿Qué regiones se traducen? | Las que tienen texto final. Las marcadas "sin texto que traducir" en HU-15 se excluyen, no cuentan como pendientes y no impiden que la página quede "Aprobada" | Coherente con CA-15.5 |
| T6 | Volver a procesar el OCR con traducciones | Igual que con las correcciones (S2 de ADR-001): las regiones se reemplazan y **las traducciones se pierden**. El aviso de confirmación dirá cuántas | Las traducciones pertenecen a regiones que dejan de existir |
| T7 | Elementos del mockup sin HU | **Fuera de alcance:** notas de glosario (*TERM*), "Add a missed text region", selector de estilo (lo prohíbe CA-16.6), revisión final con mapa de páginas y exportación (HU-27 y HU-28, Sprint 3) | Regla del proyecto: nada sin HU, CA y CP |

## 6. Estrategia de pruebas automáticas

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Construcción del contexto de la página (qué regiones van, en qué orden, cuáles solo como contexto) | Unitarias | Lógica pura; es el núcleo de CA-16.2 y CA-16.3 |
| Adaptador de Gemini | Integración con la red simulada (`unittest.mock`): URL, cabecera de la clave, esquema JSON, errores 401/429/5xx, tiempo agotado y respuesta inválida | Contrato con la API sin gastar cuota |
| Traducir una página | Escenarios por CP con el proveedor simulado y Huey inmediato | Un caso de prueba por criterio de aceptación |
| Editar, aprobar y retirar | Escenarios por vista y unitarias de las transiciones | CA-18.x y CA-19.x |
| Aislamiento | Región o página de otra cuenta → 404 en cada acción nueva, clasificadas en `test_route_access.py` | Definición de terminado de todas las HU |

La cobertura sigue con el mínimo del 90 % de la CI.

## 7. Pendientes fuera de este ADR

- ⚠️ El PO debe aceptar el riesgo de privacidad (§2.3) y decidir T1, T2 y T3.
- Medir la calidad de la traducción con el juego de páginas de prueba de CA-13.4 cuando exista.
- Contexto entre páginas (la nota "Context carried from page N" del mockup): ninguna HU lo pide; queda como mejora.
