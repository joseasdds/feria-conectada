# users/views.py
from rest_framework import viewsets, permissions
from .models import User, Role
from .serializers import UserSerializer, RoleSerializer
from .serializers_profiles import (
    FerianteProfileSerializer,
    ClienteProfileSerializer,
    RepartidorProfileSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.models_profiles import FerianteProfile, ClienteProfile, RepartidorProfile



class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista para listar roles disponibles."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista para listar o recuperar usuarios."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class MeProfileView(APIView):
    """Permite obtener o actualizar el perfil del usuario autenticado."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self, user):
        role = user.role.name if user.role else None
        if role == "Feriante":
            return FerianteProfileSerializer
        elif role == "Cliente":
            return ClienteProfileSerializer
        elif role == "Repartidor":
            return RepartidorProfileSerializer
        return None

    def get_profile_instance(self, user):
        role = user.role.name if user.role else None
        if role == "Feriante":
            return FerianteProfile.objects.get(user=user)
        elif role == "Cliente":
            return ClienteProfile.objects.get(user=user)
        elif role == "Repartidor":
            return RepartidorProfile.objects.get(user=user)
        return None

    def get(self, request):
        serializer_class = self.get_serializer_class(request.user)
        if not serializer_class:
            return Response(
                {"status": "error", "message": "Rol de usuario no válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = self.get_profile_instance(request.user)
        serializer = serializer_class(profile)
        return Response({"status": "success", "data": serializer.data})

    def patch(self, request):
        serializer_class = self.get_serializer_class(request.user)
        if not serializer_class:
            return Response(
                {"status": "error", "message": "Rol de usuario no válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = self.get_profile_instance(request.user)
        serializer = serializer_class(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)