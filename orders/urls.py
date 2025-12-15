from django.urls import include, path
from rest_framework import routers

# Solo importamos OrderViewSet (la vista maestra) y el webhook
from .views import OrderViewSet
from .views_webhooks import payment_webhook

router = routers.DefaultRouter()

# Registramos SOLO la vista maestra.
# Gracias a la refactorización, esta url maneja Clientes, Feriantes y Repartidores automáticamente.
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
    path("payments/webhook/", payment_webhook, name="payments-webhook"),
]
