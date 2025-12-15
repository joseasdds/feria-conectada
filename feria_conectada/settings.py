"""
Configuración Django para el proyecto Feria Conectada
Cumple con OWASP, DevSecOps y DDD.
"""

import os
from datetime import timedelta
from pathlib import Path

# --- IMPORTS DE CLOUDINARY ---
import cloudinary
import cloudinary.api
import cloudinary.uploader
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

# Validación de seguridad crítica
if not DEBUG and not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY must be set in the production environment (DEBUG=False)."
    )

# Valor dummy para desarrollo local si falta la key
if DEBUG and not SECRET_KEY:
    print("WARNING: Using Django's insecure default SECRET_KEY for development.")
    SECRET_KEY = "django-insecure-2s0_91-*8idoq#hzpl4o9!x5#%8t0v$q=lrg6dm(fhvw01qrnw"

# OWASP: Protección contra ataques Host header
_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
# Permitir acceso desde cualquier IP (celular, emulador, PC)
ALLOWED_HOSTS = ["*"]

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
    # Cloudinary Apps (Media)
    "cloudinary_storage",
    "cloudinary",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "djoser",
    "corsheaders",
    "drf_spectacular",
    "drf_spectacular_sidecar",
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
    "corsheaders.middleware.CorsMiddleware",  # 1. CORS primero
    "django.middleware.security.SecurityMiddleware",  # 2. Seguridad
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 3. Archivos estáticos
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
# B. Base de Datos (Híbrida: Cloud vs Local)
# ----------------------------------
if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True if not DEBUG else False,
        )
    }
else:
    print("⚠️  AVISO: No se encontró DATABASE_URL. Usando SQLite local.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ----------------------------------
# Validación de contraseñas (OWASP)
# ----------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------
# C. Usuario personalizado (DDD)
# ----------------------------------
AUTH_USER_MODEL = "users.User"

# ----------------------------------
# D. Django REST Framework + JWT
# ----------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # Permite acceso sin autenticación por defecto
    ],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ----------------------------------
# E. DJOSER (Permite registro libre en user_create)
# ----------------------------------
DJOSER = {
    "USER_ID_FIELD": "id",
    "LOGIN_FIELD": "email",
    "SERIALIZERS": {
        "user_create": "users.serializers.RegistrationSerializer",  # Tu serializer personalizado
        "user": "users.serializers.UserSerializer",
        "current_user": "users.serializers.UserSerializer",
    },
    "PERMISSIONS": {
        "user_create": [
            "rest_framework.permissions.AllowAny"
        ],  # ✅ ESTO ABRE LA PUERTA
        "user_list": ["rest_framework.permissions.IsAdminUser"],
        "user": ["rest_framework.permissions.IsAuthenticated"],
    },
}

# ----------------------------------
# F. DRF Spectacular (Docs)
# ----------------------------------
APP_VERSION_TAG = "v0.2-UsersProfiles"

SPECTACULAR_SETTINGS = {
    "TITLE": "Feria Conectada API",
    "DESCRIPTION": "Documentación de la API para la plataforma de comercio (DDD).",
    "VERSION": APP_VERSION_TAG,
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
}

# ----------------------------------
# Internacionalización
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

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ----------------------------------
# Configuración Primaria
# ----------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------
# Configuración de CORS
# ----------------------------------
_cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000"
)
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# ----------------------------------
# Configuración de correo (Consola en Dev)
# ----------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = "Feria Conectada <no-reply@feriaconectada.com>"

# ----------------------------------
# Logging
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

# ----------------------------------
# Celery (Redis)
# ----------------------------------
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Santiago"
CELERY_TASK_ALWAYS_EAGER = False

# ----------------------------------
# CONFIGURACIÓN CLOUDINARY (MEDIA)
# ----------------------------------

# 1. Inicialización EXPLÍCITA (Soluciona error "Must supply api_key")
cloudinary.config(
    cloud_name="dyf0vfbm5",
    api_key="614628397572641",
    api_secret="vWmdCXA-eobcDjlTTneGXWDh268",
    secure=True,
)

# 2. Configuración para el Backend de Storage de Django
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": "dyf0vfbm5",
    "API_KEY": "614628397572641",
    "API_SECRET": "vWmdCXA-eobcDjlTTneGXWDh268",
}

# 3. Definir Cloudinary como el almacenamiento predeterminado de archivos
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
