# users/management/commands/seed_initial.py
import os
from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Asegura roles base y crea/actualiza superuser + usuarios de ejemplo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-email",
            type=str,
            default=os.getenv("ADMIN_EMAIL", "admin@local.test"),
        )
        parser.add_argument(
            "--admin-password", type=str, default=os.getenv("ADMIN_PASSWORD", None)
        )
        parser.add_argument("--create-samples", action="store_true")
        parser.add_argument("--skip-if-exists", action="store_true")

    def handle(self, *args, **options):
        from users.models import Role

        admin_email = options["admin_email"]
        admin_password = options["admin_password"]
        create_samples = options["create_samples"]
        skip_if_exists = options["skip_if_exists"]

        roles_def = [
            ("ADMIN", "Administrador"),
            ("FERIANTE", "Feriante"),
            ("CLIENTE", "Cliente"),
            ("REPARTIDOR", "Repartidor"),
        ]

        with transaction.atomic():
            for name, desc in roles_def:
                Role.objects.get_or_create(name=name, defaults={"description": desc})
        self.stdout.write(self.style.SUCCESS("Roles base asegurados."))

        admin_role = Role.objects.get(name="ADMIN")

        if not admin_password:
            admin_password = getpass(f"Password para superusuario ({admin_email}): ")
            if not admin_password:
                self.stderr.write("Password vacía. Abortando.")
                return

        admin = User.objects.filter(email=admin_email).first()
        if admin and skip_if_exists:
            self.stdout.write(
                self.style.WARNING("Superusuario existe, --skip-if-exists usado.")
            )
        else:
            if not admin:
                # Intentamos create_user (si manager lo soporta)
                try:
                    admin = User.objects.create_user(
                        email=admin_email, password=admin_password
                    )
                except Exception:
                    admin = User(
                        email=admin_email,
                        full_name="Admin",
                        role=admin_role,
                        is_staff=True,
                        is_active=True,
                        is_superuser=True,
                    )
                    admin.set_password(admin_password)
                    admin.save()
            # Asegurar flags y rol
            admin.role = admin_role
            admin.is_active = True
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password(admin_password)
            admin.save()
            self.stdout.write(
                self.style.SUCCESS(f"Superuser creado/actualizado: {admin_email}")
            )

        if create_samples:
            sample_pw = os.getenv("SAMPLE_PW", "test1234")
            samples = [
                ("feriante@test.local", "Feriante Demo", "FERIANTE"),
                ("cliente@test.local", "Cliente Demo", "CLIENTE"),
                ("repartidor@test.local", "Repartidor Demo", "REPARTIDOR"),
            ]
            for email, name, role_name in samples:
                role = Role.objects.get(name=role_name)
                u = User.objects.filter(email=email).first()
                if u and skip_if_exists:
                    self.stdout.write(
                        self.style.WARNING(f"Usuario {email} existe, skip.")
                    )
                    continue
                if not u:
                    u = User(email=email, full_name=name, role=role, is_active=True)
                u.set_password(sample_pw)
                u.is_staff = False
                u.is_superuser = False
                u.role = role
                u.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Usuario creado/actualizado: {email} (role={role_name})"
                    )
                )
