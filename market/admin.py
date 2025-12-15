# Register your models here.
from django.contrib import admin

from .models import Feria, Producto, Puesto


@admin.register(Feria)
class FeriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "comuna", "activa")
    search_fields = ("nombre", "comuna")


@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "feria", "feriante", "activo")
    list_filter = ("feria",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # Aquí agregamos 'image' para que veas en la lista si tiene foto o no
    list_display = ("nombre", "puesto", "precio", "stock", "image", "activo")
    list_filter = ("puesto__feria", "activo")
    search_fields = ("nombre",)
