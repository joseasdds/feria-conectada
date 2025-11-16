from rest_framework import serializers
from orders.models import Order, OrderItem
from market.models import Producto


class OrderItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    puesto_nombre = serializers.CharField(source='producto.puesto.nombre', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'producto', 'producto_nombre', 'puesto_nombre',
            'cantidad', 'precio_unitario', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']


class OrderItemCreateSerializer(serializers.Serializer):
    producto = serializers.UUIDField()
    cantidad = serializers.IntegerField(min_value=1)

    def validate_producto(self, value):
        try:
            Producto.objects.get(id=value, activo=True)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado o inactivo.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    cliente_email = serializers.EmailField(source='cliente.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'cliente', 'cliente_email', 'estado', 'total',
            'notas', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'cliente', 'total', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['notas', 'items']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("El pedido debe tener al menos un producto.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        cliente = self.context['request'].user

        order = Order.objects.create(
            cliente=cliente,
            notas=validated_data.get('notas', ''),
            estado='CREADO'
        )

        for item_data in items_data:
            producto = Producto.objects.get(id=item_data['producto'])
            OrderItem.objects.create(
                order=order,
                producto=producto,
                cantidad=item_data['cantidad'],
                precio_unitario=producto.precio,
            )

        order.calcular_total()
        return order