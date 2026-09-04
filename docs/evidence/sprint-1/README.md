# Evidencias del Sprint 1

Esta carpeta guarda la evidencia reproducible de la asignatura de **Calidad del Software** para las doce etapas del Sprint 1 de PaneLingo.

Las evidencias no se copian a mano. Se generan con el script del repositorio, de forma que la salida sea idéntica y trazable en todas las etapas:

```bash
./scripts/quality_gate.sh <NN>
```

El script ejecuta los siete pasos del Quality Gate definidos en [`CLAUDE.md`](../../../CLAUDE.md), guarda la salida completa de cada uno y produce un resumen en Markdown listo para pegar en la wiki. **No hace commit ni push:** versionar los archivos generados es una decisión manual.

## Estructura

```
docs/evidence/sprint-1/
├── README.md                 Este archivo
├── etapa-01/
├── etapa-02/
└── ...                       Una carpeta por etapa, hasta etapa-12/
```

## Qué contiene cada carpeta de etapa

Una carpeta `etapa-<NN>/` contiene nueve o más archivos:

| Archivo | Origen | Contenido |
|---|---|---|
| `E<NN>-quality-gate-01-ruff-fix.txt` | script | Salida de `ruff check . --fix` |
| `E<NN>-quality-gate-02-black.txt` | script | Salida de `black .` |
| `E<NN>-quality-gate-03-ruff-check.txt` | script | Salida de `ruff check .` |
| `E<NN>-quality-gate-04-black-check.txt` | script | Salida de `black --check .` |
| `E<NN>-quality-gate-05-django-check.txt` | script | Salida de `python manage.py check` |
| `E<NN>-quality-gate-06-django-test.txt` | script | Salida de `python manage.py test` |
| `E<NN>-quality-gate-07-pip-audit.txt` | script | Salida de `pip-audit -r requirements.txt` |
| `E<NN>-quality-gate-RESUMEN.md` | script | Tabla de resultados; **este es el que se pega en la wiki** |
| `E<NN>-ci-action-verde.png` | manual | Captura del workflow de CI en verde |
| `E<NN>-pr-aprobado.png` | manual | Captura del pull request aprobado |

## Convención de nombres

Todo archivo empieza por `E<NN>`, donde `<NN>` es el número de etapa en **dos dígitos** (`01`, `02`, … `12`). El prefijo permite ordenar y localizar la evidencia sin ambigüedad cuando se adjunta a la wiki, fuera de su carpeta.

Los archivos del Quality Gate llevan además el número de paso en dos dígitos y un nombre corto: `01-ruff-fix`, `02-black`, `03-ruff-check`, `04-black-check`, `05-django-check`, `06-django-test`, `07-pip-audit`. El número de paso corresponde al orden fijado en `CLAUDE.md` y no debe alterarse.

### Capturas de pantalla

Las capturas se toman a mano y se nombran exactamente así:

| Archivo | Qué debe mostrar |
|---|---|
| `E<NN>-ci-action-verde.png` | La ejecución del workflow en GitHub Actions con los siete pasos en verde, para el pull request de esa etapa |
| `E<NN>-pr-aprobado.png` | El pull request de esa etapa con la revisión aprobada y el check requerido en verde |
| `E00-ruleset-main.png` | La configuración del ruleset de la rama `main`. Es única para todo el sprint, por eso usa el prefijo `E00` y vive en la raíz de esta carpeta, no dentro de una etapa |

## Cabecera de los archivos de evidencia

Cada archivo `.txt` empieza por un bloque de cabecera que hace la evidencia verificable:

```
==============================================================================
PaneLingo — Evidencia del Quality Gate
==============================================================================
Etapa           : 01
Paso            : 3 de 7 — Ruff — verificacion de analisis estatico
Comando         : ruff check .
Herramienta     : ruff 0.16.6
Fecha y hora    : 2026-09-03T21:30:00-05:00
Rama            : chore/project-bootstrap
Commit          : e33c7212439cbcd988dbd2ff7d7228c37a652c8c
Arbol de trabajo: limpio
Directorio      : /f/PaneLingo
==============================================================================
```

El campo **Árbol de trabajo** indica si había cambios sin versionar al generar la evidencia. Una evidencia tomada sobre un árbol `limpio` corresponde exactamente al commit indicado; una tomada `con cambios sin versionar` no es reproducible a partir de ese hash. Para la entrega, genera siempre la evidencia con el árbol limpio.

Al final de cada archivo se registra el código de salida del paso.

## Comportamiento ante fallos

El script **no se detiene en el primer paso rojo**: ejecuta los siete y registra el código de salida de cada uno. Esto es deliberado, porque una evidencia truncada en el primer fallo no sirve para diagnosticar. El script termina con código de salida distinto de cero si algún paso falló, de modo que sigue siendo utilizable en automatizaciones.

## Integración continua: nombre del status check

El workflow se llama **`Quality Gate`** y su único job se llama, textualmente:

```
Analisis estatico, pruebas y auditoria
```

**Ese es el nombre exacto que debe registrarse como status check requerido en el ruleset de la rama `main`.**

GitHub identifica los checks requeridos por el **nombre del job**, no por el del workflow ni por la clave del job en el YAML. El nombre corto `quality` —que es la clave del job dentro de `jobs:` en `.github/workflows/quality.yml`— **no funciona**: GitHub se queda esperando indefinidamente un check que nunca se reporta con ese nombre, y el merge del pull request permanece bloqueado sin ningún error visible que explique por qué.

Si en algún momento se renombra el job en el workflow, hay que actualizar el ruleset en el mismo cambio, o todos los pull requests quedarán bloqueados.
