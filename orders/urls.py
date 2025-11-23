# orders/urls.py
from django.urls import include, path
from rest_framework import routers

from .views import FerianteOrdersViewSet, OrderViewSet, RepartidorOrderViewSet
from .views_webhooks import payment_webhook

router = routers.DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"feriante/orders", FerianteOrdersViewSet, basename="feriante-orders")
router.register(
    r"repartidor/orders", RepartidorOrderViewSet, basename="repartidor-orders"
)

urlpatterns = [
    path("", include(router.urls)),
    path("payments/webhook/", payment_webhook, name="payments-webhook"),
]
