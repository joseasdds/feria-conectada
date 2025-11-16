# orders/models.py
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings

STATUS_CHOICES = [
    ('CREADO', 'Creado'),
    ('CONFIRMADO', 'Confirmado'),
    ('EN_PREPARACION', 'En Preparación'),
    ('LISTO', 'Listo para Entrega'),
    ('EN_CAMINO', 'En Camino'),
    ('ENTREGADO', 'Entregado'),
    ('CANCELADO', 'Cancelado'),
]

class Order(models.Model):
    """
    Pedido realizado por un cliente.
    Puede contener productos de múltiples puestos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CREADO'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    notas = models.TextField(blank=True, null=True)
    
    # Opcional: repartidor asignado
    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='deliveries',
        null=True,
        blank=True
    )
    ubicacion_repartidor = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Última latitud/longitud conocida del repartidor."
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
    def __str__(self):
        cliente_repr = getattr(self.cliente, 'email', str(self.cliente))
        return f"Pedido {self.id} - {cliente_repr} - {self.estado}"
    
    def calcular_total(self):
        """
        Recalcula el total sumando los subtotales de los items.
        No llama a save() si el total no cambió para evitar work loops.
        """
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.subtotal or Decimal('0.00')
        # Evitar actualizaciones innecesarias
        if self.total != total:
            self.total = total
            self.save(update_fields=['total', 'updated_at'])
        return self.total


class OrderItem(models.Model):
    """
    Item individual dentro de un pedido.
    Guarda precio_unitario y subtotal al momento de la compra.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(
        'market.Producto',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del producto al momento de la compra"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Items de Pedido'
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} - Order {self.order.id}"
    
    def save(self, *args, **kwargs):
        """
        Calcula el subtotal antes de guardar y luego actualiza el total del pedido.
        """
        # Asegurarse de que precio_unitario exista
        if self.precio_unitario is None:
            # tomar precio actual del producto como fallback (aunque ideal es asignarlo en create)
            try:
                self.precio_unitario = self.producto.precio
            except Exception:
                self.precio_unitario = Decimal('0.00')
        self.subtotal = self.precio_unitario * Decimal(self.cantidad)
        super().save(*args, **kwargs)
        # Después de guardar el item, recalcular total del pedido
        # Usamos update_fields en calcular_total para evitar recursión infinita
        try:
            self.order.calcular_total()
        except Exception:
            # evitar romper el flujo si algo falla (loguear si quieres)
            pass


class Payment(models.Model):
    STATUS_CHOICES_PAYMENT = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payments')
    metodo = models.CharField(max_length=50)  # ej: 'EFECTIVO', 'PSE', 'TRANSBANK'
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES_PAYMENT, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Payment {self.id} - {self.monto} ({self.status})"