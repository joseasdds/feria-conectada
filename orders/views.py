# orders/views.py
from rest_framework import viewsets, permissions, decorators, response, status
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from django.shortcuts import get_object_or_404


# Permisos por rol
class IsCliente(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(getattr(request.user, 'role', None), 'name', '').upper() == 'CLIENTE'
        )


class IsFeriante(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(getattr(request.user, 'role', None), 'name', '').upper() == 'FERIANTE'
        )


class IsRepartidor(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(getattr(request.user, 'role', None), 'name', '').upper() == 'REPARTIDOR'
        )


# Vista para cliente: crear y listar sus pedidos
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCliente]

    def get_queryset(self):
        return Order.objects.filter(cliente=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user)


# Vista para feriante: ver pedidos que contienen productos de sus puestos
class FerianteOrdersViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsFeriante]

    def get_queryset(self):
        from market.models import Puesto
        puestos = Puesto.objects.filter(feriante=self.request.user).values_list('id', flat=True)
        return Order.objects.filter(items__producto__puesto__id__in=puestos).distinct().order_by('-created_at')


# Vista para repartidor: claim y complete
class RepartidorOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsRepartidor]

    def get_queryset(self):
        return Order.objects.filter(repartidor=self.request.user).order_by('-created_at')

    @decorators.action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        if order.estado not in ['CONFIRMADO', 'LISTO']:
            return response.Response(
                {"detail": "El pedido no está listo para ser tomado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.estado = 'EN_CAMINO'
        order.repartidor = request.user
        order.save(update_fields=['estado', 'repartidor'])
        return response.Response(self.get_serializer(order).data)

    @decorators.action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        if order.estado != 'EN_CAMINO':
            return response.Response(
                {"detail": "El pedido no está en camino."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.estado = 'ENTREGADO'
        order.save(update_fields=['estado'])
        return response.Response(self.get_serializer(order).data)