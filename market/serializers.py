# market/serializers.py
from rest_framework import serializers
from .models import Feria, Puesto, Producto


class ProductoSerializer(serializers.ModelSerializer):
    puesto_nombre = serializers.CharField(source='puesto.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'puesto', 'puesto_nombre', 'nombre', 'descripcion', 'precio', 'stock', 'unidad', 'activo', 'created_at']
        read_only_fields = ['id', 'puesto_nombre', 'created_at']


class PuestoSerializer(serializers.ModelSerializer):
    feria_nombre = serializers.CharField(source='feria.nombre', read_only=True)
    productos = ProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Puesto
        fields = ['id', 'feria', 'feriante', 'feria_nombre', 'nombre', 'categoria', 'activo', 'created_at', 'productos']
        read_only_fields = ['id', 'feria_nombre', 'created_at', 'productos']


class FeriaSerializer(serializers.ModelSerializer):
    puestos = PuestoSerializer(many=True, read_only=True)

    class Meta:
        model = Feria
        fields = ['id', 'nombre', 'comuna', 'direccion', 'descripcion', 'dias', 'horario', 'activa', 'created_at', 'puestos']
        read_only_fields = ['id', 'created_at', 'puestos']