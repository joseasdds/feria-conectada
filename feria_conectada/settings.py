"""
Configuración Django para el proyecto Feria Conectada
Cumple con OWASP, DevSecOps y DDD.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# ----------------------------------
# A. BASE_DIR y carga de .env
# ----------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ----------------------------------
# Configuración básica
# ----------------------------------
# DevSecOps: DEBUG gestionado por variable de entorno
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# OWASP: Asegurar que SECRET_KEY no esté hardcodeado en producción
SECRET_KEY = os.getenv("SECRET_KEY")

# **<-- CORRECCIÓN DE SEGURIDAD AQUÍ -->**
# Si no estamos en DEBUG y SECRET_KEY no está definido, lanzamos error.
if not DEBUG and not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY must be set in the production environment (DEBUG=False)."
    )

# Usar un valor dummy si estamos en desarrollo y no se ha definido (OPCIONAL)
if DEBUG and not SECRET_KEY:
    print("WARNING: Using Django's insecure default SECRET_KEY for development.")
    SECRET_KEY = "django-insecure-2s0_91-*8idoq#hzpl4o9!x5#%8t0v$q=lrg6dm(fhvw01qrnw"

# --- BLOQUE ALLOWED_HOSTS CORREGIDO Y SEGURO ---
# OWASP: Protección contra ataques Host header
# Lee DJANGO_ALLOWED_HOSTS como lista separada por comas.
# Ejemplo: "example.com,api.example.com"
_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
if _hosts:
    ALLOWED_HOSTS = [h.strip() for h in _hosts.split(",") if h.strip()]
else:
    # keep safe defaults for local dev
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
# --- FIN BLOQUE ALLOWED_HOSTS CORREGIDO Y SEGURO ---

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
    "django_filters",
    "django_extensions",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "djoser",
    "corsheaders",
    "drf_spectacular",
    # Apps locales (Dominios DDD)
    "core",
    "users.apps.UsersConfig",
    "market",
    "orders",
    "delivery",
]

# ----------------------------------
# Middleware
# ----------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
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
# DevSecOps: Uso de DATABASE_URL para configuración segura
# IMPORTANTE: Se lee de os.getenv('DATABASE_URL')
# ----------------------------------
DATABASES = {
    "default": dj_database_url.config(
        # Lee de la variable de entorno DATABASE_URL
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ----------------------------------
# Validación de contraseñas (OWASP: Prácticas seguras para contraseñas)
# ----------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        )
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------
# C. Usuario personalizado (DDD: Dominio de Usuarios)
# ----------------------------------
AUTH_USER_MODEL = "users.User"

# ----------------------------------
# D. Django REST Framework + JWT
# ----------------------------------
REST_FRAMEWORK = {
    # JWT como autenticación principal
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Permisos por defecto (OWASP: Principio del Mínimo Privilegio)
    "DEFAULT_PERMISSION_CLASSES": [
        (
            "rest_framework.permissions.AllowAny"
            if DEBUG
            else "rest_framework.permissions.IsAuthenticated"
        ),
    ],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    # Documentación OpenAPI (Criterio FASE 0)
    "DEFAULT_SCHEMA_CLASS": ("drf_spectacular.openapi.AutoSchema"),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

SIMPLE_JWT = {
    # Tiempo de vida de tokens (Seguridad)
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- BLOQUE DJOSER MODIFICADO ---
DJOSER = {
    "USER_ID_FIELD": "id",
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": False,
    # CONFIGURACIÓN CLAVE DE LA FASE 1: Apuntar a tus Serializers
    "SERIALIZERS": {
        "user_create": "users.serializers.RegistrationSerializer",
        "user": "users.serializers.UserSerializer",
        "current_user": "users.serializers.UserSerializer",
        # Añadido: Se requiere para el endpoint /api/v1/me/
    },
    "PERMISSIONS": {
        "user_list": ["rest_framework.permissions.IsAdminUser"],
        "user": ["rest_framework.permissions.IsAuthenticated"],
    },
}
# --- FIN BLOQUE DJOSER MODIFICADO ---

# ----------------------------------
# E. DRF Spectacular (Documentación OpenAPI - Criterio FASE 0)
# ----------------------------------
APP_VERSION_TAG = "v0.2-UsersProfiles"

SPECTACULAR_SETTINGS = {
    "TITLE": "Feria Conectada API",
    "DESCRIPTION": (
        "Documentación de la API para la plataforma de comercio "
        "(DDD: Users, Market, Orders, Delivery)."
    ),
    "VERSION": APP_VERSION_TAG,
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
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
# Configuración de CORS (OWASP: Control de Acceso)
# ----------------------------------
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:19006"
    ).split(",")
]
CORS_ALLOW_CREDENTIALS = True

# ----------------------------------
# Configuración de correo
# ----------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = "Feria Conectada <no-reply@feriaconectada.com>"

# ----------------------------------
# Logging estructurado (DevSecOps: Monitoreo)
# ----------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} [{name}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "users": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ------------------------------------------------------------------------------
# CELERY CONFIGURATION (FASE 6: DevSecOps)
# ------------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Santiago"
CELERY_TASK_ALWAYS_EAGER = False
