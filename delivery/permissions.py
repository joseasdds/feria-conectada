# delivery/permissions.py
from rest_framework.permissions import BasePermission


class IsRepartidor(BasePermission):
    """
    Permite solo a usuarios repartidores.
    Comprueba:
      - user.role.name == 'repartidor' (case-insensitive)
      - o existencia de un profile relacionado (varios nombres comunes)
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Chequeo por Role
        role = getattr(user, "role", None)
        try:
            if role and getattr(role, "name", "").lower() == "repartidor":
                return True
        except Exception:
            pass

        # Chequeo por related_name del profile (nombres comunes)
        try:
            return (
                hasattr(user, "delivery_profile")
                or hasattr(user, "deliveryprofile")
                or hasattr(user, "repartidor_profile")
                or hasattr(user, "repartidorprofile")
                or hasattr(user, "profile")
            )
        except Exception:
            return False

    def has_object_permission(self, request, view, obj):
        # Admin siempre puede
        if getattr(request.user, "is_staff", False):
            return True

        # Si objeto tiene repartidor_id, verificar que sea el mismo usuario
        return getattr(obj, "repartidor_id", None) == getattr(request.user, "id", None)
