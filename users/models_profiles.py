# users/models_profiles.py
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class BaseProfile(models.Model):
    """
    Modelo abstracto base para todos los perfiles de usuario.
    Incluye UUID, timestamps y soporte para soft delete.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(class)s"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self):
        """Soft delete: marca el registro como eliminado sin borrarlo físicamente."""
        self.deleted_at = timezone.now()
        self.save()


class FerianteProfile(BaseProfile):
    """
    Perfil de un feriante: asocia el usuario con el puesto y la feria.
    `feria_asignada` es un UUID temporal (será FK en Fase 2).
    """

    rut = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=255)
    feria_asignada = models.UUIDField(null=True, blank=True)  # FK temporal
    puesto = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Feriante {self.user.email}"


class ClienteProfile(BaseProfile):
    """
    Perfil de cliente: dirección de entrega e historial de compras.
    """

    direccion_entrega = models.CharField(max_length=255)
    historial_compras = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Cliente {self.user.email}"


class RepartidorProfile(BaseProfile):
    """
    Perfil de repartidor: información de vehículo, licencia y zona.
    """

    vehiculo = models.CharField(max_length=100)
    licencia = models.CharField(max_length=50)
    zona_cobertura = models.CharField(max_length=255)

    def __str__(self):
        return f"Repartidor {self.user.email}"
