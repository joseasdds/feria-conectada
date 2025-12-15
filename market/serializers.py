from rest_framework import serializers

from .models import Feria, Producto, Puesto


# ==========================================
# 1. SERIALIZER DE PRODUCTO
# ==========================================
class ProductoSerializer(serializers.ModelSerializer):
    puesto_nombre = serializers.CharField(source="puesto.nombre", read_only=True)

    # Garantizamos URL completa de la imagen
    imagen = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            "id",
            "puesto",
            "puesto_nombre",
            "nombre",
            "descripcion",
            "precio",
            "stock",
            "unidad",
            "imagen",
            "activo",
            "created_at",
        ]
        read_only_fields = ["id", "puesto_nombre", "created_at"]

    def get_imagen(self, obj):
        if hasattr(obj, "imagen") and obj.imagen:
            return obj.imagen.url
        return None


# ==========================================
# 2. SERIALIZER DE PUESTO (CORREGIDO)
# ==========================================
class PuestoSerializer(serializers.ModelSerializer):
    feria_nombre = serializers.CharField(source="feria.nombre", read_only=True)
    nombre_feriante = serializers.CharField(source="feriante.full_name", read_only=True)

    # Anidamos productos
    productos = ProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Puesto
        fields = [
            "id",
            "feria",
            "feria_nombre",
            "feriante",
            "nombre_feriante",
            "nombre",
            "categoria",  # ✅ agregado (existe en el modelo)
            "activo",
            "created_at",
            "productos",
        ]
        read_only_fields = [
            "id",
            "feria_nombre",
            "nombre_feriante",
            "feriante",
            "created_at",
            "productos",
        ]


# ==========================================
# 3. SERIALIZER DE FERIA
# ==========================================
class FeriaSerializer(serializers.ModelSerializer):
    puestos = PuestoSerializer(many=True, read_only=True)

    class Meta:
        model = Feria
        fields = [
            "id",
            "nombre",
            "comuna",
            "direccion",
            "descripcion",
            "dias",
            "horario",
            "activa",
            "created_at",
            "puestos",
        ]
        read_only_fields = ["id", "created_at", "puestos"]
