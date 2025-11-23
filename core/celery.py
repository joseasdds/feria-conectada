# core/celery.py

import os

from celery import Celery

# 1. CORRECCIÓN: Apuntar al archivo settings real de tu proyecto Django
# Lo más probable es que se llame 'feria_conectada.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "feria_conectada.settings")

# 2. Crear la instancia de la aplicación Celery
# El nombre de la aplicación es 'feria_conectada' (nombre de tu proyecto)
app = Celery("feria_conectada")

# 3. Cargar la configuración de Celery desde el settings.py de Django
# El espacio de nombres 'CELERY' evita conflictos (CELERY_BROKER_URL, etc.)
app.config_from_object("django.conf:settings", namespace="CELERY")

# 4. Descubrimiento automático de tareas
# Celery buscará el archivo tasks.py en todas las apps listadas en INSTALLED_APPS
app.autodiscover_tasks()
