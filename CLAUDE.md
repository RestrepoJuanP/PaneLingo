# PaneLingo — Reglas del proyecto

## Qué es
Plataforma web para traducción asistida de cómics, manga y webtoons. El MVP del Sprint 1 cubre autenticación y gestión de álbumes y páginas. OCR, traducción con IA, workspace de traducción y exportación quedan FUERA del alcance del Sprint 1.

## Stack obligatorio (decidido en la wiki, no lo cambies)
- Python 3.12
- Django 5.x con Django Templates (renderizado en servidor)
- HTML + CSS + JavaScript vanilla
- Base de datos: SQLite en desarrollo (preparado para migrar a PostgreSQL)
- Pillow para imágenes
- Git + GitHub

PROHIBIDO: React, Vue, Node.js, Tailwind, Bootstrap o cualquier framework CSS/JS. Todo el CSS se escribe a mano con variables CSS. El JavaScript es mínimo, vanilla y solo para interacciones (modales, confirmaciones, previsualización de archivos).

## Estándares de nombramiento (PEP 8 + Django Coding Style)
Los identificadores del código van en INGLÉS. Los textos de la interfaz van en ESPAÑOL.

| Elemento | Convención | Ejemplo |
|---|---|---|
| Variables, funciones, métodos, parámetros | snake_case | `current_user`, `create_album()` |
| Clases y modelos | PascalCase | `AlbumService`, `Album` |
| Formularios | PascalCase + Form | `AlbumForm` |
| Vistas basadas en clases | PascalCase + View | `AlbumCreateView` |
| Constantes | UPPER_SNAKE_CASE | `MAX_FILE_SIZE` |
| Módulos y apps | snake_case / minúsculas | `album_service.py`, `accounts` |
| Tests | prefijo `test_` | `test_create_album()`, `test_album_views.py` |

Nada de nombres ambiguos (`a`, `x`, `img`). Booleanos con nombre semántico (`is_authenticated`, `has_pages`, `is_completed`).

## Herramientas de calidad
- **Ruff** para análisis estático, configurado en `pyproject.toml` con `select = ["E", "F", "N", "B", "I", "C90"]`, `line-length = 88`, `max-complexity = 10`.
- **Black** como formateador, `line-length = 88`.
- **Django system checks** (`python manage.py check`).
- **Django Test Framework** para pruebas automáticas.
- **pip-audit** para vulnerabilidades de dependencias.

## Quality Gate (obligatorio al final de CADA etapa)
Ejecuta en este orden y no reportes la etapa como terminada hasta que los siete pasen:

1. `ruff check . --fix`
2. `black .`
3. `ruff check .`
4. `black --check .`
5. `python manage.py check`
6. `python manage.py test`
7. `pip-audit -r requirements.txt`

El orden importa: Ruff aplica primero sus correcciones seguras (entre ellas el ordenamiento de imports de la regla `I`), luego Black da el formato definitivo, y los pasos 3 y 4 verifican que ninguna de las dos herramientas deshaga el trabajo de la otra. Si el paso 3 o el 4 falla después de haber pasado el 1 y el 2, hay un conflicto real de configuración: corrígelo en `pyproject.toml`, no repitiendo los comandos.

Si algún paso falla, corrígelo antes de continuar.

**Sobre `E501` (línea demasiado larga):** cuando Ruff marca líneas que Black no puede partir por sí solo (URLs largas, cadenas de texto, rutas), resuélvelo reescribiendo la línea — divide la cadena, extrae una constante, usa concatenación implícita entre paréntesis — o con un `noqa: E501` puntual acompañado de un comentario que explique el motivo. **Nunca desactives `E501` globalmente ni la quites de `select`:** la selección de reglas está documentada en la wiki y cambiarla invalida el criterio de calidad acordado. Lo mismo aplica a cualquier otra regla de `select`.

