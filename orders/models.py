import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q

# Constantes exportables para evitar strings mágicos
ORDER_CONFIRMED = "CONFIRMADO"
PAYMENT_SUCCESS = "SUCCESS"

# Estados posibles para un pedido
ORDER_STATUS_CHOICES = [
    ("CREADO", "Creado"),
    (ORDER_CONFIRMED, "Confirmado"),
    ("EN_PREPARACION", "En Preparación"),
    ("LISTO", "Listo para Entrega"),
    ("EN_CAMINO", "En Camino"),
    ("ENTREGADO", "Entregado"),
    ("CANCELADO", "Cancelado"),
]

# Estados posibles para un pago
PAYMENT_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    (PAYMENT_SUCCESS, "Success"),
    ("FAILED", "Failed"),
    ("REFUNDED", "Refunded"),
]


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )

    estado = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="CREADO"
    )

    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    notas = models.TextField(blank=True, null=True)

    # 👇 NUEVO CAMPO PARA EL MAPA
    direccion_envio = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Dirección física para la entrega (usada en mapas).",
    )

    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="deliveries",
        null=True,
        blank=True,
    )

    ubicacion_repartidor = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Última latitud/longitud conocida del repartidor.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        cliente_repr = getattr(self.cliente, "email", str(self.cliente))
        return f"Pedido {self.id} - {cliente_repr} - {self.estado}"

    def calcular_total(self):
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.subtotal or Decimal("0.00")
        if self.total != total:
            self.total = total
            self.save(update_fields=["total", "updated_at"])
        return self.total


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    producto = models.ForeignKey(
        "market.Producto", on_delete=models.PROTECT, related_name="order_items"
    )

    cantidad = models.PositiveIntegerField(default=1)

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del producto al momento de la compra",
    )

    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False, default=Decimal("0.00")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item de Pedido"
        verbose_name_plural = "Items de Pedido"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} - Order {self.order.id}"

    def save(self, *args, **kwargs):
        if self.precio_unitario is None:
            try:
                self.precio_unitario = self.producto.precio
            except Exception:
                self.precio_unitario = Decimal("0.00")
        self.subtotal = self.precio_unitario * Decimal(self.cantidad)
        super().save(*args, **kwargs)
        try:
            self.order.calcular_total()
        except Exception:
            pass


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="payments"
    )

    metodo = models.CharField(
        max_length=50, help_text="Método de pago (ej: EFECTIVO, TRANSBANK, MERCADOPAGO)"
    )

    monto = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="PENDING"
    )

    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Nombre de la pasarela (ej: mercadopago, flow)",
    )

    provider_ref = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="ID único del pago en la pasarela externa",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Unique constraint para reforzar idempotencia (solo cuando provider_ref no es NULL)
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_ref"],
                condition=Q(provider_ref__isnull=False),
                name="unique_provider_provider_ref_not_null",
            )
        ]

    def __str__(self):
        return (
            f"Payment {self.id} - {self.provider} - {self.provider_ref} - {self.status}"
        )


class PaymentLog(models.Model):
    received_at = models.DateTimeField(auto_now_add=True)

    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Nombre de la pasarela (ej: mercadopago, flow)",
    )

    provider_ref = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="ID del evento o pago en la pasarela",
    )

    payload = models.JSONField(help_text="Datos completos del webhook/evento recibido")

    status = models.CharField(
        max_length=50,
        default="RECEIVED",
        help_text="Estado interno del procesamiento del log",
    )

    handled = models.BooleanField(
        default=False, help_text="Indica si ya fue procesado por el sistema"
    )

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Registro de Pago"
        verbose_name_plural = "Registros de Pagos"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_ref"], name="uq_paymentlog_provider_ref"
            )
        ]

    def __str__(self):
        return f"PaymentLog {self.id} - {self.provider} - {self.status}"
