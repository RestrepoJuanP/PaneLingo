# Quality Gate — Etapa 05

| Campo | Valor |
|---|---|
| Fecha y hora | `2026-09-04T16:56:59-05:00` |
| Rama | `feature/HU-03-logout` |
| Commit | `f0c2ddae55c2204186f65cdeec0e84b63832f283` |
| Arbol de trabajo | con cambios sin versionar |
| Resultado global | **PASA (7/7)** (verde) |

## Pasos

| # | Paso | Comando | Codigo de salida | Resultado |
|---|---|---|---|---|
| 1 | Ruff — correcciones seguras | `ruff check . --fix` | 0 | verde |
| 2 | Black — formato | `black .` | 0 | verde |
| 3 | Ruff — verificacion de analisis estatico | `ruff check .` | 0 | verde |
| 4 | Black — verificacion de formato | `black --check .` | 0 | verde |
| 5 | Django — comprobaciones del sistema | `python manage.py check` | 0 | verde |
| 6 | Django — pruebas automaticas | `python manage.py test` | 0 | verde |
| 7 | pip-audit — auditoria de dependencias | `pip-audit -r requirements.txt` | 0 | verde |

## Archivos de evidencia

- `E05-quality-gate-01-ruff-fix.txt`
- `E05-quality-gate-02-black.txt`
- `E05-quality-gate-03-ruff-check.txt`
- `E05-quality-gate-04-black-check.txt`
- `E05-quality-gate-05-django-check.txt`
- `E05-quality-gate-06-django-test.txt`
- `E05-quality-gate-07-pip-audit.txt`

Generado por `scripts/quality_gate.sh 05`.
