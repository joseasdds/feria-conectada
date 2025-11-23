from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed initial roles: ADMIN, FERIANTE, CLIENTE, REPARTIDOR"

    def handle(self, *args, **options):
        try:
            # Import aquí para asegurar que Django ya cargó las apps
            from users.models import Role
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    "No se pudo importar users.models.Role. Verifica que exista el modelo Role. Error: %s"
                    % e
                )
            )
            return

        roles = [
            ("ADMIN", "Administrador del sistema"),
            ("FERIANTE", "Usuario Feriante"),
            ("CLIENTE", "Usuario Cliente"),
            ("REPARTIDOR", "Usuario Repartidor"),
        ]

        created = 0
        with transaction.atomic():
            for name, desc in roles:
                obj, was_created = Role.objects.get_or_create(
                    name=name,
                    defaults=(
                        {"description": desc} if hasattr(Role, "description") else {}
                    ),
                )
                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"Creado rol: {name}"))
                else:
                    self.stdout.write(self.style.NOTICE(f"Ya existe: {name}"))

        self.stdout.write(
            self.style.SUCCESS(f"Seed completo. Roles creados: {created}")
        )
