from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import Feria, Producto, Puesto
from .serializers import FeriaSerializer, ProductoSerializer, PuestoSerializer


# ==========================
# FERIAS
# ==========================
class FeriaViewSet(viewsets.ModelViewSet):
    """
    - Cualquiera puede VER ferias (GET)
    - Solo usuarios autenticados pueden CREAR / EDITAR / ELIMINAR
    """

    queryset = Feria.objects.all()
    serializer_class = FeriaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["nombre", "activo"]
    search_fields = ["nombre", "direccion"]
    ordering_fields = ["created_at", "nombre"]


# ==========================
# PUESTOS
# ==========================
class PuestoViewSet(viewsets.ModelViewSet):
    """
    - Cualquiera puede VER puestos (GET)
    - Solo usuarios autenticados pueden CREAR / EDITAR / ELIMINAR
    - El feriante se asigna automáticamente al crear el puesto
    - Filtrable por feriante, feria, activo
    """

    queryset = Puesto.objects.all()
    serializer_class = PuestoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # ✅ CLAVE: Habilitar filtros
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "feriante",
        "feria",
        "activo",
    ]  # 👈 Esto permite ?feriante=<user.id>
    search_fields = ["nombre", "categoria"]
    ordering_fields = ["created_at", "nombre"]

    def get_queryset(self):
        """
        Devuelve todos los puestos.
        El filtro por feriante se maneja automáticamente con filterset_fields.
        """
        return Puesto.objects.all()

    def perform_create(self, serializer):
        """
        Al crear un puesto:
        - Se asigna automáticamente el usuario logueado como feriante
        - Evita que el frontend tenga que mandar el feriante_id
        """
        serializer.save(feriante=self.request.user)


# ==========================
# PRODUCTOS
# ==========================
class ProductoViewSet(viewsets.ModelViewSet):
    """
    - Cualquiera puede VER productos (GET)
    - Solo usuarios autenticados pueden CREAR / EDITAR / ELIMINAR
    - Filtrable por puesto, activo
    """

    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["puesto", "activo"]  # 👈 Ya lo tienes, pero lo dejo explícito
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["created_at", "precio", "nombre"]
