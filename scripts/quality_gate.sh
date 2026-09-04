#!/usr/bin/env bash
#
# PaneLingo — Captura de evidencias del Quality Gate.
#
# Ejecuta los siete pasos del Quality Gate definidos en CLAUDE.md y guarda la
# salida de cada uno en docs/evidence/sprint-1/etapa-<NN>/, junto con un
# resumen en Markdown listo para pegar en la wiki del proyecto.
#
# Uso:
#   ./scripts/quality_gate.sh <NN[x]>
#
# Ejemplo:
#   ./scripts/quality_gate.sh 01
#   ./scripts/quality_gate.sh 08b   (etapa repartida en varias ramas)
#
# El script NO hace commit ni push: solo genera archivos. Versionarlos es una
# decision manual.
#
# NOTA IMPORTANTE SOBRE EL MODO ESTRICTO
# --------------------------------------
# Este script NO usa `set -e` ni `set -euo pipefail` de forma global, y no es
# un descuido: es un requisito. El objetivo de la captura de evidencias es
# registrar el resultado de LOS SIETE pasos, incluidos los que fallan. Con
# `set -e` el script abortaria en el primer paso rojo y la evidencia quedaria
# incompleta, que es justo lo contrario de lo que se necesita.
# El codigo de salida de cada paso se captura de forma explicita y el script
# termina con codigo distinto de cero si alguno fallo.

# --- Validacion del argumento ----------------------------------------------

usage() {
    cat <<'USAGE'
Uso: ./scripts/quality_gate.sh <NN[x]>

  <NN>  Numero de etapa en dos digitos (01 a 99).
  [x]   Letra minuscula opcional, para una etapa dividida en varias ramas.

Ejemplos:
  ./scripts/quality_gate.sh 01
  ./scripts/quality_gate.sh 08
  ./scripts/quality_gate.sh 08b

Genera docs/evidence/sprint-1/etapa-<NN>/ con la salida de los siete pasos
del Quality Gate y un resumen en Markdown.
USAGE
}

if [ "$#" -lt 1 ]; then
    echo "ERROR: falta el numero de etapa." >&2
    echo >&2
    usage >&2
    exit 2
fi

if [ "$#" -gt 1 ]; then
    echo "ERROR: se esperaba un unico argumento, se recibieron $#." >&2
    echo >&2
    usage >&2
    exit 2
fi

STAGE="$1"

if [ "$STAGE" = "-h" ] || [ "$STAGE" = "--help" ]; then
    usage
    exit 0
fi

# Dos digitos, con una letra minuscula opcional para las etapas que se
# reparten en varias ramas, como 08 y 08b cuando una etapa cubre dos
# historias de usuario y la wiki exige una rama por historia.
if ! [[ "$STAGE" =~ ^[0-9]{2}[a-z]?$ ]]; then
    echo "ERROR: '$STAGE' no tiene el formato esperado (01, 08 o 08b)." >&2
    echo >&2
    usage >&2
    exit 2
fi

# --- Contexto de ejecucion --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || {
    echo "ERROR: no se pudo acceder a la raiz del repositorio." >&2
    exit 2
}

# Antepone el entorno virtual al PATH para que los comandos registrados en la
# evidencia sean exactamente los de CLAUDE.md y no rutas absolutas. En CI no
# hay .venv y se usan las herramientas ya instaladas en el entorno.
if [ -d "$REPO_ROOT/.venv/Scripts" ]; then
    PATH="$REPO_ROOT/.venv/Scripts:$PATH"
elif [ -d "$REPO_ROOT/.venv/bin" ]; then
    PATH="$REPO_ROOT/.venv/bin:$PATH"
fi
export PATH

# Fuerza salida UTF-8 en los procesos Python. Sin esto, al redirigir a un
# archivo en Windows la consola usa cp1252 y los acentos y rayas de los
# docstrings de las pruebas quedan como mojibake en la evidencia.
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

