# orders/urls.py
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, FerianteOrdersViewSet, RepartidorOrderViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'feriante/orders', FerianteOrdersViewSet, basename='feriante-orders')
router.register(r'repartidor/orders', RepartidorOrderViewSet, basename='repartidor-orders')

urlpatterns = router.urls