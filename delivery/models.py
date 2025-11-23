# delivery/models.py
import uuid

from django.conf import settings
from django.db import models

from orders.models import Order  # ya existe en tu proyecto


class DeliveryProfile(models.Model):
    """
    Perfil adicional para los usuarios que son repartidores.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delivery_profile",
    )
    vehiculo = models.CharField(
        max_length=50,
        choices=[
            ("Bicicleta", "Bicicleta"),
            ("Moto", "Moto"),
            ("Auto", "Auto"),
            ("Caminando", "Caminando"),
        ],
        default="Caminando",
    )
    disponible = models.BooleanField(default=True)
    rating_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Repartidor"
        verbose_name_plural = "Perfiles de Repartidores"

    def __str__(self):
        return f"Repartidor: {self.user.email} ({self.vehiculo})"


class DeliveryAssignment(models.Model):
    """
    Asignación de entrega para un pedido (Order).
    Un Order tiene a lo sumo una DeliveryAssignment (OneToOne).
    """

    STATE_PENDING = "PENDING"
    STATE_ASSIGNED = "ASSIGNED"
    STATE_IN_ROUTE = "IN_ROUTE"
    STATE_DELIVERED = "DELIVERED"
    STATE_CANCELLED = "CANCELLED"

    STATE_CHOICES = [
        (STATE_PENDING, "Pending"),
        (STATE_ASSIGNED, "Assigned"),
        (STATE_IN_ROUTE, "In route"),
        (STATE_DELIVERED, "Delivered"),
        (STATE_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delivery_assignments",
        null=True,
        blank=True,
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery_assignment"
    )
    estado = models.CharField(
        max_length=20, choices=STATE_CHOICES, default=STATE_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asignación de Entrega"
        verbose_name_plural = "Asignaciones de Entrega"

    def __str__(self):
        return f"{self.order.pk} -> {self.repartidor} [{self.estado}]"
