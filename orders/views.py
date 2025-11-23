# orders/views.py
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import (decorators, permissions, response, serializers,
                            status, viewsets)

from market.models import Producto

from .models import Order, OrderItem, Payment
from .serializers import OrderCreateSerializer, OrderSerializer


# Permisos por rol
class IsCliente(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(getattr(request.user, "role", None), "name", "").upper()
            == "CLIENTE"
        )


class IsFeriante(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(getattr(request.user, "role", None), "name", "").upper()
            == "FERIANTE"
        )


class IsRepartidor(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(getattr(request.user, "role", None), "name", "").upper()
            == "REPARTIDOR"
        )


# Vista para cliente: crear y listar sus pedidos
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCliente]

    def get_queryset(self):
        return Order.objects.filter(cliente=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        out_serializer = OrderSerializer(instance, context={"request": request})
        headers = self.get_success_headers(out_serializer.data)
        return response.Response(
            out_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


# Vista para feriante: ver pedidos que contienen productos de sus puestos
class FerianteOrdersViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsFeriante]

    def get_queryset(self):
        from market.models import Puesto

        puestos = Puesto.objects.filter(feriante=self.request.user).values_list(
            "id", flat=True
        )
        return (
            Order.objects.filter(items__producto__puesto__id__in=puestos)
            .distinct()
            .order_by("-created_at")
        )


# Vista para repartidor: claim y complete
class RepartidorOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsRepartidor]

    def get_queryset(self):
        return Order.objects.filter(repartidor=self.request.user).order_by(
            "-created_at"
        )

    @decorators.action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        if order.estado not in ["CONFIRMADO", "LISTO"]:
            return response.Response(
                {"detail": "El pedido no está listo para ser tomado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.estado = "EN_CAMINO"
        order.repartidor = request.user
        order.save(update_fields=["estado", "repartidor"])
        return response.Response(self.get_serializer(order).data)

    @decorators.action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        if order.estado != "EN_CAMINO":
            return response.Response(
                {"detail": "El pedido no está en camino."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.estado = "ENTREGADO"
        order.save(update_fields=["estado"])
        return response.Response(self.get_serializer(order).data)


# Serializers (definidos aquí para mantener todo en un solo archivo)
class OrderItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    puesto_nombre = serializers.CharField(
        source="producto.puesto.nombre", read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "producto",
            "producto_nombre",
            "puesto_nombre",
            "cantidad",
            "precio_unitario",
            "subtotal",
        ]
        read_only_fields = ["id", "subtotal"]


class OrderItemCreateSerializer(serializers.Serializer):
    producto = serializers.UUIDField()
    cantidad = serializers.IntegerField(min_value=1)

    def validate_producto(self, value):
        try:
            Producto.objects.get(id=value, activo=True, puesto__activo=True)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado o inactivo.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    cliente_email = serializers.EmailField(source="cliente.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "cliente",
            "cliente_email",
            "estado",
            "total",
            "notas",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "cliente", "total", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ["notas", "items"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "El pedido debe tener al menos un producto."
            )
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        cliente = validated_data.pop("cliente", None) or self.context["request"].user

        with transaction.atomic():
            order = Order.objects.create(
                cliente=cliente, notas=validated_data.get("notas", ""), estado="CREADO"
            )

            total = Decimal("0.00")

            for idx, item_data in enumerate(items_data):
                prod_id = item_data["producto"]
                cantidad = int(item_data["cantidad"])

                try:
                    producto = Producto.objects.select_for_update().get(
                        id=prod_id, activo=True, puesto__activo=True
                    )
                except Producto.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            "items": [
                                {
                                    "producto": "Producto no encontrado o inactivo.",
                                    "index": idx,
                                }
                            ]
                        }
                    )

                if producto.stock < cantidad:
                    raise serializers.ValidationError(
                        {
                            "items": [
                                {
                                    "cantidad": f"Stock insuficiente para producto {producto.id}. Disponible: {producto.stock}",
                                    "index": idx,
                                }
                            ]
                        }
                    )

                producto.stock -= cantidad
                producto.save(update_fields=["stock"])

                precio_unitario = producto.precio or Decimal("0.00")
                subtotal = precio_unitario * Decimal(cantidad)

                OrderItem.objects.create(
                    order=order,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                )

                total += subtotal

            order.total = total
            order.save(update_fields=["total"])

            Payment.objects.create(order=order, monto=total, status="PENDIENTE")

        return order
