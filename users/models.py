import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import UserManager

class Role(models.Model):
    """Rol del sistema (Feriante, Cliente, Repartidor, Admin)."""
    ROLE_CHOICES = [
        ("ADMIN", "Administrador"),
        ("FERIANTE", "Feriante"),
        ("CLIENTE", "Cliente"),
        ("REPARTIDOR", "Repartidor"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()


class User(AbstractBaseUser, PermissionsMixin):
    """Modelo base de usuario con roles y campos personalizados."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True, null=True)

    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="users")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def get_role_display(self):
        return self.role.get_name_display() if self.role else "Sin rol"