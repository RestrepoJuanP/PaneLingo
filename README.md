# PaneLingo

Plataforma web para la **traducción asistida de cómics, manga y webtoons**. PaneLingo permite a un traductor organizar su trabajo en álbumes, cargar las páginas completas de cada obra y gestionarlas desde un espacio propio y privado.

Proyecto académico desarrollado para **Proyecto Integrador 2**. El alcance del Sprint 1 cubre autenticación de usuarios y gestión de álbumes y páginas. El OCR, la traducción con IA, el workspace de traducción y la exportación quedan fuera de este sprint.

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

Para no copiar las salidas a mano, `./scripts/quality_gate.sh <NN>` ejecuta los siete pasos y guarda la evidencia de la etapa `<NN>` en `docs/evidence/sprint-1/etapa-<NN>/`, junto con un resumen en Markdown listo para la wiki:

```bash
./scripts/quality_gate.sh 01
```

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

La interfaz se redacta en español. El mockup está en inglés: se toma de él la composición y la jerarquía, no los textos.

Requisito no funcional: la aplicación cumple **WCAG 2.1 nivel AA**. Las desviaciones deliberadas respecto al mockup están documentadas en `DESIGN_TOKENS.md`.

## Documentación

La documentación completa del proyecto —visión de producto, arquitectura, historias de usuario, criterios de aceptación y casos de prueba— vive en la wiki del repositorio:

**[Wiki del proyecto PaneLingo](../../wiki)**

Las reglas permanentes que sigue el equipo al escribir código están en [`CLAUDE.md`](CLAUDE.md).
