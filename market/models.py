import uuid

# 1. IMPORTANTE: Importamos el campo de Cloudinary
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.db import models


class Feria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=120)
    comuna = models.CharField(max_length=80, default="Sin comuna")
    direccion = models.CharField(max_length=150, blank=True)
    descripcion = models.TextField(blank=True)
    dias = models.CharField(max_length=120, blank=True)  # ej: "Lun-Mie-Vie"
    horario = models.CharField(max_length=80, blank=True)  # ej: "09:00-18:00"
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ["comuna", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.comuna})"


class Puesto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feria = models.ForeignKey(Feria, on_delete=models.CASCADE, related_name="puestos")
    feriante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="puestos"
    )
    nombre = models.CharField(max_length=120)
    categoria = models.CharField(max_length=80, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        unique_together = [("feria", "nombre")]

    def __str__(self):
        return f"{self.nombre} - {self.feria.nombre}"


class Producto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    puesto = models.ForeignKey(
        Puesto, on_delete=models.CASCADE, related_name="productos"
    )
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    unidad = models.CharField(
        max_length=20, default="unidad"
    )  # unidad, kg, bandeja, etc.

    # 2. NUEVO CAMPO DE IMAGEN 📸
    # Esto guardará la URL de la foto en la base de datos y el archivo en Cloudinary
    image = CloudinaryField("image", folder="productos", blank=True, null=True)

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
