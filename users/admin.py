from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Configuración admin limpia para el modelo personalizado User."""

    # Campos que se muestran en la lista
    list_display = (
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
        "is_verified",
    )
    list_filter = ("is_active", "is_staff", "role")
    search_fields = ("email", "full_name")
    ordering = ("email",)

    # No tenemos 'username', así que lo removemos
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Información personal"), {"fields": ("full_name", "phone", "role")}),
        (
            _("Permisos"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Fechas importantes"), {"fields": ("last_login", "created_at")}),
    )

    # Campos usados al crear un nuevo usuario en el admin
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2"),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")
