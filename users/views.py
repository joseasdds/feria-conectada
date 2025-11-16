# users/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from rest_framework import mixins

# Importaciones de CORE y Modelos
from core.api_response import APIResponse
from .models import Role
from .models_profiles import FerianteProfile, ClienteProfile, RepartidorProfile 
from .serializers import UserSerializer, RoleSerializer
from .serializers_profiles import MeSerializer


User = get_user_model()


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista para listar roles disponibles (Público/ReadOnly).
    Endpoint: /api/v1/roles/
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista para listar o recuperar usuarios (Generalmente restringida a Admin).
    Endpoint: /api/v1/users/
    """
    queryset = User.objects.all().select_related('role')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class MeViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    Endpoint (/api/v1/me/) que permite a un usuario autenticado ver y editar 
    sus propios datos de User y su Perfil asociado.
    
    Usa list() en lugar de retrieve() para que funcione sin pk en la URL.
    """
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimización: Pre-carga los perfiles y el rol en una sola consulta."""
        return User.objects.all().select_related(
            'role', 
            'ferianteprofile',
            'clienteprofile',
            'repartidorprofile'
        )

    def list(self, request, *args, **kwargs):
        """
        GET /api/v1/me/ - Devuelve el perfil del usuario autenticado.
        Usa list() para que el router genere 'me-list' sin necesidad de pk.
        """
        try:
            user = get_object_or_404(self.get_queryset(), pk=request.user.pk)
            serializer = self.get_serializer(user)
            return Response(
                APIResponse.success(
                    data=serializer.data, 
                    message="Datos de perfil recuperados con éxito"
                )
            )
        except ObjectDoesNotExist:
            return Response(
                APIResponse.error(
                    "Usuario no encontrado (Internal error).", 
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/v1/me/ - Actualiza campos del User y del Profile.
        Nota: Requiere pasar pk en la URL, pero podemos sobrescribirlo.
        """
        try:
            # Forzar que siempre actualice al usuario autenticado
            user = get_object_or_404(self.get_queryset(), pk=request.user.pk)
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return Response(
                APIResponse.success(
                    data=serializer.data, 
                    message="Perfil actualizado correctamente"
                )
            )
        except Exception as e:
            error_data = getattr(e, 'detail', str(e))
            return Response(
                APIResponse.error(
                    "Error al actualizar el perfil. Revise los campos.", 
                    data=error_data
                ),
                status=status.HTTP_400_BAD_REQUEST
            )