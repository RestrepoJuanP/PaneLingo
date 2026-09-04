"""Configuración de Django para el proyecto PaneLingo.

Los valores sensibles y los que cambian entre entornos se leen de variables de
entorno mediante python-dotenv. Nunca se escriben secretos en este archivo.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def get_env_bool(name: str, default: bool = False) -> bool:
    """Lee una variable de entorno y la interpreta como booleano."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_env_list(name: str, default: str = "") -> list[str]:
    """Lee una variable de entorno separada por comas y la devuelve como lista."""
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


# --- Seguridad -------------------------------------------------------------

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Falta la variable de entorno DJANGO_SECRET_KEY. "
        "Copia .env.example a .env y genera una clave."
    )

DEBUG = get_env_bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = get_env_list("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1")


# --- Aplicaciones ----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "albums",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --- Base de datos ---------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --- Autenticación ---------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

# Prefijo del módulo de validadores de contraseña de Django. Se extrae a una
# constante porque las rutas completas superan el límite de 88 caracteres y
# Black no puede partir una cadena literal.
_PASSWORD_VALIDATION = "django.contrib.auth.password_validation"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"{_PASSWORD_VALIDATION}.UserAttributeSimilarityValidator"},
    {"NAME": f"{_PASSWORD_VALIDATION}.MinimumLengthValidator"},
    {"NAME": f"{_PASSWORD_VALIDATION}.CommonPasswordValidator"},
    {"NAME": f"{_PASSWORD_VALIDATION}.NumericPasswordValidator"},
]

LOGIN_URL = "/cuentas/ingresar/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/cuentas/ingresar/"


# --- Correo ----------------------------------------------------------------

# La recuperación de contraseña del MVP no usa un proveedor de correo real:
# los mensajes se imprimen en la consola del servidor de desarrollo.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "PaneLingo <no-responder@panelingo.local>"


# --- Internacionalización --------------------------------------------------

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos y de medios ----------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Constantes del proyecto -----------------------------------------------

# Tamaño máximo aceptado por página cargada, en bytes (10 MB).
MAX_FILE_SIZE = 10_000_000

# Extensiones de imagen admitidas al cargar una página de un álbum.
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
