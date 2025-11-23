from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsFeriante(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return (
            user.is_authenticated
            and getattr(user.role, "name", "").lower() == "feriante"
        )


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Para Puesto: owner es obj.feriante
        owner = getattr(obj, "feriante", None)
        # Para Producto: owner es obj.puesto.feriante
        if owner is None and hasattr(obj, "puesto"):
            owner = getattr(obj.puesto, "feriante", None)
        return owner == request.user
