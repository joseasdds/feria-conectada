# orders/tests/test_payments_webhook.py
import hashlib
import hmac
import json
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from orders.models import ORDER_CONFIRMED, Order, Payment, PaymentLog

WEBHOOK_URL = "/api/v1/payments/webhook/"


def make_sig(secret: str, body: bytes) -> str:
    """Calcula la firma HMAC-SHA256 del cuerpo del payload."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


@override_settings(WEBHOOK_SECRET="testsecret")
class PaymentWebhookTests(TestCase):

    def setUp(self):
        User = get_user_model()
        user_kwargs = {
            "email": "wbh_cliente@test.local",
            "password": "pass",
        }

        # Detectar si el modelo User requiere un campo 'role'
        try:
            from users.models import Role

            role = Role.objects.first() or Role.objects.create(name="cliente")
            user_kwargs["role"] = role
        except Exception:
            # Si no existe Role o no es requerido, continuar sin él
            pass

        # Crear usuario con kwargs compatibles
        try:
            self.cliente = User.objects.create_user(**user_kwargs)
        except TypeError:
            # Si create_user no acepta password en kwargs
            password = user_kwargs.pop("password", None)
            self.cliente = User.objects.create(**user_kwargs)
            if password:
                self.cliente.set_password(password)
                self.cliente.save()

        # Crear Order asociado al cliente
        self.order = Order.objects.create(id=str(uuid.uuid4()), cliente=self.cliente)

    def _post_payload(self, payload: dict, secret: str = "testsecret", headers=None):
        """Realiza la solicitud POST al endpoint del webhook con la firma correcta."""
        body = json.dumps(payload).encode("utf-8")
        sig = make_sig(secret, body)
        hdrs = {
            "HTTP_X_SIGNATURE": sig,
            "HTTP_X_PROVIDER": payload.get("provider", "mercadopago"),
        }
        if headers:
            hdrs.update(headers)
        return self.client.post(
            WEBHOOK_URL, data=body, content_type="application/json", **hdrs
        )

    def test_webhook_confirms_payment_and_order(self):
        provider_ref = "prov-123"
        payload = {
            "id": provider_ref,
            "external_reference": str(self.order.id),
            "status": "approved",
            "amount": "10.00",
        }
        resp = self._post_payload(payload)
        self.assertEqual(resp.status_code, 200)

        payment = Payment.objects.filter(provider_ref=provider_ref).first()
        self.assertIsNotNone(payment)
        self.assertEqual(str(payment.monto), "10.00")

        self.order.refresh_from_db()
        self.assertEqual(self.order.estado, ORDER_CONFIRMED)

        logs = PaymentLog.objects.filter(provider_ref=provider_ref)
        self.assertTrue(logs.exists())

    def test_webhook_idempotent_on_replay(self):
        provider_ref = "prov-999"
        payload = {
            "id": provider_ref,
            "external_reference": str(self.order.id),
            "status": "approved",
            "amount": "10.00",
        }

        # Primer envío
        resp1 = self._post_payload(payload)
        self.assertEqual(resp1.status_code, 200)

        # Segundo envío (replay)
        resp2 = self._post_payload(payload)
        self.assertEqual(resp2.status_code, 200)

        payments = Payment.objects.filter(provider_ref=provider_ref)
        self.assertEqual(
            payments.count(),
            1,
            "Debe haber solo un objeto Payment creado (idempotencia)",
        )

        logs = PaymentLog.objects.filter(provider_ref=provider_ref)
        self.assertEqual(logs.count(), 1)

    def test_webhook_signature_invalid(self):
        provider_ref = "prov-bad"
        payload = {
            "id": provider_ref,
            "external_reference": str(self.order.id),
            "status": "approved",
            "amount": "10.00",
        }
        body = json.dumps(payload).encode("utf-8")
        bad_sig = "bad-sign"

        # Envío con una firma incorrecta
        resp = self.client.post(
            WEBHOOK_URL,
            data=body,
            content_type="application/json",
            HTTP_X_SIGNATURE=bad_sig,
        )
        self.assertEqual(resp.status_code, 403)  # Se espera Forbidden

    def test_webhook_signature_valid(self):
        provider_ref = "prov-sig-valid"
        payload = {
            "id": provider_ref,
            "external_reference": str(self.order.id),
            "status": "approved",
            "amount": "10.00",
        }

        # Se usa _post_payload para generar la firma correcta
        resp = self._post_payload(payload)
        self.assertEqual(resp.status_code, 200)

        payment = Payment.objects.filter(provider_ref=provider_ref).first()
        self.assertIsNotNone(payment)
