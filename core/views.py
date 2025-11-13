from django.http import JsonResponse
from django.db import connection
from django.utils.timezone import now
import os

SERVICE_NAME = "feria-conectada"

def _db_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return True
    except Exception:
        return False

def health(request):
    # Liveness: responde si el proceso está vivo
    data = {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": os.getenv("APP_VERSION", "v0.2"),
        "commit": os.getenv("APP_COMMIT", ""),
        "env": os.getenv("APP_ENV", "local"),
        "time": now().isoformat(),
    }
    return JsonResponse(data, status=200)

def ready(request):
    # Readiness: verifica dependencias críticas (DB)
    db_ok = _db_ok()
    data = {
        "status": "ok" if db_ok else "degraded",
        "service": SERVICE_NAME,
        "version": os.getenv("APP_VERSION", "v0.2"),
        "commit": os.getenv("APP_COMMIT", ""),
        "env": os.getenv("APP_ENV", "local"),
        "time": now().isoformat(),
        "dependencies": {"database": "ok" if db_ok else "fail"},
    }
    return JsonResponse(data, status=200 if db_ok else 503)