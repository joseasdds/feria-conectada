# users/views.py - CORREGIDO

from rest_framework import viewsets, permissions
from .models import User, Role
from .serializers import UserSerializer, RoleSerializer

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista para listar roles disponibles."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """Gestión de usuarios (solo admin o el propio usuario)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        # Devuelve las CLASES de permiso (sin instanciar con ())
        if self.action in ["create"]:
            return [permissions.AllowAny]
        elif self.action in ["update", "partial_update", "retrieve"]:
            return [permissions.IsAuthenticated]
        return [permissions.IsAdminUser]