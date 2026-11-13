"""Comprobación de salud del contenedor web de PaneLingo.

Pide la pantalla de inicio de sesión a Gunicorn dentro del contenedor, con la
cabecera Host del primer host permitido: Django rechaza con 400 cualquier
host que no esté en DJANGO_ALLOWED_HOSTS. Sale con 0 si responde 200.
"""

import os
import sys
import urllib.request

HOST = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost").split(",")[0].strip()
REQUEST = urllib.request.Request(
    "http://127.0.0.1:8000/cuentas/ingresar/",
    headers={"Host": HOST, "X-Forwarded-Proto": "https"},
)

try:
    with urllib.request.urlopen(REQUEST, timeout=5) as response:
        sys.exit(0 if response.status == 200 else 1)
except OSError:
    sys.exit(1)
