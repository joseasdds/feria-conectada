# delivery/tests/test_api.py
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

# imports locales (se importan dentro de funciones si hay riesgo de import-time issues)
from delivery.models import DeliveryAssignment  # asume que existe
from users.models import Role  # ajustar si la ruta es otra


def create_sample_order(cliente_user=None, **overrides):
    """
    Helper best-effort para crear una Order válida en tests.
    Intenta rellenar automáticamente campos obligatorios inspeccionando el modelo.
    """
    from orders.models import Order

    defaults = {}
    model_fields = [
        f for f in Order._meta.get_fields() if not (f.many_to_many or f.one_to_many)
    ]

    for field in model_fields:
        if getattr(field, "auto_created", False) or getattr(
            field, "primary_key", False
        ):
            continue

        name = field.name
        if name in overrides:
            defaults[name] = overrides[name]
            continue

        default = getattr(field, "default", None)
        if (
            default not in (None, getattr(field, "default", None))
            and default is not None
        ):
            defaults[name] = default() if callable(default) else default
            continue

        if getattr(field, "is_relation", False) and getattr(
            field, "related_model", None
        ):
            rel_model = field.related_model
            if rel_model == User:
                if cliente_user is not None:
                    defaults[name] = cliente_user
                else:
                    u = User.objects.create(
                        email=f"u_{uuid.uuid4().hex[:6]}@test.local", is_active=True
                    )
                    u.set_password("pass123")
                    u.save()
                    defaults[name] = u
            else:
                try:
                    inst = rel_model.objects.first()
                    if inst:
                        defaults[name] = inst
                    else:
                        defaults[name] = None
                except Exception:
                    defaults[name] = None
            continue

        field_type = field.get_internal_type()
        if field_type in ("CharField", "TextField"):
            defaults[name] = f"sample_{name}"
        elif field_type in (
            "IntegerField",
            "PositiveIntegerField",
            "SmallIntegerField",
            "BigIntegerField",
        ):
            defaults[name] = 1
        elif field_type in ("DecimalField", "FloatField"):
            defaults[name] = Decimal("10.0")
        elif field_type in ("BooleanField",):
            defaults[name] = False
        elif field_type in ("DateTimeField",):
            defaults[name] = timezone.now()
        elif field_type in ("DateField",):
            defaults[name] = timezone.now().date()
        elif field_type in ("UUIDField",):
            defaults[name] = uuid.uuid4()
        else:
            defaults[name] = None

    # Intentar asignar cliente si hay un campo típico
    for candidate in ("cliente", "cliente_user", "customer", "user", "owner"):
        if candidate in [f.name for f in model_fields]:
            if cliente_user is not None:
                defaults[candidate] = cliente_user
            break

    defaults.update(overrides)

    final_kwargs = {}
    for name, value in defaults.items():
        try:
            f = Order._meta.get_field(name)
        except Exception:
            continue
        if value is None and not (
            getattr(f, "null", False) or getattr(f, "blank", False)
        ):
            # omitimos para forzar fallo claro que muestre qué falta
            continue
        final_kwargs[name] = value

    return Order.objects.create(**final_kwargs)


