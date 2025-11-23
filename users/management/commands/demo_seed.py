# users/management/commands/demo_seed.py
import random
import uuid
from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


def has_field(Model, name):
    try:
        Model._meta.get_field(name)
        return True
    except Exception:
        return False


def pick_name_field(Model, candidates):
    for c in candidates:
        try:
            Model._meta.get_field(c)
            return c
        except Exception:
            continue
    return None


class Command(BaseCommand):
    help = "Crea datos demo: roles, usuarios, ferias, puestos, productos y órdenes (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        Role = apps.get_model("users", "Role")

        Feria = (
            apps.get_model("market", "Feria") if apps.is_installed("market") else None
        )
        Puesto = (
            apps.get_model("market", "Puesto") if apps.is_installed("market") else None
        )
        Producto = (
            apps.get_model("market", "Producto")
            if apps.is_installed("market")
            else None
        )
        Order = (
            apps.get_model("orders", "Order") if apps.is_installed("orders") else None
        )
        OrderItem = (
            apps.get_model("orders", "OrderItem")
            if apps.is_installed("orders")
            else None
        )
        Payment = (
            apps.get_model("orders", "Payment") if apps.is_installed("orders") else None
        )

        # 1) Roles
        self.stdout.write("Asegurando roles base...")
        roles = {}
        for name, desc in [
            ("ADMIN", "Administrador"),
            ("FERIANTE", "Feriante"),
            ("CLIENTE", "Cliente"),
            ("REPARTIDOR", "Repartidor"),
        ]:
            if Role:
                r, created = Role.objects.get_or_create(
                    name=name,
                    defaults=(
                        {"description": desc} if has_field(Role, "description") else {}
                    ),
                )
                roles[name] = r
                self.stdout.write(
                    f" - {name} {'(creado)' if created else '(ya existe)'}"
                )
            else:
                self.stdout.write(
                    self.style.WARNING("Role model no encontrado; saltando roles.")
                )

        # 2) Usuarios base (usar update_or_create para asegurar role en defaults)
        self.stdout.write("Creando/asegurando usuarios demo...")
        pw_admin = "adminpass"
        admin_defaults = {
            "full_name": "Admin Demo",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }
        if roles.get("ADMIN"):
            admin_defaults["role"] = roles.get("ADMIN")
        admin, _ = User.objects.update_or_create(
            email="admin@example.com", defaults=admin_defaults
        )
        admin.set_password(pw_admin)
        admin.save()

        feriantes = []
        for i in range(1, 4):
            e = f"feriante{i}@example.com"
            defaults = {"full_name": f"Feriante {i}", "is_active": True}
            if roles.get("FERIANTE"):
                defaults["role"] = roles.get("FERIANTE")
            u, _ = User.objects.update_or_create(email=e, defaults=defaults)
            u.set_password("feriantepass")
            u.save()
            feriantes.append(u)

        clientes = []
        for i in range(1, 4):
            e = f"cliente{i}@example.com"
            defaults = {"full_name": f"Cliente {i}", "is_active": True}
            if roles.get("CLIENTE"):
                defaults["role"] = roles.get("CLIENTE")
            u, _ = User.objects.update_or_create(email=e, defaults=defaults)
            u.set_password("clientepass")
            u.save()
            clientes.append(u)

        repartidores = []
        for i in range(1, 3):
            e = f"repartidor{i}@example.com"
            defaults = {"full_name": f"Repartidor {i}", "is_active": True}
            if roles.get("REPARTIDOR"):
                defaults["role"] = roles.get("REPARTIDOR")
            u, _ = User.objects.update_or_create(email=e, defaults=defaults)
            u.set_password("repartidorpass")
            u.save()
            repartidores.append(u)

        # 3) Ferias / Puestos / Productos
        if Feria and Puesto and Producto:
            self.stdout.write("Creando Feria/Puestos/Productos demo...")
            # intentar detectar name field
            feria_name_field = pick_name_field(Feria, ["name", "nombre"])
            if feria_name_field:
                feria, _ = Feria.objects.get_or_create(
                    **{feria_name_field: "Feria Central"}
                )
            else:
                feria, _ = Feria.objects.get_or_create(pk=1)

            prod_created = 0
            for idx, fuser in enumerate(feriantes, start=1):
                puesto_kwargs = {}
                nombre_field = pick_name_field(Puesto, ["name", "nombre"])
                numero_field = pick_name_field(Puesto, ["numero", "number"])
                if nombre_field:
                    puesto_kwargs[nombre_field] = f"Puesto {idx}"
                if numero_field:
                    puesto_kwargs[numero_field] = idx
                if has_field(Puesto, "feria"):
                    puesto_kwargs["feria"] = feria
                if has_field(Puesto, "feriante"):
                    puesto_kwargs["feriante"] = fuser
                # crear puesto solo con campos válidos del modelo
                allowed = {f.name for f in Puesto._meta.fields}
                create_kwargs = {k: v for k, v in puesto_kwargs.items() if k in allowed}
                puesto, _ = Puesto.objects.get_or_create(**create_kwargs)
                # crear productos
                name_field = pick_name_field(Producto, ["name", "nombre"])
                desc_field = pick_name_field(Producto, ["description", "descripcion"])
                price_field = pick_name_field(Producto, ["price", "precio"])
                stock_field = pick_name_field(
                    Producto, ["stock", "cantidad", "stock_available"]
                )
                for j in range(1, 4):
                    kwargs = {}
                    if name_field:
                        kwargs[name_field] = f"Producto {idx}-{j}"
                    if desc_field:
                        kwargs[desc_field] = "Producto demo"
                    if price_field:
                        kwargs[price_field] = Decimal(random.randint(1000, 5000))
                    if stock_field:
                        kwargs[stock_field] = random.randint(5, 30)
                    if has_field(Producto, "puesto"):
                        kwargs["puesto"] = puesto
                    allowed_p = {f.name for f in Producto._meta.fields}
                    try:
                        obj, created = Producto.objects.get_or_create(
                            **{k: v for k, v in kwargs.items() if k in allowed_p}
                        )
                        if created:
                            prod_created += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"Error creando producto {idx}-{j}: {e}")
                        )
            self.stdout.write(
                self.style.SUCCESS(f"Productos creados (aprox): {prod_created}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Modelos Feria/Puesto/Producto no encontrados; saltando catálogo."
                )
            )

        # 4) Órdenes demo
        if Order and OrderItem and Producto:
            self.stdout.write("Creando órdenes demo...")
            cliente_field = pick_name_field(
                Order, ["usuario_cliente", "cliente", "user", "customer"]
            )
            monto_field = pick_name_field(Order, ["monto_total", "total", "amount"])
            estado_field = pick_name_field(Order, ["estado", "status"])
            productos_qs = list(Producto.objects.all())
            created_orders = 0
            for k, cliente in enumerate(clientes, start=1):
                order_kwargs = {}
                if cliente_field:
                    order_kwargs[cliente_field] = cliente
                if estado_field:
                    order_kwargs[estado_field] = "CREADO"
                if monto_field:
                    order_kwargs[monto_field] = 0
                try:
                    order = Order.objects.create(
                        **{
                            k: v
                            for k, v in order_kwargs.items()
                            if k in [f.name for f in Order._meta.fields]
                        }
                    )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error creando Order: {e}"))
                    continue
                total = Decimal("0")
                for p in productos_qs[(k - 1) * 2 : ((k - 1) * 2) + 2]:
                    prod_field = pick_name_field(
                        OrderItem, ["product", "producto", "item"]
                    )
                    qty_field = pick_name_field(
                        OrderItem, ["cantidad", "quantity", "qty"]
                    )
                    subtotal_field = pick_name_field(
                        OrderItem, ["subtotal", "sub_total"]
                    )
                    item_kwargs = {}
                    if prod_field:
                        item_kwargs[prod_field] = p
                    if qty_field:
                        item_kwargs[qty_field] = 1
                    if subtotal_field:
                        price_attr = (
                            pick_name_field(p.__class__, ["price", "precio"]) or "price"
                        )
                        price_val = getattr(p, price_attr, Decimal("1000"))
                        item_kwargs[subtotal_field] = price_val * 1
                    if has_field(OrderItem, "order"):
                        item_kwargs["order"] = order
                    try:
                        OrderItem.objects.create(
                            **{
                                k: v
                                for k, v in item_kwargs.items()
                                if k in [f.name for f in OrderItem._meta.fields]
                            }
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"Error creando OrderItem: {e}")
                        )
                    total += Decimal(item_kwargs.get(subtotal_field, Decimal("0")))
                if monto_field and hasattr(order, monto_field):
                    setattr(order, monto_field, total)
                    order.save()
                created_orders += 1
            self.stdout.write(
                self.style.SUCCESS(f"Órdenes demo creadas: {created_orders}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Modelos Order/OrderItem/Producto no encontrados; saltando órdenes."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "demo_seed finalizado. Usuarios demo: admin/feriante*/cliente*/repartidor* (pass en código)."
            )
        )