## Estrategia de ramas (GitHub Flow)
- `main` contiene código estable. Nunca trabajes directamente en `main`.
- Una rama por historia de usuario: `feature/HU-XX-descripcion-en-ingles`
- Bugs: `fix/BUG-XXX-descripcion` · Docs: `docs/tema` · Configuración: `chore/tema`
- Commits en formato Conventional Commits con el ID de la HU:
  - `feat(albums): HU-05 add album creation form`
  - `test(accounts): HU-01 add CP-01.1 and CP-01.2 cases`
- Al terminar una etapa: haz commit, push de la rama y muéstrame el comando `gh pr create` sugerido con título y descripción (la descripción debe listar la HU, los CA cubiertos y los CP verificados). **No hagas merge tú.**

## Seguridad
- `SECRET_KEY`, `DEBUG` y credenciales SIEMPRE desde variables de entorno. Nunca hardcodeadas ni versionadas.
- Mantén `.env` fuera de Git y provee un `.env.example` sin secretos.
- Todo formulario POST lleva `csrf_token`.
- **Aislamiento por propietario:** un usuario solo puede ver o modificar sus propios álbumes y páginas. Filtra siempre los querysets por `request.user`; si un objeto pertenece a otra cuenta, responde **404** (no 403, para no revelar existencia).
- Contraseñas con el hasher de Django y los validadores `AUTH_PASSWORD_VALIDATORS` activos.
- Las imágenes cargadas se guardan en `media/` organizadas por usuario y no se sirven públicamente sin control de acceso.

## Accesibilidad (WCAG 2.1 AA — requisito no funcional de la wiki)
- **Foco visible:** todo elemento interactivo muestra `:focus-visible` con `outline: 2px solid var(--brand)`, `outline-offset: 2px` y el halo `var(--focus-ring)`. Nunca uses `outline: none` sin un reemplazo visible.
- **Etiquetas de formulario:** toda entrada lleva un `<label>` asociado por `for`/`id`. El `placeholder` es una ayuda complementaria, jamás la única etiqueta. Los errores de validación se asocian con `aria-describedby`.
- **Imágenes:** `alt` descriptivo en imágenes de contenido (por ejemplo, la miniatura de una página cargada); `alt=""` en las decorativas para que los lectores de pantalla las omitan.
- **Regiones dinámicas:** los toasts van en un contenedor con `aria-live="polite"` (`assertive` solo para errores). Los modales atrapan el foco mientras están abiertos, lo devuelven al elemento que los invocó al cerrarse y se cierran con `Escape`.
- **Movimiento:** respeta `prefers-reduced-motion: reduce` desactivando las animaciones `rise`, `spin` y las transiciones de hover.
- **Teclado:** navegación completa sin ratón en menús contextuales, pills de idioma, filtros, grillas de página y modales. Los controles construidos sobre `<div>` no existen: usa `<button>`, `<a>` y controles nativos.
- **REGLA DE CONTRASTE (desviación deliberada respecto al mockup):** `--muted-2` (`#8a8478`, 3.7:1) y `--muted-3` (`#a09a8e`, 2.8:1) no alcanzan el 4.5:1 que AA exige para texto pequeño. Para cualquier texto por debajo de 14px usa `--muted` (`#6f6a60`, 5.4:1) o un tono más oscuro. Reserva `--muted-2` y `--muted-3` para texto sobre 18px, iconografía o elementos decorativos. La desviación, los contrastes medidos y su alcance real están documentados en `design/DESIGN_TOKENS.md`.

## Fidelidad visual (requisito del cliente)
La aplicación debe parecerse al mockup [`design/PaneLingo.dc.html`](design/PaneLingo.dc.html) en la mayor medida posible: misma paleta, misma tipografía, mismos radios, misma estructura de pantallas y mismos patrones de componentes. Consulta el mockup **ANTES** de maquetar cada pantalla nueva y no inventes un estilo distinto.

**Los tokens de diseño viven en [`design/DESIGN_TOKENS.md`](design/DESIGN_TOKENS.md) y ese archivo es la fuente de verdad visual del proyecto.**
Léelo antes de maquetar cualquier pantalla y usa sus nombres de variable CSS: no escribas valores hex, tamaños ni radios sueltos en las plantillas.

