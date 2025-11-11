from django.utils import timezone
from users.models import User

def create_user_with_role(email, password, full_name, role):
    """Crea un nuevo usuario y asigna un rol específico."""
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        role=role,
    )
    user.is_verified = True  # TODO: activar verificación real por correo
    user.save()
    return user