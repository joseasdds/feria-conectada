# users/serializers.py

from django.apps import apps
from rest_framework import serializers

from .models import (  # Asegúrate de que todos los perfiles están aquí
    ClienteProfile, FerianteProfile, RepartidorProfile, Role, User)

# --- 1. Serializers de Perfiles (para anidamiento en /me/) ---


class ClienteProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de Cliente."""

    class Meta:
        model = ClienteProfile
        fields = (
            "id",
            "direccion_entrega",
            "historial_compras",
        )  # Ajusta estos campos si es necesario


class FerianteProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de Feriante."""

    class Meta:
        model = FerianteProfile
        fields = (
            "id",
            "puesto",
            "rut",
            "direccion",
            "telefono",
        )  # Ajusta estos campos si es necesario


class RepartidorProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de Repartidor."""

    class Meta:
        model = RepartidorProfile
        fields = ("id", "licencia", "vehiculo")  # Ajusta estos campos si es necesario


# --- 2. Serializer de Roles ---


class RoleSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Role (Lectura)."""

    class Meta:
        model = Role
        fields = ["id", "name"]


# --- 3. Serializer de REGISTRO (Creación de Usuario) ---


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializador para el registro público. Asigna 'cliente' por defecto."""

    full_name = serializers.CharField(max_length=255, required=True)
    phone = serializers.CharField(max_length=20, required=False)
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ("email", "password", "full_name", "phone", "role")
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
        }

    def create(self, validated_data):
        role = validated_data.pop("role", None)
        password = validated_data.pop("password", None)

        # LÓGICA CLAVE: Asignar 'cliente' si el rol es nulo
        if role is None:
            RoleModel = apps.get_model("users", "Role")
            try:
                role = RoleModel.objects.get(name__iexact="cliente")
            except RoleModel.DoesNotExist:
                raise serializers.ValidationError(
                    {"role": "Role 'cliente' no encontrado."}
                )

        user = User(**validated_data)
        user.role = role
        if password:
            user.set_password(password)

        user.save()
        return user


# --- 4. Serializer de USUARIO (Lectura / Endpoint /me/) ---


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User. Anida el objeto Role y el Profile."""

    role = RoleSerializer(read_only=True)

    # Campo dinámico para devolver el perfil correcto (Cliente, Feriante, etc.)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "role",  # Objeto Role anidado
            "profile",  # Objeto de Perfil anidado
            "is_active",
            "is_staff",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "created_at", "updated_at"]

    def get_profile(self, obj):
        """Devuelve el serializer correcto para el perfil basado en el rol del usuario."""
        role_name = obj.role.name.lower() if obj.role else None

        # Mapeo y acceso a la relación OneToOne (atributo en minúsculas)
        if role_name == "cliente":
            return ClienteProfileSerializer(getattr(obj, "clienteprofile", None)).data
        elif role_name == "feriante":
            return FerianteProfileSerializer(getattr(obj, "ferianteprofile", None)).data
        elif role_name == "repartidor":
            return RepartidorProfileSerializer(
                getattr(obj, "repartidorprofile", None)
            ).data

        return None
