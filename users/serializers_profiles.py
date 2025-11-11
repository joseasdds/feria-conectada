# users/serializers_profiles.py
import re
import uuid
from rest_framework import serializers
from .models_profiles import FerianteProfile, ClienteProfile, RepartidorProfile


# ========================================
# 🔹 VALIDADORES ESPECÍFICOS
# ========================================

def validar_rut_chileno(value):
    """
    Valida el formato básico de un RUT chileno.
    Formato esperado: 12345678-9 o 1234567-K
    """
    if not value:  # Permitir vacío si el campo no es obligatorio
        return value
    
    pattern = r"^\d{7,8}-[\dkK]$"
    if not re.match(pattern, value):
        raise serializers.ValidationError(
            "Formato de RUT inválido. Use el formato: 12345678-9 o 1234567-K"
        )
    return value


def validar_uuid(value):
    """
    Valida que el valor sea un UUID válido.
    Usado para feria_asignada (temporal hasta Fase 2).
    """
    if not value:  # Permitir vacío
        return value
    
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError):
        raise serializers.ValidationError("El campo debe ser un UUID válido.")
    
    return value


def validar_telefono_chileno(value):
    """
    Valida formato de teléfono chileno.
    Acepta: +56912345678, 912345678, +569 1234 5678
    """
    if not value:
        return value
    
    # Eliminar espacios y guiones para validación
    telefono_limpio = re.sub(r"[\s\-]", "", value)
    
    # Patrones aceptados
    pattern = r"^(\+?56)?[9]\d{8}$"
    if not re.match(pattern, telefono_limpio):
        raise serializers.ValidationError(
            "Formato de teléfono inválido. Use: +56912345678 o 912345678"
        )
    return value


def validar_licencia_conducir(value):
    """
    Valida formato de licencia de conducir chilena.
    Formato: A1, A2, B, C, D, E, F (puede ser combinado: A1-B)
    """
    if not value:
        return value
    
    pattern = r"^[A-F][1-2]?(-[A-F][1-2]?)*$"
    if not re.match(pattern, value.upper()):
        raise serializers.ValidationError(
            "Formato de licencia inválido. Ejemplos válidos: B, A1, A1-B, C-D"
        )
    return value.upper()


# ========================================
# 🔸 SERIALIZERS POR PERFIL
# ========================================

class FerianteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil de Feriante (vendedor).
    Incluye validaciones de RUT, teléfono y dirección.
    """
    rut = serializers.CharField(
        max_length=12,
        validators=[validar_rut_chileno],
        required=False,
        allow_blank=True,
        help_text="RUT chileno en formato 12345678-9"
    )
    
    feria_asignada = serializers.UUIDField(
        validators=[validar_uuid],
        required=False,
        allow_null=True,
        help_text="UUID de la feria asignada (temporal hasta Fase 2)"
    )
    
    telefono = serializers.CharField(
        max_length=20,
        validators=[validar_telefono_chileno],
        required=False,
        allow_blank=True,
        help_text="Teléfono en formato +56912345678"
    )

    class Meta:
        model = FerianteProfile
        fields = [
            'id',
            'user',
            'rut',
            'direccion',
            'telefono',
            'puesto',
            'feria_asignada',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'deleted_at']

    def validate_direccion(self, value):
        """Valida que la dirección tenga al menos 10 caracteres."""
        if value is None:
            return value  # ✅ Permitir PATCH sin dirección
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "La dirección debe tener al menos 10 caracteres."
            )
        return value.strip()

    def validate_puesto(self, value):
        """Valida formato de puesto (ej: A-12, B-5, Local 23)."""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError(
                "El número de puesto debe tener al menos 2 caracteres."
            )
        return value.strip() if value else value

    def validate(self, data):
        """
        Validaciones a nivel de objeto completo.
        Refuerza reglas de negocio específicas.
        """
        # Si se actualiza, no requerir dirección obligatoria (PATCH permite parcial)
        # Pero si se crea, sí validar
        if self.instance is None:  # Creación
            if not data.get("direccion"):
                raise serializers.ValidationError({
                    "direccion": "La dirección es obligatoria al crear el perfil."
                })
        
        return data

    def to_representation(self, instance):
        """
        ✅ Convierte el campo 'user' (UUID) a string para consistencia en tests y API.
        """
        representation = super().to_representation(instance)
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
        help_text="Teléfono en formato +56912345678"
    )

    class Meta:
        model = ClienteProfile
        fields = [
            'id',
            'user',
            'direccion_entrega',
            'telefono',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'deleted_at']

    def validate_direccion_entrega(self, value):
        """Valida que la dirección de entrega tenga al menos 10 caracteres."""
        if value is None:
            return value  # ✅ Permitir PATCH sin dirección
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "La dirección de entrega debe tener al menos 10 caracteres."
            )
        return value.strip()

    def validate(self, data):
        """Validaciones a nivel de objeto completo."""
        if self.instance is None:  # Creación
            if not data.get("direccion_entrega"):
                raise serializers.ValidationError({
                    "direccion_entrega": "Debe ingresar una dirección de entrega válida."
                })
        return data

    def to_representation(self, instance):
        """Convierte el campo 'user' UUID → string."""
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
        help_text="Teléfono en formato +56912345678"
    )
    
    licencia = serializers.CharField(
        max_length=20,
        validators=[validar_licencia_conducir],
        required=False,
        allow_blank=True,
        help_text="Tipo de licencia: B, A1, C, etc."
    )

    class Meta:
        model = RepartidorProfile
        fields = [
            'id',
            'user',
            'vehiculo',
            'licencia',
            'telefono',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'deleted_at']

    def validate_vehiculo(self, value):
        """Valida que el tipo de vehículo sea válido."""
        vehiculos_validos = ['moto', 'auto', 'camioneta', 'bicicleta', 'otro']
        if value and value.lower() not in vehiculos_validos:
            raise serializers.ValidationError(
                f"Tipo de vehículo inválido. Opciones: {', '.join(vehiculos_validos)}"
            )
        return value.lower() if value else value

    def validate(self, data):
        """Validaciones de negocio."""
        if self.instance is None:  # Creación
            if not data.get("licencia"):
                raise serializers.ValidationError({
                    "licencia": "Debe registrar su número de licencia de conducir."
                })
            if not data.get("vehiculo"):
                raise serializers.ValidationError({
                    "vehiculo": "Debe especificar el tipo de vehículo."
                })
        return data

    def to_representation(self, instance):
        """Convierte el campo 'user' UUID → string."""
        representation = super().to_representation(instance)
        if isinstance(representation.get("user"), uuid.UUID):
            representation["user"] = str(representation["user"])
        return representation