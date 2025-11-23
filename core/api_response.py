# core/api_response.py
import os
import uuid

from django.conf import settings


class APIResponse:
    """
    Clase estática para generar respuestas JSON estandarizadas
    con los metadatos de request y build.
    """

    @staticmethod
    def _get_meta(request_id=None):
        """Genera el diccionario de metadatos."""
        # Usa el request_id proporcionado o genera uno nuevo
        req_id = request_id if request_id else str(uuid.uuid4())

        # Obtenemos build info de las variables de entorno o settings (para CI/CD)
        build_sha = os.environ.get("BUILD_SHA", settings.APP_VERSION_TAG)

        return {"request_id": req_id, "build": build_sha}

    @staticmethod
    def success(data=None, message="Operación exitosa", request_id=None):
        """Genera una respuesta de éxito con el formato estándar."""
        return {
            "status": "success",
            "data": data if data is not None else {},
            "message": message,
            "meta": APIResponse._get_meta(request_id),
        }

    @staticmethod
    def error(
        message="Ha ocurrido un error", data=None, status_code=400, request_id=None
    ):
        """Genera una respuesta de error con el formato estándar."""
        # El status_code es principalmente para logging/observabilidad,
        # pero es útil pasarlo en la vista para devolver el código HTTP correcto.
        return {
            "status": "error",
            "data": data if data is not None else {},
            "message": message,
            "meta": APIResponse._get_meta(request_id),
        }
