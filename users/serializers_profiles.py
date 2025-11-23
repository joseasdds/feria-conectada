# users/serializers_profiles.py
import re
import uuid

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models_profiles import ClienteProfile, FerianteProfile, RepartidorProfile
# Utilidades para RUT (asegúrate de crear users/utils.py con estas funciones)
from .utils import normalize_rut, validate_rut

User = get_user_model()


# ========================================
# 🔹 VALIDADORES ESPECÍFICOS (DRF)
# ========================================


def validar_rut_chileno(value):
    """
    Validador DRF para RUT chileno.
    - Acepta formatos con o sin puntos/guion.
    - Normaliza y valida el dígito verificador (DV) usando utils.validate_rut.
    - Si value es blank/None y el campo permite blank, no lanza error.
    """
    if value in (None, ""):
        return value

    norm = normalize_rut(value)
    if not norm:
        raise serializers.ValidationError("RUT vacío o en formato no soportado.")
    if not validate_rut(norm):
        raise serializers.ValidationError("RUT inválido (DV no coincide).")
    return value  # la normalización se aplica en validate_rut del serializer


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
    Acepta formas con prefijo +56 o sin él; valida número móvil (9xxxxxxxx).
    No modifica el valor; la normalización se hace en validate_telefono del serializer.
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
    Valida formato de licencia de conducir chilena (A-F, opcional número).
    Retorna value en mayúsculas si es válido.
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
    Incluye validaciones de RUT, teléfono y dirección. Normaliza RUT antes de guardar.
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
        help_text="UUID de la feria asignada (temporal hasta Fase 2)",
    )

    telefono = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Teléfono en formato +56912345678",
    )

    class Meta:
        model = FerianteProfile
        fields = [
            "id",
            "user",
            "rut",
            "direccion",
            "telefono",
            "puesto",
            "feria_asignada",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "deleted_at"]

    def validate_rut(self, value):
        """
        Normaliza el RUT antes de guardarlo:
        - Quita puntos y guion, DV en mayúscula.
        - Devuelve string normalizado (ej. '12345678K' o '123456785' según utils).
        """
        if value in (None, ""):
            return value
        return normalize_rut(value)

    def validate_telefono(self, value):
        """
        Normaliza teléfono para almacenamiento: quita espacios y guiones.
        Valida el formato usando validar_telefono_chileno.
        """
        if value in (None, ""):
            return value
        cleaned = re.sub(r"[\s\-()]", "", value)
        # validar
        validar_telefono_chileno(cleaned)
        # almacenar en formato +56 prefijo si viene sin +56 (opcional)
        if cleaned.startswith("9"):
            # transformar a formato +569XXXXXXXX si quieres estándar E.164-lite
            cleaned = f"+56{cleaned}"
        return cleaned

    def validate_direccion(self, value):
        """Valida que la dirección tenga al menos 10 caracteres si se provee."""
        if value in (None, ""):
            return value
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "La dirección debe tener al menos 10 caracteres."
            )
        return value.strip()

    def validate_puesto(self, value):
        """Valida formato de puesto (ej: A-12, B-5, Local 23)."""
        if value in (None, ""):
            return value
        v = value.strip()
        if len(v) < 2:
            raise serializers.ValidationError(
                "El número de puesto debe tener al menos 2 caracteres."
            )
        return v

    def validate(self, data):
        """
        Validaciones a nivel de objeto completo.
        - Si es creación (instance is None), exigir dirección.
        """
        if self.instance is None:
            if not data.get("direccion"):
                raise serializers.ValidationError(
                    {"direccion": "La dirección es obligatoria al crear el perfil."}
                )
        return data

    def to_representation(self, instance):
        """
        Convierte UUIDs a strings y devuelve representación con solo el perfil correspondiente.
        """
        representation = super().to_representation(instance)
        # Convertir user UUID a string si corresponde
        if isinstance(representation.get("user"), uuid.UUID):
            representation["user"] = str(representation["user"])
        return representation


class ClienteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de Cliente (comprador).
    Incluye validaciones de dirección de entrega y teléfono.
    """

    telefono = serializers.CharField(
        max_length=20,
        validators=[validar_telefono_chileno],
        required=False,
        allow_blank=True,
        help_text="Teléfono en formato +56912345678",
    )

    class Meta:
        model = ClienteProfile
        fields = [
            "id",
            "user",
            "direccion_entrega",
            "telefono",
            "historial_compras",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "deleted_at"]

    def validate_direccion_entrega(self, value):
        if value in (None, ""):
            return value
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "La dirección de entrega debe tener al menos 10 caracteres."
            )
        return value.strip()

    def validate_telefono(self, value):
        if value in (None, ""):
            return value
        cleaned = re.sub(r"[\s\-()]", "", value)
        validar_telefono_chileno(cleaned)
        if cleaned.startswith("9"):
            cleaned = f"+56{cleaned}"
        return cleaned

    def validate(self, data):
        if self.instance is None:
            if not data.get("direccion_entrega"):
                raise serializers.ValidationError(
                    {
                        "direccion_entrega": "Debe ingresar una dirección de entrega válida."
                    }
                )
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if isinstance(representation.get("user"), uuid.UUID):
            representation["user"] = str(representation["user"])
        return representation


class RepartidorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de Repartidor (logística).
    Incluye validaciones de licencia, vehículo y teléfono.
    """

    telefono = serializers.CharField(
        max_length=20,
        validators=[validar_telefono_chileno],
        required=False,
        allow_blank=True,
        help_text="Teléfono en formato +56912345678",
    )

    licencia = serializers.CharField(
        max_length=20,
        validators=[validar_licencia_conducir],
        required=False,
        allow_blank=True,
        help_text="Tipo de licencia: B, A1, C, etc.",
    )

    class Meta:
        model = RepartidorProfile
        fields = [
            "id",
            "user",
            "vehiculo",
            "licencia",
            "zona_cobertura",
            "telefono",
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

    def validate_telefono(self, value):
        if value in (None, ""):
            return value
        cleaned = re.sub(r"[\s\-()]", "", value)
        validar_telefono_chileno(cleaned)
        if cleaned.startswith("9"):
            cleaned = f"+56{cleaned}"
        return cleaned

    def validate(self, data):
        if self.instance is None:
            if not data.get("licencia"):
                raise serializers.ValidationError(
                    {"licencia": "Debe registrar su número de licencia de conducir."}
                )
            if not data.get("vehiculo"):
                raise serializers.ValidationError(
                    {"vehiculo": "Debe especificar el tipo de vehículo."}
                )
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
    Devuelve datos del User + perfil asociado según el rol.
    Solo devuelve el perfil que corresponde al rol del usuario.
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
