from rest_framework import serializers
from .models import User, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description"]


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True
    )

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone", "role", "role_id",
            "is_verified", "created_at"
        ]
        read_only_fields = ["id", "created_at", "is_verified"]