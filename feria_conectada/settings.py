"""
Configuración Django para el proyecto Feria Conectada
Cumple con OWASP, DevSecOps y DDD.
"""

from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url

# ----------------------------------
# A. BASE_DIR y carga de .env
# ----------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ----------------------------------
# Configuración básica
# ----------------------------------
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-2s0_91-*8idoq#hzpl4o9!x5#%8t0v$q=lrg6dm(fhvw01qrnw"  # TODO: Cambiar en producción
)
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Soporta múltiples hosts separados por coma
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]

# ----------------------------------
# Aplicaciones instaladas
# ----------------------------------
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "djoser",
    "corsheaders",
    "drf_spectacular",  # <- añade soporte OpenAPI 3.0

    # Apps locales (Dominios DDD)
    "core",
    "users",
    "market",
    "orders",
    "delivery",
]

# ----------------------------------
# Middleware
# ----------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # debe ir arriba
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ----------------------------------
# Rutas, plantillas y WSGI
# ----------------------------------
ROOT_URLCONF = "feria_conectada.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "feria_conectada.wsgi.application"

# ----------------------------------
# B. Base de Datos (dj_database_url + PostgreSQL)
# ----------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}

# ----------------------------------
# Validación de contraseñas
# ----------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------
# C. Usuario personalizado
# ----------------------------------
AUTH_USER_MODEL = "users.User"

# ----------------------------------
# D. Django REST Framework + JWT (CORRECCIÓN APLICADA AQUÍ)
# ----------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        # IMPORTANTE: Se fuerza a ser una tupla de 1 elemento usando la coma (,)
        ("rest_framework.permissions.AllowAny",)
        if DEBUG
        else ("rest_framework.permissions.IsAuthenticated",)
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    # Para OpenAPI
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

DJOSER = {
    "USER_ID_FIELD": "id",
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": False,
    "SERIALIZERS": {},  # se personalizará luego
    "PERMISSIONS": {
        "user_list": ["rest_framework.permissions.IsAdminUser"],
        "user": ["rest_framework.permissions.IsAuthenticated"],
    },
}

# ----------------------------------
# Internacionalización (Chile)
# ----------------------------------
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ----------------------------------
# Archivos estáticos y media
# ----------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ----------------------------------
# Configuración por defecto de clave primaria
# ----------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------
# Configuración de CORS
# ----------------------------------
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:19006"
).split(",")]

CORS_ALLOW_CREDENTIALS = True

# ----------------------------------
# Configuración de correo (placeholder)
# ----------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = "Feria Conectada <no-reply@feriaconectada.com>"

# ----------------------------------
# Logging estructurado (base)
# ----------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} [{name}] {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}