class DeliveryAPITests(APITestCase):
    def setUp(self):
        # Crear/obtener roles
        role_repartidor, _ = Role.objects.get_or_create(name="repartidor")
        role_cliente, _ = Role.objects.get_or_create(name="cliente")

        # Crear repartidor (crear con .create + set_password para evitar manager custom)
        self.repartidor = User.objects.create(
            email="r@test.local",
            role=role_repartidor,
            is_active=True,
        )
        self.repartidor.set_password("pass123")
        self.repartidor.save()

        # Crear cliente
        self.cliente = User.objects.create(
            email="c@test.local",
            role=role_cliente,
            is_active=True,
        )
        self.cliente.set_password("pass123")
        self.cliente.save()

        # Crear una orden válida (el helper intentará rellenar lo necesario)
        self.order = create_sample_order(self.cliente)

        # Crear assignment (sin repartidor inicialmente)
        self.assignment = DeliveryAssignment.objects.create(order=self.order)

    def test_mias_empty_for_unassigned(self):
        # Ajusta el nombre de la ruta si lo tienes distinto
        # reverse('my-deliveries-list') es un ejemplo; cambia si tu urls usan otro name
        self.client.force_authenticate(user=self.repartidor)
        try:
            url = reverse("my-deliveries-list")
        except Exception:
            # fallback: usa endpoint directo si no tienes named url
            url = "/api/delivery/my-deliveries/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)

    def test_claim_assignment(self):
        # Prints diagnósticos para entender por qué IsRepartidor puede devolver False
        print("USER AUTHENTICATED:", getattr(self.repartidor, "is_authenticated", None))
        print(
            "USER ROLE NAME:",
            getattr(getattr(self.repartidor, "role", None), "name", None),
        )
        # comprobar varios nombres posibles de profile
        print("HAS delivery_profile:", hasattr(self.repartidor, "delivery_profile"))
        print("HAS deliveryprofile:", hasattr(self.repartidor, "deliveryprofile"))
        print("HAS repartidor_profile:", hasattr(self.repartidor, "repartidor_profile"))
        print("HAS repartidorprofile:", hasattr(self.repartidor, "repartidorprofile"))
        print("HAS profile:", hasattr(self.repartidor, "profile"))

        self.client.force_authenticate(user=self.repartidor)
        try:
            claim_url = reverse(
                "delivery-assignment-claim", args=[str(self.assignment.pk)]
            )
        except Exception:
            claim_url = f"/api/delivery/assignments/{self.assignment.pk}/claim/"

        resp = self.client.post(claim_url)

        # Imprime status y body para diagnosticar por qué devuelve 403
        body = None
        try:
            body = resp.data
        except Exception:
            try:
                body = resp.content.decode()
            except Exception:
                body = repr(resp)

        print("CLAIM RESPONSE:", resp.status_code, body)

        # Asserción informativa: si falla veremos el contenido en el mensaje
        self.assertIn(
            resp.status_code,
            (status.HTTP_200_OK, status.HTTP_202_ACCEPTED),
            msg=f"Expected 200/202 but got {resp.status_code}. Body: {body}",
        )

        self.assignment.refresh_from_db()
        self.assertEqual(
            getattr(
                self.assignment, "estado", getattr(self.assignment, "status", None)
            ),
            getattr(DeliveryAssignment, "STATE_ASSIGNED", "assigned"),
        )
        self.assertEqual(self.assignment.repartidor_id, self.repartidor.id)

    def test_mark_delivered(self):
        self.client.force_authenticate(user=self.repartidor)

        # Primero reclamar
        try:
            claim_url = reverse(
                "delivery-assignment-claim", args=[str(self.assignment.pk)]
            )
        except Exception:
            claim_url = f"/api/delivery/assignments/{self.assignment.pk}/claim/"

        resp = self.client.post(claim_url)

        # Imprimir respuesta para diagnosticar si falla
        body = None
        try:
            body = resp.data
        except Exception:
            try:
                body = resp.content.decode()
            except Exception:
                body = repr(resp)

        print("CLAIM (before mark_delivered):", resp.status_code, body)

        self.assertIn(
            resp.status_code,
            (status.HTTP_200_OK, status.HTTP_202_ACCEPTED),
            msg=f"Claim failed. Expected 200/202 but got {resp.status_code}. Body: {body}",
        )

        # Ahora marcar como entregado
        try:
            mark_url = reverse(
                "delivery-assignment-mark-delivered", args=[str(self.assignment.pk)]
            )
        except Exception:
            mark_url = f"/api/delivery/assignments/{self.assignment.pk}/mark-delivered/"

        resp = self.client.post(mark_url)

        # Imprimir respuesta para diagnosticar si falla
        body = None
        try:
            body = resp.data
        except Exception:
            try:
                body = resp.content.decode()
            except Exception:
                body = repr(resp)

        print("MARK DELIVERED RESPONSE:", resp.status_code, body)

        self.assertIn(
            resp.status_code,
            (status.HTTP_200_OK, status.HTTP_202_ACCEPTED),
            msg=f"Mark delivered failed. Expected 200/202 but got {resp.status_code}. Body: {body}",
        )

        self.assignment.refresh_from_db()
        self.assertEqual(
            getattr(
                self.assignment, "estado", getattr(self.assignment, "status", None)
            ),
            getattr(DeliveryAssignment, "STATE_DELIVERED", "delivered"),
        )