OUTPUT_DIR="docs/evidence/sprint-1/etapa-${STAGE}"
mkdir -p "$OUTPUT_DIR" || {
    echo "ERROR: no se pudo crear $OUTPUT_DIR." >&2
    exit 2
}

TIMESTAMP="$(date -Is 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'desconocida')"
COMMIT="$(git rev-parse HEAD 2>/dev/null || echo 'desconocido')"

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    TREE_STATE="con cambios sin versionar"
else
    TREE_STATE="limpio"
fi

# --- Definicion de los siete pasos ------------------------------------------
# El orden es el fijado en CLAUDE.md y no debe alterarse: Ruff aplica primero
# sus correcciones seguras, Black da el formato definitivo, y los pasos 3 y 4
# verifican que ninguna de las dos herramientas deshaga el trabajo de la otra.

STEP_SLUGS=(
    "01-ruff-fix"
    "02-black"
    "03-ruff-check"
    "04-black-check"
    "05-django-check"
    "06-django-test"
    "07-pip-audit"
)

STEP_COMMANDS=(
    "ruff check . --fix"
    "black ."
    "ruff check ."
    "black --check ."
    "python manage.py check"
    "python manage.py test"
    "pip-audit -r requirements.txt"
)

STEP_LABELS=(
    "Ruff — correcciones seguras"
    "Black — formato"
    "Ruff — verificacion de analisis estatico"
    "Black — verificacion de formato"
    "Django — comprobaciones del sistema"
    "Django — pruebas automaticas"
    "pip-audit — auditoria de dependencias"
)

STEP_TOOLS=(
    "ruff"
    "black"
    "ruff"
    "black"
    "django"
    "django"
    "pip-audit"
)

tool_version() {
    # Devuelve la version de la herramienta usada en un paso.
    case "$1" in
        ruff)
            ruff --version 2>&1 | head -1
            ;;
        black)
            black --version 2>&1 | head -1
            ;;
        django)
            printf '%s / Django %s' \
                "$(python --version 2>&1)" \
                "$(python -c 'import django; print(django.get_version())' 2>&1)"
            ;;
        pip-audit)
            pip-audit --version 2>&1 | head -1
            ;;
        *)
            echo "desconocida"
            ;;
    esac
}

# --- Ejecucion --------------------------------------------------------------

TOTAL="${#STEP_SLUGS[@]}"
EXIT_CODES=()
FAILED=0

echo "=============================================================="
echo " PaneLingo — Quality Gate — Etapa ${STAGE}"
echo "=============================================================="
echo " Rama    : ${BRANCH}"
echo " Commit  : ${COMMIT}"
echo " Arbol   : ${TREE_STATE}"
echo " Destino : ${OUTPUT_DIR}/"
echo "=============================================================="
echo

for index in "${!STEP_SLUGS[@]}"; do
    number=$((index + 1))
    slug="${STEP_SLUGS[$index]}"
    command_line="${STEP_COMMANDS[$index]}"
    label="${STEP_LABELS[$index]}"
    version="$(tool_version "${STEP_TOOLS[$index]}")"
    file="${OUTPUT_DIR}/E${STAGE}-quality-gate-${slug}.txt"

    printf '[%d/%d] %-42s ' "$number" "$TOTAL" "$command_line"

    {
        echo "=============================================================================="
        echo "PaneLingo — Evidencia del Quality Gate"
        echo "=============================================================================="
        printf 'Etapa           : %s\n' "$STAGE"
        printf 'Paso            : %d de %d — %s\n' "$number" "$TOTAL" "$label"
        printf 'Comando         : %s\n' "$command_line"
        printf 'Herramienta     : %s\n' "$version"
        printf 'Fecha y hora    : %s\n' "$TIMESTAMP"
        printf 'Rama            : %s\n' "$BRANCH"
        printf 'Commit          : %s\n' "$COMMIT"
        printf 'Arbol de trabajo: %s\n' "$TREE_STATE"
        printf 'Directorio      : %s\n' "$REPO_ROOT"
        echo "=============================================================================="
        echo
    } >"$file"

    # Se captura stdout y stderr juntos. El fallo de un paso NO interrumpe el
    # bucle: se registra su codigo de salida y se continua con el siguiente.
    eval "$command_line" >>"$file" 2>&1
    code=$?

    EXIT_CODES+=("$code")
    if [ "$code" -ne 0 ]; then
        FAILED=1
        result="FALLO"
    else
        result="CORRECTO"
    fi

    {
        echo
        echo "=============================================================================="
        printf 'Codigo de salida: %d  (%s)\n' "$code" "$result"
        echo "=============================================================================="
    } >>"$file"

    if [ "$code" -eq 0 ]; then
        echo "OK   (exit 0)"
    else
        echo "FALLO (exit ${code})"
    fi
