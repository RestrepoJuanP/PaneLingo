# PaneLingo

Plataforma web para la **traducción asistida de cómics, manga y webtoons**. PaneLingo permite a un traductor organizar su trabajo en álbumes, cargar las páginas completas de cada obra y gestionarlas desde un espacio propio y privado.

Proyecto académico desarrollado para **Proyecto Integrador 2**. Hoy PaneLingo cubre el flujo completo de una página: autenticación, álbumes y páginas, detección y OCR del texto, traducción asistida por IA con revisión y aprobación humanas, autoguardado y progreso del trabajo, limpieza del texto original, maquetación de la traducción sobre la imagen y exportación en DOCX o en PNG. Lo que todavía no incluye está en [Fuera del alcance actual](#fuera-del-alcance-actual).

## Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Framework | Django 5.2 con Django Templates (renderizado en servidor) |
| Frontend | HTML, CSS y JavaScript vanilla — sin frameworks CSS/JS |
| Base de datos | SQLite en desarrollo, preparada para migrar a PostgreSQL |
| Imágenes | Pillow |
| Configuración | python-dotenv |
| Calidad | Ruff, Black, Django Test Framework, pip-audit |
| Control de versiones | Git + GitHub Flow |

## Pantallas implementadas en el Sprint 1

| Pantalla | Ruta | Historia |
|---|---|---|
| Crear cuenta | `/cuentas/registro/` | HU-01 |
| Iniciar sesión | `/cuentas/ingresar/` | HU-02 |
| Cerrar sesión | `/cuentas/salir/` (POST) | HU-03 |
| Recuperar contraseña — solicitar | `/cuentas/recuperar/` | HU-04 |
| Recuperar contraseña — confirmación de envío | `/cuentas/recuperar/enviado/` | HU-04 |
| Recuperar contraseña — nueva contraseña | `/cuentas/recuperar/<uid>/<token>/` | HU-04 |
| Recuperar contraseña — resultado | `/cuentas/recuperar/listo/` | HU-04 |
| Mis álbumes | `/` | HU-05 |
| Crear álbum | `/albumes/nuevo/` | HU-05, HU-06, HU-07 |
| Detalle de álbum | `/albumes/<id>/` | HU-08 |
| Editar álbum | `/albumes/<id>/editar/` | HU-08 |
| Renombrar álbum | `/albumes/<id>/renombrar/` | HU-06 |
| Elegir álbum para cargar | `/albumes/cargar/` | HU-09 |
| Cargar páginas | `/albumes/<id>/cargar/` | HU-09 |
| Eliminar página | `/paginas/<id>/eliminar/` | HU-10 |

Más `/design-system/`, la referencia de estilos, que **solo existe en desarrollo**.

### Edición de imagen (EP-08, Sprint 3)

| Pantalla | Ruta | Historia |
|---|---|---|
| Espacio de trabajo — pestaña Maquetación | `/paginas/<id>/?paso=maquetacion` | HU-89 |
| Revisión y exportación — DOCX o páginas traducidas (PNG en un ZIP) | `/albumes/<id>/exportar/` | HU-27, HU-90 |
| Descargar una exportación (DOCX o ZIP) | `/exportaciones/<id>/descargar/` | HU-28, HU-90 |

La pestaña Maquetación solo se habilita cuando la página tiene imagen limpia y regiones de texto. Cómo probarla en local: [Maquetación y exportación PNG en desarrollo](#maquetación-y-exportación-png-en-desarrollo).

## Requisitos previos

- Python 3.12 o superior
- Git
- pip (incluido con Python)

Verifica tu versión antes de empezar:

```bash
python --version
```

## Instalación

**1. Clona el repositorio**

```bash
git clone <url-del-repositorio>
cd panelingo
```

**2. Crea y activa el entorno virtual**

```bash
# Windows (PowerShell)
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3.12 -m venv .venv
source .venv/bin/activate
```

**3. Instala las dependencias**

```bash
pip install -r requirements-dev.txt
```

`requirements.txt` contiene solo lo necesario para ejecutar la aplicación; `requirements-dev.txt` lo incluye y añade las herramientas de calidad.

**4. Configura las variables de entorno**

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Genera una clave secreta y pégala en `DJANGO_SECRET_KEY` dentro de `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

El archivo `.env` **nunca se versiona**. `DJANGO_DEBUG` vale `False` por defecto; actívalo solo en tu entorno local.

**5. Aplica las migraciones**

```bash
python manage.py migrate
```

**6. Crea un superusuario** (opcional, para acceder al panel de administración)

```bash
python manage.py createsuperuser
```

Las cuentas se identifican por correo electrónico, no por nombre de usuario.

**7. Levanta el servidor de desarrollo**

```bash
python manage.py runserver
```

La aplicación queda disponible en <http://127.0.0.1:8000/>.

**8. Arranca el trabajador de tareas (HU-12)**

Procesar una página (detectar sus regiones de texto) corre en segundo plano con [Huey](https://huey.readthedocs.io/), sobre un archivo SQLite propio (`huey.sqlite3`); no hace falta Redis. En **otra terminal**, con el entorno virtual activado:

```bash
python manage.py run_huey
```

Sin el trabajador, las páginas se quedan en "Procesando" y a los cinco minutos se ofrece reintentar. Para una demostración rápida sin segunda terminal, pon `HUEY_IMMEDIATE=True` en `.env`: la detección corre dentro de la propia petición, pero deja de ser asíncrona.

## Detección de texto en desarrollo

El proveedor se elige con `OCR_PROVIDER` en `.env` (decisión en [ADR-001](docs/adr/ADR-001-proveedor-ocr-y-tareas-asincronas.md)):

| Valor | Qué hace |
|---|---|
| `fake` (por defecto) | Proveedor simulado: marca dos globos de ejemplo en cualquier página, sin red ni claves. Es el que usan las pruebas y la integración continua |
| `azure` | Azure AI Vision Read. Crea en el portal de Azure un recurso **Computer Vision** con el plan **Free F0** y copia su punto de conexión y su **KEY 1** en `AZURE_VISION_ENDPOINT` y `AZURE_VISION_KEY` |

La clave vive solo en `.env`; nunca en el código ni en Git.

### Imágenes de los usuarios

Las páginas, sus miniaturas y las portadas **no se sirven desde `/media/`**, ni siquiera en desarrollo. Se entregan por vistas protegidas (`/paginas/<id>/imagen/`, `/paginas/<id>/miniatura/`, `/albumes/<id>/portada/`) que exigen sesión y responden 404 a otras cuentas (HU-11, deuda DT-02).

Cada región guarda el texto reconocido y su confianza (HU-13). Las que tienen poca confianza (por debajo de `OCR_REVIEW_THRESHOLD`, 70 % provisional), no tienen texto o están en otro alfabeto que el idioma de origen se marcan "Revisar", y la página pasa a "Necesita revisión".

Para medir la precisión del OCR sobre un juego de páginas de prueba (CA-13.4), con una subcarpeta por idioma y un JSON con el texto esperado junto a cada imagen:

```bash
python manage.py ocr_accuracy_report ruta/al/juego-de-prueba --output informe-ocr.md
```

El formato de la carpeta está descrito al principio de `albums/management/commands/ocr_accuracy_report.py`.

## Maquetación y exportación PNG en desarrollo

El flujo completo de EP-08 (detectar, traducir, limpiar, maquetar y exportar en PNG) se puede probar sin red ni claves con los proveedores simulados. Decisiones en [ADR-003](docs/adr/ADR-003-edicion-de-imagen.md).

**1. Configura `.env`** con los valores por defecto de `.env.example`:

```bash
OCR_PROVIDER=fake
TRANSLATION_PROVIDER=fake
HUEY_IMMEDIATE=True
```

`HUEY_IMMEDIATE=True` ejecuta el procesamiento, la traducción, la limpieza y la exportación dentro de la propia petición. Si prefieres el comportamiento asíncrono real, déjalo en `False` y arranca `python manage.py run_huey` en otra terminal.

**2. Prepara una página.** Crea un álbum con idioma de origen japonés y carga una página. El OCR simulado marca dos globos de ejemplo en cualquier imagen; con una imagen de **fondo blanco** la limpieza los rellena sola, y con una ilustración cualquiera quedarán en «Limpieza manual», lo que también sirve para probar el aviso.

**3. Recorre el flujo en la vista de la página:**

1. **Procesar página** → aparecen las dos regiones.
2. **Traducir página** → el traductor simulado propone el texto de origen con el prefijo del idioma de destino (`[ES] こんにちは`). Como las fuentes de maquetación no tienen glifos japoneses, **edita cada traducción con un texto en español** (por ejemplo, «¡Hola!») y apruébala con **Aprobar**.
3. **Limpiar página** → se genera la capa limpia; compara las vistas «Original», «Limpia» y «Traducida».
4. Abre la pestaña **Maquetación** (`?paso=maquetacion`): selecciona un texto con clic o `Tab`, muévelo con el ratón o las flechas (`Mayús` para 10 px, `Alt` para cambiar el tamaño), cambia fuente, tamaño, alineación y color en el panel, prueba `Ctrl+Z` y **Restablecer**, y pulsa **Aprobar página**.
5. Vuelve al álbum: la página muestra «Maquetada».

**4. Exporta.** En **Revisión y exportación**, elige «Páginas traducidas (PNG en un ZIP)», confirma los avisos y descarga el ZIP. Cada `pagina-NNN.png` debe coincidir con lo que se ve en el editor.

Los procedimientos manuales de CP-89.2, CP-89.3, CP-89.6 y CP-89.8, con la tabla para registrar el resultado, están en [`docs/WIKI_SPRINT_3_CP_HU-89.md`](docs/WIKI_SPRINT_3_CP_HU-89.md).

## Recuperación de contraseña en desarrollo

PaneLingo no usa un proveedor de correo real: está fuera del alcance del MVP. En desarrollo, `EMAIL_BACKEND` es el backend de consola, así que **el mensaje de recuperación se imprime en la terminal donde corre `runserver`**, no se envía a ninguna parte.

Para ejecutar el caso de prueba de recuperación a mano:

1. Con el servidor levantado, ve a <http://127.0.0.1:8000/cuentas/recuperar/> y envía el correo de una cuenta registrada.
2. Vuelve a la terminal del `runserver`. Verás algo así:

```
Content-Type: text/plain; charset="utf-8"
Subject: PaneLingo: enlace para restablecer tu contraseña
From: PaneLingo <no-responder@panelingo.local>
To: mira@estudio.test

Hola, Mira Okonkwo:

Recibimos una solicitud para restablecer la contraseña de tu cuenta de
PaneLingo (mira@estudio.test).

Abre este enlace para elegir una contraseña nueva:

http://127.0.0.1:8000/cuentas/recuperar/MQ/dee5tm-00a74134bc7fcf290dac307ac82f8eca/

El enlace caduca en una hora y solo sirve una vez. Al usarlo se cerrarán las
demás sesiones abiertas de tu cuenta.
```

3. Copia esa dirección completa en el navegador y elige la contraseña nueva.

Dos detalles al leer la consola:

- El mensaje sale **dos veces**, en texto plano y en HTML. El enlace es el mismo; toma el de la primera parte, que se lee mejor.
- El enlace **caduca en una hora y solo sirve una vez**. Si lo reutilizas o tardas, la pantalla dirá que ya no sirve y tendrás que solicitar otro. Es intencionado, no un fallo.

Si envías un correo que no corresponde a ninguna cuenta, la aplicación mostrará la misma pantalla de confirmación pero **no aparecerá nada en la consola**: la respuesta visible no revela si la cuenta existe.

## Comandos de calidad

El **Quality Gate** debe ejecutarse completo al final de cada etapa. Los siete pasos, en este orden:

```bash
ruff check . --fix          # 1. Correcciones seguras (incluye orden de imports)
black .                     # 2. Formato definitivo
ruff check .                # 3. Verificación de análisis estático
black --check .             # 4. Verificación de formato
python manage.py check      # 5. Comprobaciones del sistema Django
python manage.py test       # 6. Pruebas automáticas
pip-audit -r requirements.txt   # 7. Auditoría de vulnerabilidades
```

El orden importa: Ruff aplica primero sus correcciones seguras, Black da el formato final, y los pasos 3 y 4 verifican que ninguna de las dos herramientas deshaga el trabajo de la otra.

Para no copiar las salidas a mano, `./scripts/quality_gate.sh <NN>` ejecuta los siete pasos y guarda la evidencia de la etapa `<NN>` en `docs/evidence/sprint-1/etapa-<NN>/`, junto con un resumen en Markdown listo para la wiki. Si una etapa se reparte en varias ramas, admite un sufijo de una letra (`08`, `08b`):

```bash
./scripts/quality_gate.sh 01
```

El sprint se elige con la variable `SPRINT` (1 por defecto); por ejemplo, `SPRINT=3 ./scripts/quality_gate.sh 90b` guarda la evidencia en `docs/evidence/sprint-3/etapa-90b/`.

Ejecuta los siete pasos aunque alguno falle y termina con código distinto de cero si hubo alguno en rojo. No hace commit ni push. La convención de nombres está documentada en [`docs/evidence/sprint-1/README.md`](docs/evidence/sprint-1/README.md).

La configuración vive en `pyproject.toml`: `line-length = 88`, reglas `["E", "F", "N", "B", "I", "C90"]` y complejidad ciclomática máxima de 10. **No desactives reglas globalmente.** Si `E501` marca una línea que Black no puede partir, reescríbela o usa un `noqa` puntual con su comentario justificativo.

Estos mismos pasos se ejecutan automáticamente en GitHub Actions (`.github/workflows/quality.yml`) en cada push y pull request hacia `main`.

## Convención de ramas y commits

Seguimos **GitHub Flow**. `main` siempre contiene código estable y nunca se trabaja directamente sobre ella.

| Tipo | Formato | Ejemplo |
|---|---|---|
| Historia de usuario | `feature/HU-XX-descripcion-en-ingles` | `feature/HU-05-album-creation` |
| Corrección de error | `fix/BUG-XXX-descripcion` | `fix/BUG-014-upload-size-limit` |
| Documentación | `docs/tema` | `docs/design-tokens` |
| Configuración | `chore/tema` | `chore/project-bootstrap` |

Los commits siguen **Conventional Commits** e incluyen el identificador de la historia de usuario:

```
feat(albums): HU-05 add album creation form
test(accounts): HU-01 add CP-01.1 and CP-01.2 cases
fix(uploads): BUG-014 reject files over the size limit
```

Cada historia de usuario se integra a `main` mediante pull request, nunca por merge directo.

## Estructura del proyecto

```
panelingo/
├── .github/workflows/   Integración continua (Quality Gate)
├── accounts/            Autenticación y modelo de usuario
├── albums/              Álbumes y páginas
├── config/              Configuración del proyecto Django
├── design/              Mockup aprobado y tokens de diseño
├── media/               Imágenes cargadas por los usuarios (no versionadas)
├── static/              CSS, JavaScript e imágenes de la aplicación
├── templates/           Plantillas Django compartidas
└── manage.py
```

## Diseño

La referencia visual obligatoria es el mockup de alta fidelidad `design/PaneLingo.dc.html`, aprobado por el Product Owner. Los colores, tipografías, radios y espaciados están extraídos y documentados en **[`design/DESIGN_TOKENS.md`](design/DESIGN_TOKENS.md)**, que es la fuente de verdad visual del proyecto.

Las capturas del mockup renderizado están en `design/screenshots/` y son la mejor referencia visual: consúltalas antes de maquetar cada pantalla. Las de `design/screenshots/fuera-de-alcance/` son contexto del producto completo y no se construyen en el Sprint 1.

La interfaz se redacta en español. El mockup está en inglés: se toma de él la composición y la jerarquía, no los textos.

### Página de referencia de estilos

Con el servidor de desarrollo levantado, <http://127.0.0.1:8000/design-system/> reúne todos los componentes y sus estados en una sola página, para compararlos con las capturas.

**Es una página de desarrollo, no forma parte del producto.** Solo responde cuando `DJANGO_DEBUG=True`; con `DEBUG` desactivado devuelve 404, de modo que nunca queda expuesta en producción.

Requisito no funcional: la aplicación cumple **WCAG 2.1 nivel AA**. Las desviaciones deliberadas respecto al mockup están documentadas en `DESIGN_TOKENS.md`.

## Fuera del alcance actual

Estas funcionalidades **no están implementadas** y no deben esperarse:

| Fuera de alcance | Motivo |
|---|---|
| Terminología y glosario | Sin historia de usuario. La entrada «Terminología» de la barra lateral se muestra deshabilitada |
| Limpieza con IA del texto que está sobre el dibujo | HU-91 se descartó tras su *spike* ([ADR-003, P4](docs/adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91)). Las regiones que la limpieza no resuelve quedan en «Limpieza manual» y se avisan |
| Cambiar a mano el tipo globo/narración de una región | Propuesta pendiente del PO ([ADR-003, P10](docs/adr/ADR-003-edicion-de-imagen.md)) |
| Reordenar o insertar páginas | Sin historia de usuario |
| Colaboración en equipo y SSO | Fuera del MVP |
| Pagos, créditos y planes | Fuera del MVP |
| Pantalla de perfil y preferencias | Fuera del MVP |
| Panel administrativo completo | Fuera del MVP. Solo existe el admin de Django |
| **Envío real de correo** | En desarrollo va a la consola. Ver la sección de recuperación |

Lo que el Sprint 1 dejó fuera y llegó después con su historia: detección y OCR (HU-12, HU-13), workspace y traducción con IA (HU-14 a HU-19), eliminar álbumes (HU-20), filtros por estado (HU-26), revisión y exportación (HU-27, HU-28) y edición de imagen (HU-85 a HU-90).

Las páginas cargadas quedan en estado **Pendiente de procesamiento** hasta que se pulsa "Procesar página" en su vista (HU-12).

## Documentación

La documentación completa del proyecto —visión de producto, arquitectura, historias de usuario, criterios de aceptación y casos de prueba— vive en la wiki del repositorio:

**[Wiki del proyecto PaneLingo](../../wiki)**

Las reglas permanentes que sigue el equipo al escribir código están en [`CLAUDE.md`](CLAUDE.md).

Documentos de cierre del Sprint 1:

- **[`docs/TRACEABILITY.md`](docs/TRACEABILITY.md)** — matriz HU → CA → CP → prueba automática → evidencia.
- **[`docs/WIKI_SPRINT_1_DESARROLLO.md`](docs/WIKI_SPRINT_1_DESARROLLO.md)** — borrador para la wiki, con decisiones técnicas, deudas y propuestas abiertas.
- **`docs/evidence/sprint-1/`** — salida del Quality Gate de las 14 etapas.
