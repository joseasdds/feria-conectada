# users/validators.py
from rest_framework.serializers import ValidationError

from .utils import normalize_rut, validate_rut


def validar_rut_chileno(value):
    """
    Validador DRF: normaliza y valida RUT (lanza ValidationError si inválido).
    Si value es blank/None y el campo permite blank, no levanta error aquí.
    """
    if value in (None, ""):
        return  # permitimos blank; el serializer controla required/allow_blank

    norm = normalize_rut(value)
    if not norm:
        raise ValidationError("RUT vacío o en formato no soportado.")

    if not validate_rut(norm):
        raise ValidationError("RUT inválido (DV no coincide).")
