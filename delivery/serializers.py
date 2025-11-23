# delivery/serializers.py
from rest_framework import serializers

from delivery.models import DeliveryAssignment

# Intento importar un serializer simple de Order si ya existiese.
try:
    from orders.serializers import OrderSimpleSerializer
except Exception:
    OrderSimpleSerializer = None


class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    if OrderSimpleSerializer:
        order = OrderSimpleSerializer(read_only=True)
    else:
        order = serializers.PrimaryKeyRelatedField(read_only=True)

    order_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = DeliveryAssignment
        fields = (
            "id",
            "order",
            "order_id",
            "repartidor",
            "estado",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "order")

    def create(self, validated_data):
        # Crear assignment a partir de order_id (sistema/admin). Si tu flujo difiere, ajusta.
        order_id = validated_data.pop("order_id")
        from orders.models import Order

        order = Order.objects.get(pk=order_id)
        assignment = DeliveryAssignment.objects.create(order=order, **validated_data)
        return assignment