done

# --- Resumen en Markdown ----------------------------------------------------

SUMMARY_FILE="${OUTPUT_DIR}/E${STAGE}-quality-gate-RESUMEN.md"

if [ "$FAILED" -eq 0 ]; then
    GLOBAL_RESULT="PASA (${TOTAL}/${TOTAL})"
    GLOBAL_MARK="verde"
else
    passed=0
    for code in "${EXIT_CODES[@]}"; do
        [ "$code" -eq 0 ] && passed=$((passed + 1))
    done
    GLOBAL_RESULT="FALLA (${passed}/${TOTAL} en verde)"
    GLOBAL_MARK="rojo"
fi

{
    echo "# Quality Gate — Etapa ${STAGE}"
    echo
    echo "| Campo | Valor |"
    echo "|---|---|"
    echo "| Fecha y hora | \`${TIMESTAMP}\` |"
    echo "| Rama | \`${BRANCH}\` |"
    echo "| Commit | \`${COMMIT}\` |"
    echo "| Arbol de trabajo | ${TREE_STATE} |"
    echo "| Resultado global | **${GLOBAL_RESULT}** (${GLOBAL_MARK}) |"
    echo
    echo "## Pasos"
    echo
    echo "| # | Paso | Comando | Codigo de salida | Resultado |"
    echo "|---|---|---|---|---|"

    for index in "${!STEP_SLUGS[@]}"; do
        number=$((index + 1))
        code="${EXIT_CODES[$index]}"
        if [ "$code" -eq 0 ]; then
            mark="verde"
        else
            mark="rojo"
        fi
        printf '| %d | %s | `%s` | %d | %s |\n' \
            "$number" \
            "${STEP_LABELS[$index]}" \
            "${STEP_COMMANDS[$index]}" \
            "$code" \
            "$mark"
    done

    echo
    echo "## Archivos de evidencia"
    echo
    for index in "${!STEP_SLUGS[@]}"; do
        printf -- '- `E%s-quality-gate-%s.txt`\n' "$STAGE" "${STEP_SLUGS[$index]}"
    done
    echo
    echo "Generado por \`scripts/quality_gate.sh ${STAGE}\`."
} >"$SUMMARY_FILE"

# --- Resumen en consola -----------------------------------------------------

echo
echo "=============================================================="
echo " RESUMEN — Etapa ${STAGE}"
echo "=============================================================="
for index in "${!STEP_SLUGS[@]}"; do
    number=$((index + 1))
    code="${EXIT_CODES[$index]}"
    if [ "$code" -eq 0 ]; then
        mark="verde"
    else
        mark="rojo "
    fi
    printf ' %d/%d  %s  exit %-3d  %s\n' \
        "$number" "$TOTAL" "$mark" "$code" "${STEP_COMMANDS[$index]}"
done
echo "=============================================================="
echo " Resultado global : ${GLOBAL_RESULT}"
echo " Evidencias       : ${OUTPUT_DIR}/"
echo " Resumen wiki     : ${SUMMARY_FILE}"
echo "=============================================================="

if [ "$FAILED" -ne 0 ]; then
    echo
    echo "Hay pasos en rojo. Revisa los archivos de evidencia antes de dar la"
    echo "etapa por terminada."
    exit 1
fi

exit 0
