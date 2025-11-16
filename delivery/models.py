import uuid
from django.db import models
from django.conf import settings


class DeliveryProfile(models.Model):
    """
    Perfil adicional para los usuarios que son repartidores.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_profile'
    )
    vehiculo = models.CharField(
        max_length=50,
        choices=[
            ('Bicicleta', 'Bicicleta'),
            ('Moto', 'Moto'),
            ('Auto', 'Auto'),
            ('Caminando', 'Caminando')
        ],
        default='Caminando'
    )
    disponible = models.BooleanField(default=True)
    rating_promedio = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Repartidor'
        verbose_name_plural = 'Perfiles de Repartidores'
        
    def __str__(self):
        return f"Repartidor: {self.user.email} ({self.vehiculo})"