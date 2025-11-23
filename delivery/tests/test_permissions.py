# delivery/tests/test_permissions.py (CÓDIGO COMPLETO Y CORREGIDO)

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from delivery.models import DeliveryAssignment
# Helper de creación de orden (asumimos que está en delivery/tests/test_api.py)
from delivery.tests.test_api import create_sample_order
# Importamos Order y la constante de confirmación para el setup
from orders.models import ORDER_CONFIRMED, Order
# Importaciones de modelos
from users.models import Role

User = get_user_model()


class DeliveryPermissionTests(APITestCase):

    def setUp(self):
        # ----- Roles -----
        self.role_cliente, _ = Role.objects.get_or_create(name="cliente")
        self.role_repartidor, _ = Role.objects.get_or_create(name="repartidor")

        # ----- Usuarios -----
        self.cliente = User.objects.create(
            email="notr@test.local",
            full_name="Cliente Test",
            role=self.role_cliente,
            is_active=True,
        )
        self.cliente.set_password("pass123")
        self.cliente.save()
        self.repartidor = User.objects.create(
            email="rperm@test.local",
            full_name="Repartidor Test",
            role=self.role_repartidor,
            is_active=True,
        )
        self.repartidor.set_password("pass123")
        self.repartidor.save()

        # ----- Orden (Estado inicial: CONFIRMADO) -----
        self.order = create_sample_order(self.cliente, estado=ORDER_CONFIRMED)

        # La asignación se usa para referenciar el ID en los endpoints, aunque el ViewSet opera sobre Order
        self.assignment = DeliveryAssignment.objects.create(order=self.order)

    # ----------------------------
    #       URL helpers (usan el pk de la Order)
    # ----------------------------
    def _claim_url(self, pk):
        try:
            # Usar el basename 'repartidor-orders' del RepartidorOrderViewSet
            return reverse("repartidor-orders-claim", args=[str(pk)])
        except Exception:
            # Fallback URL (basado en el output de tu consola)
            return f"/api/v1/repartidor/orders/{pk}/claim/"

    def _mark_url(self, pk):
        try:
            # Usar el basename 'repartidor-orders' del RepartidorOrderViewSet
            return reverse("repartidor-orders-complete", args=[str(pk)])
        except Exception:
            # Fallback URL
            return f"/api/v1/repartidor/orders/{pk}/complete/"

    # ----------------------------
    #         TESTS
    # ----------------------------

    def test_cliente_no_puede_claim(self):
        """Un cliente NO puede reclamar una asignación (403)."""
        self.client.force_authenticate(user=self.cliente)
        # Se usa self.order.pk porque el RepartidorOrderViewSet opera sobre Order
        resp = self.client.post(self._claim_url(self.order.pk))

        self.assertEqual(
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            msg=f"Expected 403 for Cliente but got {resp.status_code}. Body: {getattr(resp, 'data', resp.content)}",
        )

    def test_repartidor_puede_claim_y_marcar_entregado(self):
        """Un repartidor puede reclamar y luego marcar como entregado (200/202)."""

        self.client.force_authenticate(user=self.repartidor)

        # ---------- CLAIM (Actualiza Order a EN_CAMINO) ----------
        claim_url = self._claim_url(self.order.pk)

        print(f"\n[DEBUG] Rol del repartidor: {self.repartidor.role.name.upper()}")
        print(f"[DEBUG] Estado inicial de la orden: {self.order.estado}")

        resp = self.client.post(claim_url)

        error_msg = (
            f"Claim expected 200/202 but got {resp.status_code}. "
            f"Error: {getattr(resp, 'data', resp.content)}"
        )
        self.assertIn(
            resp.status_code,
            (status.HTTP_200_OK, status.HTTP_202_ACCEPTED),
            msg=error_msg,
        )

        # 1. Verificar estado de la ORDEN después del CLAIM
        self.order.refresh_from_db()  # 🎯 Recarga la Order desde la DB
        self.assertEqual(self.order.repartidor_id, self.repartidor.id)

        self.assertIn(
            self.order.estado,
            # Se usa 'EN_CAMINO' porque es la cadena literal de tu ViewSet, e 'IN_ROUTE' como constante de DeliveryAssignment (opcional)
            ("EN_CAMINO", "IN_ROUTE"),
            msg=f"Order should be EN_CAMINO after claim, got: {self.order.estado}",
        )

        # ---------- MARK DELIVERED (Actualiza Order a ENTREGADO) ----------
        mark_url = self._mark_url(self.order.pk)

        resp2 = self.client.post(mark_url)

        error_msg2 = (
            f"Mark delivered expected 200/202 but got {resp2.status_code}. "
            f"Error: {getattr(resp2, 'data', resp2.content)}"
        )
        self.assertIn(
            resp2.status_code,
            (status.HTTP_200_OK, status.HTTP_202_ACCEPTED),
            msg=error_msg2,
        )

        # 2. Verificar estado final de la ORDEN
        self.order.refresh_from_db()

        expected_order_state = "ENTREGADO"  # Asumido de la lógica del ViewSet

        self.assertEqual(
            self.order.estado,
            expected_order_state,
            msg=f"Expected order state ENTREGADO, got: {self.order.estado}",
        )
