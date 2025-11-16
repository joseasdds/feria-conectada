# orders/tests/test_orders_api.py
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from market.models import Producto, Puesto, Feria
from users.models import Role
from orders.models import Order, Payment

User = get_user_model()

class OrderCreateTests(APITestCase):
    def setUp(self):
        Role.objects.get_or_create(name="CLIENTE")
        Role.objects.get_or_create(name="FERIANTE")
        self.cliente = User.objects.create_user(email="test_cliente@test.local", password="pw1234", full_name="Cliente Test", role=Role.objects.get(name="CLIENTE"))
        self.feriante = User.objects.create_user(email="test_feriante@test.local", password="pw1234", full_name="Feriante Test", role=Role.objects.get(name="FERIANTE"))
        self.feria = Feria.objects.create(nombre="Feria Test")
        self.puesto = Puesto.objects.create(feria=self.feria, feriante=self.feriante, nombre="Puesto Test")
        self.producto = Producto.objects.create(puesto=self.puesto, nombre="Prod", precio=Decimal("2.00"), stock=5)
        self.client.force_authenticate(self.cliente)

    def test_create_order_decrements_stock_and_creates_payment(self):
        url = reverse('orders-list')
        payload = {"notas": "test", "items": [{"producto": str(self.producto.id), "cantidad": 2}]}
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, 201, msg=f"Status code inesperado: {resp.status_code}, body: {getattr(resp, 'data', None)}")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)
        order = Order.objects.get(id=resp.data['id'])
        self.assertEqual(order.total, Decimal("4.00"))
        self.assertTrue(order.payments.exists())
        self.assertEqual(order.payments.first().monto, order.total)

class FerianteListTests(APITestCase):
    def setUp(self):
        Role.objects.get_or_create(name="CLIENTE")
        Role.objects.get_or_create(name="FERIANTE")
        self.cliente = User.objects.create_user(email="cliente2@test.local", password="pw", full_name="C", role=Role.objects.get(name="CLIENTE"))
        self.feriante = User.objects.create_user(email="feriante2@test.local", password="pw", full_name="F", role=Role.objects.get(name="FERIANTE"))
        feria = Feria.objects.create(nombre="F2")
        puesto = Puesto.objects.create(feria=feria, feriante=self.feriante, nombre="P2")
        prod = Producto.objects.create(puesto=puesto, nombre="P2Prod", precio=Decimal("1.00"), stock=10)
        self.client.force_authenticate(self.cliente)
        self.client.post(reverse('orders-list'), {"notas": "", "items": [{"producto": str(prod.id), "cantidad": 1}]}, format='json')

    def test_feriante_sees_order(self):
        self.client.force_authenticate(self.feriante)
        resp = self.client.get(reverse('feriante-orders-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.data) >= 1)

class RepartidorFlowTests(APITestCase):
    def setUp(self):
        Role.objects.get_or_create(name="CLIENTE")
        Role.objects.get_or_create(name="REPARTIDOR")
        self.cliente = User.objects.create_user(email="c3@test.local", password="pw", full_name="C3", role=Role.objects.get(name="CLIENTE"))
        self.repartidor = User.objects.create_user(email="r3@test.local", password="pw", full_name="R3", role=Role.objects.get(name="REPARTIDOR"))
        fer = Feria.objects.create(nombre="F3")
        puesto = Puesto.objects.create(feria=fer, feriante=self.repartidor, nombre="PuestoX")
        prod = Producto.objects.create(puesto=puesto, nombre="PX", precio=Decimal("1.00"), stock=10)
        self.client.force_authenticate(self.cliente)
        resp = self.client.post(reverse('orders-list'), {"notas":"", "items": [{"producto": str(prod.id), "cantidad": 1}]}, format='json')
        self.order_id = resp.data['id']
        order = Order.objects.get(id=self.order_id)
        order.estado = "LISTO"
        order.save()

    def test_claim_and_complete(self):
        self.client.force_authenticate(self.repartidor)
        claim = self.client.post(reverse('repartidor-orders-claim', args=[self.order_id]))
        self.assertEqual(claim.status_code, 200)
        order = Order.objects.get(id=self.order_id)
        self.assertEqual(order.estado, "EN_CAMINO")
        self.assertEqual(order.repartidor, self.repartidor)

        complete = self.client.post(reverse('repartidor-orders-complete', args=[self.order_id]))
        self.assertEqual(complete.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.estado, "ENTREGADO")
