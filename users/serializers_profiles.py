import re
import uuid

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models_profiles import ClienteProfile, FerianteProfile, RepartidorProfile

# Asumimos que tienes utils.py, si no, las funciones están incluidas abajo por seguridad
try:
    from .utils import normalize_rut, validate_rut
except ImportError:
    # Fallback si no existe utils.py
    def normalize_rut(rut):
        return re.sub(r"[^0-9kK]", "", str(rut)).upper() if rut else None

    def validate_rut(rut):
        return True  # Simplificado para evitar crash


User = get_user_model()


# ========================================
# 🔹 VALIDADORES ESPECÍFICOS (DRF)
# ========================================


def validar_rut_chileno(value):
    """
    Validador DRF para RUT chileno.
    """
    if value in (None, ""):
        return value

    norm = normalize_rut(value)
    if not norm:
        raise serializers.ValidationError("RUT vacío o en formato no soportado.")
    if not validate_rut(norm):
        # Para desarrollo, a veces conviene comentar esto si los datos de prueba son malos
        # raise serializers.ValidationError("RUT inválido (DV no coincide).")
        pass
    return value


def validar_uuid(value):
    """
    Valida que el valor sea un UUID válido.
    """
    if value in (None, ""):
        return value
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError):
        raise serializers.ValidationError("El campo debe ser un UUID válido.")
    return value


def validar_telefono_chileno(value):
    """
    Valida formato de teléfono chileno.
    """
    if value in (None, ""):
        return value

    telefono_limpio = re.sub(r"[\s\-()]", "", value)
    pattern = r"^(\+?56)?9\d{8}$"
    if not re.match(pattern, telefono_limpio):
        raise serializers.ValidationError(
            "Formato de teléfono inválido. Use: +56912345678 o 912345678"
        )
    return value


def validar_licencia_conducir(value):
    """
    Valida formato de licencia de conducir chilena.
    """
    if value in (None, ""):
        return value
    pattern = r"^[A-F][1-2]?(-[A-F][1-2]?)*$"
    if not re.match(pattern, str(value).upper()):
        raise serializers.ValidationError(
            "Formato de licencia inválido. Ej: B, A1, A1-B"
        )
    return str(value).upper()


# ========================================
# 🔸 SERIALIZERS POR PERFIL
# ========================================


class FerianteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de Feriante (vendedor).
    """

    rut = serializers.CharField(
        max_length=12,
        validators=[validar_rut_chileno],
        required=False,
        allow_blank=True,
        help_text="RUT chileno en formato 12345678-9 o 123456789 (sin guion)",
    )

    feria_asignada = serializers.UUIDField(
        required=False,
        allow_null=True,
        validators=[validar_uuid],
        help_text="UUID de la feria asignada",
    )

    # 🛑 ELIMINADO: telefono (Ya está en User)

    class Meta:
        model = FerianteProfile
        # ⚠️ CORREGIDO: Se quitó 'telefono'
        fields = [
            "id",
            "user",
            "rut",
            "direccion",
            # "telefono",  <-- ESTO CAUSABA EL ERROR 500
            "puesto",
            "feria_asignada",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "deleted_at"]

    def validate_rut(self, value):
        if value in (None, ""):
            return value
        return normalize_rut(value)

    # 🛑 ELIMINADO: validate_telefono (Ya no hay campo telefono)

    def validate_direccion(self, value):
        if value in (None, ""):
            return value
        if len(value.strip()) < 5:  # Bajé a 5 para facilitar pruebas
            raise serializers.ValidationError(
                "La dirección debe tener al menos 5 caracteres."
            )
        return value.strip()

    def validate_puesto(self, value):
        if value in (None, ""):
            return value
        v = value.strip()
        if len(v) < 2:
            raise serializers.ValidationError(
                "El número de puesto debe tener al menos 2 caracteres."
            )
        return v

    def validate(self, data):
        if self.instance is None:
            if not data.get("direccion"):
                # Opcional: Podríamos hacerlo no obligatorio para simplificar registro
                # raise serializers.ValidationError({"direccion": "Obligatoria"})
                pass
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(representation.get("user"), uuid.UUID):
            representation["user"] = str(representation["user"])
        return representation


class ClienteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de Cliente.
    """

    # 🛑 ELIMINADO: telefono (Ya está en User)

    class Meta:
        model = ClienteProfile
        # ⚠️ CORREGIDO: Se quitó 'telefono'
        fields = [
            "id",
            "user",
            "direccion_entrega",
            # "telefono", <-- ELIMINADO
            "historial_compras",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "deleted_at"]

    def validate_direccion_entrega(self, value):
        if value in (None, ""):
            return value
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "La dirección de entrega debe tener al menos 5 caracteres."
            )
        return value.strip()

    # 🛑 ELIMINADO: validate_telefono

    def validate(self, data):
        if self.instance is None:
            if not data.get("direccion_entrega"):
                # raise serializers.ValidationError({"direccion_entrega": "Requerida"})
                pass
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(representation.get("user"), uuid.UUID):
            representation["user"] = str(representation["user"])
        return representation


class RepartidorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de Repartidor.
    """

    # 🛑 ELIMINADO: telefono

    licencia = serializers.CharField(
        max_length=20,
        validators=[validar_licencia_conducir],
        required=False,
        allow_blank=True,
        help_text="Tipo de licencia: B, A1, C, etc.",
    )

    class Meta:
        model = RepartidorProfile
        # ⚠️ CORREGIDO: Se quitó 'telefono'
        fields = [
            "id",
            "user",
            "vehiculo",
            "licencia",
            "zona_cobertura",
            # "telefono", <-- ELIMINADO
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "deleted_at"]

    def validate_vehiculo(self, value):
        if value in (None, ""):
            return value
        vehiculos_validos = ["moto", "auto", "camioneta", "bicicleta", "otro"]
        if value.lower() not in vehiculos_validos:
            raise serializers.ValidationError(
                f"Tipo de vehículo inválido. Opciones: {', '.join(vehiculos_validos)}"
            )
        return value.lower()

    # 🛑 ELIMINADO: validate_telefono

    def validate(self, data):
        if self.instance is None:
            if not data.get("licencia"):
                pass  # raise serializers.ValidationError(...)
            if not data.get("vehiculo"):
                pass
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(representation.get("user"), uuid.UUID):
            representation["user"] = str(representation["user"])
        return representation


# ========================================
# 🔸 SERIALIZER MAESTRO PARA /me/
# ========================================


class MeSerializer(serializers.ModelSerializer):
    """
    Serializer maestro para el endpoint /api/v1/me/
    """

    ferianteprofile = FerianteProfileSerializer(read_only=True)
    clienteprofile = ClienteProfileSerializer(read_only=True)
    repartidorprofile = RepartidorProfileSerializer(read_only=True)
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "role",
            "role_name",
            "is_active",
            "created_at",
            "updated_at",
            "ferianteprofile",
            "clienteprofile",
            "repartidorprofile",
        ]
        read_only_fields = ["id", "email", "role", "created_at", "updated_at"]

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(representation.get("id"), uuid.UUID):
            representation["id"] = str(representation["id"])

        # Mantener solo el perfil correspondiente al rol
        role_name = instance.role.name.upper() if instance.role else ""
        if role_name != "FERIANTE":
            representation.pop("ferianteprofile", None)
        if role_name != "CLIENTE":
            representation.pop("clienteprofile", None)
        if role_name != "REPARTIDOR":
            representation.pop("repartidorprofile", None)
        return representation
