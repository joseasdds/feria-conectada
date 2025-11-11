# users/views_profiles.py
from rest_framework import generics, permissions, response, status
from .models_profiles import FerianteProfile, ClienteProfile, RepartidorProfile
from .serializers_profiles import (
    FerianteProfileSerializer,
    ClienteProfileSerializer,
    RepartidorProfileSerializer,
)


class MeProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint que devuelve o actualiza el perfil del usuario autenticado.
    Selecciona dinámicamente el serializer según el rol asociado al usuario.
    Disponibles:
      - Feriante → FerianteProfileSerializer
      - Cliente → ClienteProfileSerializer
      - Repartidor → RepartidorProfileSerializer

    Métodos:
      GET   → obtener perfil autenticado
      PATCH → actualizar parcialmente su perfil
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        role_name = self.request.user.role.name.strip().lower()
        if role_name == "feriante":
            return FerianteProfileSerializer
        elif role_name == "cliente":
            return ClienteProfileSerializer
        elif role_name == "repartidor":
            return RepartidorProfileSerializer
        else:
            return None

    def get_object(self):
        role_name = self.request.user.role.name.strip().lower()
        user = self.request.user

        if role_name == "feriante":
            return FerianteProfile.objects.get(user=user)
        elif role_name == "cliente":
            return ClienteProfile.objects.get(user=user)
        elif role_name == "repartidor":
            return RepartidorProfile.objects.get(user=user)
        else:
            return None

    def get(self, request, *args, **kwargs):
        """
        GET /api/v1/me/ → retorna datos personales + perfil.
        """
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        if not serializer_class or not instance:
            return response.Response(
                {
                    "status": "error",
                    "message": "El rol del usuario no posee un perfil asociado.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = serializer_class(instance)
        return response.Response(
            {
                "status": "success",
                "message": "Perfil recuperado correctamente.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        """
        PATCH /api/v1/me/ → permite actualizar parcialmente su perfil.
        """
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        if not serializer_class or not instance:
            return response.Response(
                {
                    "status": "error",
                    "message": "Rol no reconocido para actualización.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            {
                "status": "success",
                "message": "Perfil actualizado correctamente.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )