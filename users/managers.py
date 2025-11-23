from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Administrador personalizado del modelo User."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        role_model = self.model.role.field.related_model
        admin_role, _ = role_model.objects.get_or_create(name="ADMIN")
        extra_fields["role"] = admin_role

        return self.create_user(email, password, **extra_fields)