El mockup **no es código ejecutable**: usa plantillas propietarias con `sc-if`, `sc-for`, expresiones `{{ }}` y estilos en línea. No lo copies ni lo importes. Úsalo solo como referencia de composición y jerarquía, y reescribe cada pantalla como Django Templates + CSS propio con las variables de `DESIGN_TOKENS.md` declaradas en `:root`.

**Diferencia clave:** el mockup está redactado en inglés; nuestra interfaz va en **ESPAÑOL**, porque los casos de prueba de la wiki referencian botones como "Crear cuenta", "Cargar página", "Eliminar" y "Cancelar".

### Pantallas del mockup y su alcance en Sprint 1

| Pantalla | Sprint 1 | Trazabilidad | Notas |
|---|---|---|---|
| Auth split (panel oscuro + pestañas Log in / Create account) | Sí | HU-01, HU-02 | Iniciar sesión / Crear cuenta |
| Recuperación de contraseña (4 pantallas) | Sí | HU-04 | **No existe en el mockup.** Diseñar por extensión del layout de autenticación |
| Barra lateral — bloque de perfil con "Cerrar sesión" | Sí | HU-03 | El resto de la barra lateral queda fuera (ver fila siguiente) |
| Barra lateral — créditos mensuales, SSO, badge de plan | No | — | Funcionalidad de facturación y equipo, fuera del MVP |
| Dashboard con tarjetas de álbum | Sí | — | Mis álbumes |
| Modal "Create new album" | Sí (simplificado) | — | Modal "Crear álbum" |
| Detalle de álbum + grilla de páginas | Sí | — | Detalle del álbum / Páginas |
| Upload & scan pages (solo zona de carga y cola de archivos) | Sí, **sin** escaneo ni OCR | — | Cargar páginas |
| Modal "Eliminar página" | Sí | HU-10, CA-10.1, CA-10.2 | **No existe como tal en el mockup.** Reutilizar el patrón del modal de confirmación |
| Toast de confirmación | Sí | — | Mensajes de éxito y error |
| Modal "Delete album?" | **No** | — | Sin HU, CA ni CP en el Sprint 1. Acción visible pero deshabilitada (ver abajo) |
| Workspace de traducción dividido | No | — | — |
| Final review & export | No | — | — |
| Settings › Preferences / Team | No | — | — |

**Eliminar álbum — acción deshabilitada.** El botón "Eliminar" del detalle de álbum se maqueta con el estilo destructivo del mockup pero se renderiza en estado deshabilitado (`disabled`, `aria-disabled="true"`, cursor `not-allowed`, opacidad reducida) y con un texto de apoyo que indique que la funcionalidad llega en un Sprint posterior. No implementes vista, ruta, formulario ni servicio de borrado de álbumes: sería código sin historia de usuario ni caso de prueba que lo respalde.

**Recuperación de contraseña — cuatro pantallas a diseñar.** Se construyen reutilizando el layout dividido de autenticación (panel oscuro `--surface-navy` a la izquierda, formulario de `--w-auth-form` a la derecha) y sus componentes ya definidos: input, botón primario, botón secundario, alerta de error y toast. Las cuatro son:

1. **Solicitar restablecimiento** — un campo de correo y botón primario "Enviar enlace".
2. **Confirmación de envío** — estado informativo, sin formulario, con enlace de regreso a iniciar sesión. No revela si el correo existe.
3. **Definir nueva contraseña** — dos campos (contraseña y confirmación) con el medidor de fuerza del mockup y los validadores de Django.
4. **Resultado** — éxito con enlace a iniciar sesión, o enlace inválido/expirado con la opción de volver a solicitar.

Se apoyan en las vistas de `django.contrib.auth` (`PasswordReset*`) con plantillas propias. En desarrollo el correo va al backend de consola; **no configures envío real de correo en producción** (fuera de alcance).

