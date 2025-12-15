from django.apps import apps
from rest_framework import serializers

from .models import Role, User
# Importamos los perfiles corregidos del archivo anterior
from .serializers_profiles import (ClienteProfileSerializer,
                                   FerianteProfileSerializer,
                                   RepartidorProfileSerializer)

# --- 1. Serializer de Roles ---


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name"]


# --- 2. Serializer de REGISTRO ---


class RegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=255, required=True)
    # El teléfono se guarda en el User, no en el Profile
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


# --- 3. Serializer de USUARIO (/me/) ---


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "role",
            "profile",
            "is_active",
            "is_staff",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "created_at", "updated_at"]

    def get_profile(self, obj):
        """Devuelve el serializer correcto para el perfil basado en el rol."""
        if not obj.role:
            return None

        role_name = obj.role.name.lower()

        # Aquí usamos los serializers corregidos que NO tienen el campo telefono
        if role_name == "cliente":
            return ClienteProfileSerializer(getattr(obj, "clienteprofile", None)).data
        elif role_name == "feriante":
            return FerianteProfileSerializer(getattr(obj, "ferianteprofile", None)).data
        elif role_name == "repartidor":
            return RepartidorProfileSerializer(
                getattr(obj, "repartidorprofile", None)
            ).data

        return None
