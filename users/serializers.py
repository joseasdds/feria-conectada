# users/serializers.py
from rest_framework import serializers
from .models import User, Role


class RoleSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Role."""
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User."""
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'is_active',
            'is_staff',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']