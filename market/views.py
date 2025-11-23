# market/views.py

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

from market.models import Feria, Producto, Puesto
from market.serializers import (FeriaSerializer, ProductoSerializer,
                                PuestoSerializer)
from users.permissions import IsFeriante, IsOwnerOrReadOnly


class FeriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista de solo lectura para Ferias.
    Cualquiera puede ver ferias activas.
    """

    queryset = Feria.objects.filter(activa=True)
    serializer_class = FeriaSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["comuna", "activa"]
    search_fields = ["nombre", "comuna", "descripcion"]


class PuestoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Puestos.
    - GET: cualquiera puede ver puestos activos.
    - POST/PUT/PATCH/DELETE: solo feriante autenticado y dueño del puesto.
    """

    queryset = Puesto.objects.filter(activo=True)
    serializer_class = PuestoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["feria", "activo", "categoria"]
    search_fields = ["nombre", "categoria"]

    def get_permissions(self):
        # Lectura: cualquiera
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        # Escritura: auth + feriante + owner
        return [IsAuthenticatedOrReadOnly(), IsFeriante(), IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        """
        Al crear un puesto, asignar automáticamente al usuario autenticado como feriante.
        """
        serializer.save(feriante=self.request.user)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.filter(activo=True).select_related("puesto")
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["puesto", "activo"]
    search_fields = ["nombre", "descripcion"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticatedOrReadOnly(), IsFeriante(), IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        """
        Asegura que solo el dueño del puesto pueda crear productos en él.
        """
        puesto = serializer.validated_data["puesto"]
        if puesto.feriante != self.request.user:
            # Lanzamos error 403 si el puesto no es del usuario autenticado
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "No puedes crear productos en un puesto que no es tuyo."
            )

        serializer.save()