Los elementos del mockup ligados a funcionalidad fuera de alcance (barras de progreso de traducción, chips "Needs review" / "Approved", contadores de bloques, "Resume translating") se omiten o se reemplazan por el estado real disponible en Sprint 1 (por ejemplo, número de páginas cargadas).

### Patrones de componente a respetar
- **Layout de la app:** barra lateral fija de `--w-sidebar` sobre `--surface` con `border-right: 1px solid var(--border)`; contenido principal con `padding: var(--pad-page)`; header sticky translúcido (`rgba(247,246,243,.92)` + `backdrop-filter: blur(8px)`) con miga de pan. En móvil la barra lateral se reemplaza por una navegación inferior fija.
- **Botón primario:** fondo `--brand`, texto `#fff`, `padding: var(--pad-btn)`, `border-radius: var(--r-lg)`, peso 700, hover `--brand-hover`.
- **Botón secundario:** fondo `--surface`, `border: 1px solid var(--border-strong)`, texto `--ink-800`, peso 600, hover `border-color: var(--border-hover)`.
- **Botón destructivo:** texto `--danger` sobre `--surface` con `border: 1px solid var(--danger-border-soft)`; en el modal de confirmación, fondo sólido `--danger` con texto blanco.
- **Input:** `padding: var(--pad-input)`, `border: 1px solid var(--border-strong)`, `border-radius: var(--r-lg)`, foco `border-color: var(--brand)` + `box-shadow: 0 0 0 3px var(--focus-ring)`.
- **Card:** `--surface`, `border: 1px solid var(--border)`, `border-radius: var(--r-3xl)` (`--r-2xl` en paneles); hover `transform: translateY(-2px)` + `--shadow-card-hover`.
- **Chip / píldora de estado:** `border-radius: var(--r-pill)`, `padding: var(--pad-chip)`, peso 700, tamaño `--fs-badge`, con la pareja fondo/texto de la tabla de colores semánticos.
- **Modal:** overlay `--overlay` + `blur(3px)`, tarjeta `--surface` con `border-radius: var(--r-modal)` y `--shadow-modal`; cabecera y pie separados por `1px solid var(--divider)`, pie con fondo `--surface-subtle`. Foco atrapado y cierre con `Escape`.
- **Toast:** fijo abajo y centrado, `border-radius: var(--r-xl)`, fondo `--ink-900` (éxito) o `--danger-deep` (error), texto blanco, contenedor con `aria-live`.
- **Estado vacío:** contenedor `border: 1.5px dashed var(--border-dashed-soft)`, `border-radius: var(--r-3xl)`, fondo `--surface-subtle`, texto centrado y botón primario de acción.
- **Grillas:** álbumes `repeat(auto-fill, minmax(252px, 1fr))` con `gap: var(--sp-8)`; páginas `repeat(auto-fill, minmax(146px, 1fr))` con `gap: var(--sp-7)`. Las miniaturas de página usan `aspect-ratio: var(--ratio-page)`.

## Alcance: qué NO hacer
No implementes OCR, detección de burbujas, traducción con IA, workspace de traducción dividido, exportación, colaboración en equipo, envío real de correo en producción, pagos, panel administrativo ni eliminación de álbumes. Si una pantalla del mockup pertenece a esas funcionalidades, no la construyas en el Sprint 1.

## Reglas de trabajo contigo
- Trabaja etapa por etapa. No adelantes trabajo de etapas futuras.
- Antes de escribir código en cada etapa, muéstrame un plan corto de archivos a crear o modificar y espera mi confirmación.
- Prefiere código simple y legible sobre abstracciones prematuras. Complejidad ciclomática máxima 10.
- Cada función y clase pública lleva docstring breve en español.
- Las pruebas automáticas referencian en su docstring el CP de la wiki que verifican (por ejemplo: `"CP-05.1 — Crear álbum correctamente — Happy Path"`).
- No construyas funcionalidad sin HU, CA y CP que la respalden. Si detectas un hueco de trazabilidad, dímelo antes de implementar.
