# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'estado', 'total', 'created_at']
    list_filter = ['estado', 'created_at']
    search_fields = ['cliente__email', 'id']
    readonly_fields = ['id', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'producto', 'cantidad', 'precio_unitario', 'subtotal', 'created_at']
    readonly_fields = ['subtotal', 'created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'metodo', 'monto', 'status', 'created_at']
    readonly_fields = ['id', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id']