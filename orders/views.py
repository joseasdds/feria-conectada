from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.response import Response

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        """
        Define qué pedidos ve cada usuario según su ROL.
        Incluye optimización de consultas (prefetch_related).
        """
        user = self.request.user
        role = getattr(getattr(user, "role", None), "name", "").upper()

        # -------------------------------------------------------
        # 1. OPTIMIZACIÓN N+1 (PREFETCH)
        # Traemos Cliente, Items, Productos y Puestos en una sola query
        # -------------------------------------------------------
        queryset = Order.objects.select_related("cliente").prefetch_related(
            "items", "items__producto", "items__producto__puesto"
        )

        # 🛒 Lógica CLIENTE: Ve sus propios pedidos
        if role == "CLIENTE":
            return queryset.filter(cliente=user).order_by("-created_at")

        # 🍎 Lógica FERIANTE: Ve pedidos que tengan productos de sus puestos
        if role == "FERIANTE":
            from market.models import Puesto

            puestos_ids = Puesto.objects.filter(feriante=user).values_list(
                "id", flat=True
            )
            # Distinct() es necesario porque una orden puede tener 2 productos del mismo feriante
            return (
                queryset.filter(items__producto__puesto__id__in=puestos_ids)
                .distinct()
                .order_by("-created_at")
            )

        # 🛵 Lógica REPARTIDOR: Ve pedidos LISTOS o los que ya tiene asignados
        if role == "REPARTIDOR":
            return queryset.filter(Q(estado="LISTO") | Q(repartidor=user)).order_by(
                "-created_at"
            )

        # Admin o rol desconocido
        return Order.objects.none()

    # ===========================================================
    # 2. SOLUCIÓN CRÍTICA: RESPUESTA COMPLETA AL CREAR
    # ===========================================================
    def create(self, request, *args, **kwargs):
        # Usamos el serializer de ESCRITURA para validar
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)

        # Guardamos la orden (se ejecuta create() del serializer)
        order = write_serializer.save()

        # TRUCO: Volvemos a serializar con el serializer de LECTURA
        # Esto asegura que el Frontend reciba ID, items, total, etc.
        read_serializer = OrderSerializer(order)

        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    # ===========================================================
    # ACCIONES DE REPARTIDOR
    # ===========================================================

    @decorators.action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        """Repartidor toma un pedido"""
        order = get_object_or_404(Order, pk=pk)

        role = getattr(getattr(request.user, "role", None), "name", "").upper()
        if role != "REPARTIDOR":
            return Response(
                {"detail": "Solo repartidores pueden tomar pedidos."}, status=403
            )

        if order.estado != "LISTO":
            return Response(
                {"detail": "El pedido no está listo para ser tomado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.estado = "EN_CAMINO"
        order.repartidor = request.user
        order.save(update_fields=["estado", "repartidor"])
        return Response(OrderSerializer(order).data)

    @decorators.action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Repartidor finaliza un pedido"""
        order = get_object_or_404(Order, pk=pk)

        if order.repartidor != request.user:
            return Response(
                {"detail": "No eres el repartidor de este pedido."}, status=403
            )

        if order.estado != "EN_CAMINO":
            return Response(
                {"detail": "El pedido no está en camino."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.estado = "ENTREGADO"
        order.save(update_fields=["estado"])
        return Response(OrderSerializer(order).data)
